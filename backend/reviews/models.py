from django.db import models
from django.contrib.auth.models import User

class ProductReview(models.Model):
    product = models.ForeignKey('catalog.Product', related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='submitted_reviews')
    source = models.CharField(max_length=50, default='manual') # csv, manual
    reviewer_name = models.CharField(max_length=150, blank=True, default='Anonymous')
    review_title = models.CharField(max_length=255, blank=True, default='')
    review_text = models.TextField()
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    review_date = models.DateTimeField(null=True, blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'is_demo']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Review for {self.product.name} ({self.rating}★ by {self.reviewer_name})"

class ReviewAnalysis(models.Model):
    product = models.OneToOneField('catalog.Product', related_name='analysis', on_delete=models.CASCADE)
    total_reviews = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    rating_distribution = models.JSONField(default=dict)
    sentiment_distribution = models.JSONField(default=dict) # {positive: %, neutral: %, negative: %}
    sentiment_score = models.DecimalField(max_digits=4, decimal_places=3, default=0.0)
    top_positive_words = models.JSONField(default=list)
    top_negative_words = models.JSONField(default=list)
    duplicate_count = models.IntegerField(default=0)
    similar_count = models.IntegerField(default=0)
    rating_sentiment_mismatches = models.IntegerField(default=0)
    suspicious_indicators = models.JSONField(default=list) # potential indicators
    analyzed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.product.name} ({self.total_reviews} reviews)"
