from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from shop.models import Product
from shop.services.queries import get_recent_products


def index(request: HttpRequest) -> HttpResponse:
    context = {"recent_products": get_recent_products()}
    return render(request, "index.html", context)


def detail_product(request: HttpRequest, slug: str) -> HttpResponse:
    context = {"object": Product.objects.get(slug=slug)}
    return render(request, "single-product.html", context)
