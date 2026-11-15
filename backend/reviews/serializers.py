from decimal import Decimal
from rest_framework import serializers
from .models import ProductReview, ReviewAnalysis

class ProductReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'reviewer_name', 'review_title', 'review_text',
            'rating', 'review_date', 'is_verified_purchase', 'is_demo', 'source', 'created_at'
        ]
        read_only_fields = ['created_at']

class ManualReviewCreateSerializer(serializers.Serializer):
    reviewer_name = serializers.CharField(required=False, default='Anonymous', allow_blank=True)
    review_title = serializers.CharField(required=False, default='', allow_blank=True)
    review_text = serializers.CharField(required=True)
    rating = serializers.DecimalField(max_digits=2, decimal_places=1, required=True, min_value=Decimal('1.0'), max_value=Decimal('5.0'))
    is_verified_purchase = serializers.BooleanField(required=False, default=False)

class ReviewAnalysisSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = ReviewAnalysis
        fields = [
            'id', 'product', 'product_name', 'total_reviews', 'average_rating',
            'rating_distribution', 'sentiment_distribution', 'sentiment_score',
            'top_positive_words', 'top_negative_words', 'duplicate_count',
            'similar_count', 'rating_sentiment_mismatches', 'suspicious_indicators',
            'analyzed_at'
        ]
