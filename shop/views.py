from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from shop.models import Product
from shop.services.queries import get_product_list, get_recent_products


def index(request: HttpRequest) -> HttpResponse:
    context = {"recent_products": get_recent_products()}
    return render(request, "index.html", context)


def detail_product(request: HttpRequest, slug: str) -> HttpResponse:
    product = get_object_or_404(Product, slug=slug)
    return render(request, "single-product.html", {"object": product})


def product_list(request: HttpRequest) -> HttpResponse:
    search = request.GET.get("search", "")
    products = get_product_list(search)
    page_number = request.GET.get("page", 1)
    paginator = Paginator(products, 9)
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "paginator": paginator,
    }
    return render(request, "list.html", context)


def page_not_found(request: HttpRequest, exception) -> HttpResponse:
    return render(request, "404.html")
