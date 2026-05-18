from django.db.models import QuerySet

from shop.models import Product


def get_recent_products(limit: int = 8) -> QuerySet[Product]:
    return Product.objects.filter(is_active=True).order_by("-created_at")[:limit]
