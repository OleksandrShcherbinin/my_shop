import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
from pathlib import Path

from curl_cffi import requests
from curl_cffi.requests import exceptions as request_exceptions
from defusedxml import ElementTree as ET
from django.conf import settings
from django.utils.text import slugify
from selectolax.parser import HTMLParser

from shop.models import Brand, Category, Image, Product, Size

logger = logging.getLogger(__name__)

SITEMAP_URL = (
    "https://monkeeswilmington.com/sitemap_collections_1.xml?from=300820922483&to=317796417651"
)
BASE_URL = "https://monkeeswilmington.com"
MAX_WORKERS = 20
REQUEST_TIMEOUT = 30
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


class ProductCrawler:
    def __init__(self) -> None:
        # impersonate a real Chrome TLS/JA3 fingerprint — Shopify's WAF
        # rejects vanilla python-requests handshakes with 403.
        self.session = requests.Session(impersonate="chrome")
        self.media_root = Path(settings.MEDIA_ROOT)
        (self.media_root / "products").mkdir(parents=True, exist_ok=True)

    def execute(self) -> dict:
        print("COMMAND STARTED")
        collection_urls = self.fetch_collection_urls()
        print(f"Found {len(collection_urls)} collections")

        product_urls = self.fetch_product_urls(collection_urls)
        print(f"Found {len(product_urls)} unique product URLs")

        products_data = self.fetch_products(product_urls)
        print(f"Scraped {len(products_data)} product pages")

        saved = self.save_products(products_data)
        print(f"Saved/updated {saved} products")
        return {
            "collections": len(collection_urls),
            "product_urls": len(product_urls),
            "scraped": len(products_data),
            "saved": saved,
        }

    def fetch_collection_urls(self) -> list[str]:
        response = self.session.get(SITEMAP_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        return [
            loc.text.strip() for loc in root.findall(".//sm:url/sm:loc", SITEMAP_NS) if loc.text
        ]

    def fetch_product_urls(self, collection_urls: list[str]) -> list[str]:
        seen: set[str] = set()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(self._scrape_collection, url): url for url in collection_urls}
            for future in as_completed(futures):
                col_url = futures[future]
                try:
                    for product_url in future.result():
                        seen.add(product_url)
                except Exception as exc:
                    logger.warning("collection failed %s: %s", col_url, exc)
        return sorted(seen)

    def _scrape_collection(self, url: str) -> list[str]:
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        parser = HTMLParser(response.text)
        links = parser.css(".product-item__image-link")
        urls = []
        for link in links:
            href = link.attributes.get("href")
            if not href:
                continue
            urls.append(href if href.startswith("http") else BASE_URL + href)
        return urls

    def fetch_products(self, product_urls: list[str]) -> list[dict]:
        results: list[dict] = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(self._scrape_product, url): url for url in product_urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                except Exception as exc:
                    logger.warning("product failed %s: %s", url, exc)
        return results

    def _scrape_product(self, url: str) -> dict | None:
        response = self.session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        parser = HTMLParser(response.text)

        h1 = parser.css_first("h1")
        if h1 is None:
            return None
        name = h1.text(strip=True)

        parts = url.rstrip("/").split("/")
        category_slug = parts[-3] if len(parts) >= 3 else "uncategorized"

        brand_node = parser.css_first(".product__vendor a")
        brand_name = brand_node.text(strip=True) if brand_node else "Unknown"

        price = self._parse_price(parser)
        if price is None:
            return None

        size_nodes = parser.css(".product__color-chips button")
        sizes: list[str] = []
        for n in size_nodes:
            label = n.attributes.get("data-label")
            if label:
                sizes.append(label.strip())

        desc_node = parser.css_first(".product__description")
        description = desc_node.text(strip=True) if desc_node else ""

        image_path = self._download_first_image(parser, name)

        return {
            "name": name,
            "category_slug": category_slug,
            "brand_name": brand_name,
            "price": price,
            "sizes": sizes,
            "description": description,
            "image_path": image_path,
            "source_url": url,
        }

    @staticmethod
    def _parse_price(parser: HTMLParser) -> Decimal | None:
        spans = parser.css(".product__price span")
        if len(spans) < 2:
            return None
        raw = spans[1].text(strip=True)
        cleaned = re.sub(r"[^\d.]", "", raw)
        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None

    def _download_first_image(self, parser: HTMLParser, name: str) -> str | None:
        link = parser.css_first(".product__media-item a")
        if link is None:
            return None
        href = link.attributes.get("href")
        if not href:
            return None
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = BASE_URL + href
        try:
            resp = self.session.get(href, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except request_exceptions.RequestException as exc:
            logger.warning("image download failed %s: %s", href, exc)
            return None
        ext = Path(href.split("?")[0]).suffix or ".jpg"
        filename = f"{slugify(name)}{ext}"
        rel_path = f"products/{filename}"
        abs_path = self.media_root / rel_path
        abs_path.write_bytes(resp.content)
        return rel_path

    def save_products(self, products_data: list[dict]) -> int:
        category_cache: dict[str, Category] = {}
        brand_cache: dict[str, Brand] = {}
        size_cache: dict[str, Size] = {}
        saved = 0

        for data in products_data:
            category = category_cache.get(data["category_slug"])
            if category is None:
                category, _ = Category.objects.get_or_create(name=data["category_slug"])
                category_cache[data["category_slug"]] = category

            brand = brand_cache.get(data["brand_name"])
            if brand is None:
                brand, _ = Brand.objects.get_or_create(name=data["brand_name"])
                brand_cache[data["brand_name"]] = brand

            product, _ = Product.objects.get_or_create(
                slug=slugify(data["name"]),
                defaults={
                    "name": data["name"],
                    "description": data["description"],
                    "brand": brand,
                    "price": data["price"],
                },
            )
            product.categories.add(category)

            for size_name in data["sizes"]:
                size = size_cache.get(size_name)
                if size is None:
                    size, _ = Size.objects.get_or_create(name=size_name)
                    size_cache[size_name] = size
                product.sizes.add(size)

            if data["image_path"] and not product.images.exists():
                Image.objects.create(product=product, image=data["image_path"])

            saved += 1
        return saved
