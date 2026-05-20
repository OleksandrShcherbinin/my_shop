from django.db.models import Count, QuerySet

from shop.models import Category, Product


def get_recent_products(limit: int = 8) -> QuerySet[Product]:
    return Product.objects.filter(is_active=True).order_by("-created_at")[:limit]


def get_product_list(search: str) -> QuerySet[Product]:
    if len(search) > 2:
        return Product.objects.filter(name__icontains=search)
    return Product.objects.all()


def get_biggest_categories(limit: int = 8) -> QuerySet[Category]:
    return Category.objects.annotate(products_count=Count("products", distinct=True)).order_by(
        "-products_count"
    )[:limit]
