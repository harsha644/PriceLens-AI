from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify

def validate_image_file(image):
    # Max size: 5MB
    filesize = image.size
    if filesize > 5 * 1024 * 1024:
        raise ValidationError("Maximum image file size is 5MB.")

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, blank=True, default='package')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    brand = models.CharField(max_length=100, db_index=True)
    model = models.CharField(max_length=150, blank=True, default='')
    category = models.CharField(max_length=100, db_index=True) # Text category for fast indexing
    category_rel = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    model_number = models.CharField(max_length=100, blank=True, default='', db_index=True)
    variant = models.CharField(max_length=100, blank=True, default='')
    ram = models.CharField(max_length=50, blank=True, default='')
    storage = models.CharField(max_length=50, blank=True, default='')
    colour = models.CharField(max_length=50, blank=True, default='')
    # Universal product fields for any category
    size = models.CharField(max_length=50, blank=True, default='')
    material = models.CharField(max_length=100, blank=True, default='')
    specifications = models.JSONField(default=dict, blank=True)
    is_demo = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['brand', 'category']),
            models.Index(fields=['brand', 'model_number']),
            models.Index(fields=['is_demo', 'name']),
            models.Index(fields=['category', 'is_demo']),
        ]

    def clean(self):
        super().clean()
        if self.model_number:
            qs = Product.objects.filter(
                brand__iexact=self.brand,
                model_number__iexact=self.model_number,
                variant__iexact=self.variant,
                ram__iexact=self.ram,
                storage__iexact=self.storage,
                colour__iexact=self.colour
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("A product with this brand, model number, and exact variant already exists.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        desc = f"{self.brand} {self.name}"
        extras = [x for x in [self.variant, self.ram, self.storage, self.colour, self.size] if x]
        if extras:
            desc += f" ({', '.join(extras)})"
        return desc

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/%Y/%m/', validators=[validate_image_file])
    is_primary = models.BooleanField(default=False)
    confirmed_by_user = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name} (Primary: {self.is_primary})"
