from rest_framework import serializers
from .models import SearchHistory, UserRecommendation

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ['id', 'query', 'category', 'filters', 'created_at']
        read_only_fields = ['id', 'created_at']

class UserRecommendationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    marketplace_name = serializers.CharField(source='best_listing.marketplace.name', read_only=True)
    price = serializers.DecimalField(source='best_listing.current_price', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = UserRecommendation
        fields = [
            'id', 'product', 'product_name', 'score', 'best_listing',
            'marketplace_name', 'price', 'factor_breakdown',
            'plain_language_explanation', 'created_at'
        ]
