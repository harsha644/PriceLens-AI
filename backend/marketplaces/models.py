from django.db import models


class Marketplace(models.Model):
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)  # amazon_in, flipkart
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    # Timestamp of the last successful API connection for this marketplace
    last_successful = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class MarketplaceListing(models.Model):
    product = models.ForeignKey('catalog.Product', related_name='listings', on_delete=models.CASCADE)
    marketplace = models.ForeignKey(Marketplace, related_name='listings', on_delete=models.CASCADE)
    marketplace_product_id = models.CharField(max_length=100)  # ASIN or FSN
    title = models.CharField(max_length=300)
    product_url = models.URLField(max_length=500)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    seller_name = models.CharField(max_length=200, blank=True, default='')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    rating_count = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    shipping_info = models.CharField(max_length=200, blank=True, default='')
    last_checked = models.DateTimeField(auto_now=True)
    is_demo = models.BooleanField(default=False, db_index=True)



    def __str__(self):
        return f"{self.marketplace.name}: {self.title} (₹{self.current_price})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['marketplace', 'marketplace_product_id'],
                name='unique_marketplace_listing'
            )
        ]
        indexes = [
            models.Index(fields=['product', 'is_demo']),
            models.Index(fields=['marketplace', 'is_demo']),
        ]


class PriceHistory(models.Model):
    listing = models.ForeignKey(MarketplaceListing, related_name='price_history', on_delete=models.CASCADE)
    product = models.ForeignKey('catalog.Product', related_name='price_history', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_demo = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'timestamp']),
            models.Index(fields=['listing', 'timestamp']),
            models.Index(fields=['is_demo', 'timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product.name} @ ₹{self.price} on {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
