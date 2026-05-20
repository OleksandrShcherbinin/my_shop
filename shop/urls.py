from django.urls import path

from shop import views

app_name = "shop"

urlpatterns = [
    path("", views.index, name="index"),
    path("products/", views.product_list, name="product_list"),
    path("products/<slug:slug>/", views.detail_product, name="detail_product"),
]
