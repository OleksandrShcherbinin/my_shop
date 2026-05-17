from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Brand(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, default="")
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Size(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=280, unique=True)
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    old_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Original price before discount(optional)",
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    categories = models.ManyToManyField(Category, related_name="products", blank=True)
    sizes = models.ManyToManyField(Size, related_name="products", blank=True)
    brand = models.ForeignKey(
        Brand,
        related_name="products",
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = (
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def has_discount(self) -> bool:
        return self.old_price is not None and self.old_price > self.price

    @property
    def discount_percent(self) -> int:
        if self.old_price is None or self.old_price <= self.price:
            return 0
        price = Decimal(str(self.price))
        old_price = Decimal(str(self.old_price))
        return int(round((Decimal(1) - price / old_price) * 100))


class Image(models.Model):
    objects = models.Manager()

    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.pk}"
