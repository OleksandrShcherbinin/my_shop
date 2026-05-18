from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from shop.models import Brand, Category, Image, Product, Size


def image_tag(image_field: str, height: int = 50) -> str:
    if not image_field:
        return format_html('<span style="color: #aaaaaa">-</span>')
    return format_html(
        '<img src="{}" height="{}" style="border-radius: 5px;"/>',
        image_field,
        height,
    )


def admin_link(obj) -> str:
    if obj is None:
        return format_html('<span style="color: #aaaaaa">-</span>')
    url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=(obj.pk,))
    return format_html('<a href="{}">{}</a>', url, obj.name)


class ProductImageInline(admin.TabularInline):
    model = Image
    fields = ("image_preview",)
    readonly_fields = ("image_preview",)
    extra = 0

    def image_preview(self, obj: Image) -> str:
        return image_tag(obj.image.url, 300)  # ty: ignore[unresolved-attribute]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand_link", "stock", "price", "old_price")
    inlines = [
        ProductImageInline,
    ]

    @admin.display()
    def brand_link(self, obj: Product) -> str:
        return admin_link(obj.brand)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("image", "image_preview")

    @admin.display()
    def image_preview(self, obj: Image) -> str:
        return image_tag(obj.image.url)  # ty: ignore[unresolved-attribute]
