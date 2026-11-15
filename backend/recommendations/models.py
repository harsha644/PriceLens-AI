from django.db import models
from django.contrib.auth.models import User

class SearchHistory(models.Model):
    user = models.ForeignKey(User, related_name='search_history', on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, default='')
    filters = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.query} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class UserRecommendation(models.Model):
    user = models.ForeignKey(User, related_name='recommendations', on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey('catalog.Product', related_name='recommendations', on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2) # 0 to 100
    best_listing = models.ForeignKey('marketplaces.MarketplaceListing', on_delete=models.SET_NULL, null=True, blank=True)
    factor_breakdown = models.JSONField(default=dict)
    plain_language_explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['user', '-score']),
            models.Index(fields=['product', '-score']),
        ]

    def __str__(self):
        return f"Recommendation: {self.product.name} (Score: {self.score})"
