from django.contrib import admin

from shop.models import Brand, Category, Product, Size

# Register your models here.


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "stock", "price", "old_price")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name",)
