from django.db.models import QuerySet
from django.http import HttpRequest

from shop.models import Category
from shop.services.queries import get_biggest_categories


def header_categories(request: HttpRequest) -> dict[str, QuerySet[Category]]:
    return {"categories": get_biggest_categories()}
