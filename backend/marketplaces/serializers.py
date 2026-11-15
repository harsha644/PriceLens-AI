from rest_framework import serializers
from .models import Marketplace, MarketplaceListing, PriceHistory

class MarketplaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marketplace
        fields = ['id', 'name', 'code', 'base_url', 'is_active']

class MarketplaceListingSerializer(serializers.ModelSerializer):
    marketplace_name = serializers.CharField(source='marketplace.name', read_only=True)
    marketplace_code = serializers.CharField(source='marketplace.code', read_only=True)

    class Meta:
        model = MarketplaceListing
        fields = [
            'id', 'product', 'marketplace', 'marketplace_name', 'marketplace_code',
            'marketplace_product_id', 'title', 'product_url',
            'current_price', 'original_price', 'discount_percent',
            'seller_name', 'rating', 'rating_count', 'is_available',
            'shipping_info', 'last_checked', 'is_demo'
        ]

class PriceHistorySerializer(serializers.ModelSerializer):
    marketplace_name = serializers.CharField(source='listing.marketplace.name', read_only=True)
    marketplace_code = serializers.CharField(source='listing.marketplace.code', read_only=True)

    class Meta:
        model = PriceHistory
        fields = ['id', 'product', 'listing', 'marketplace_name', 'marketplace_code', 'price', 'timestamp', 'is_demo']
