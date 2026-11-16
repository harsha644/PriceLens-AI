from django.test import TestCase
from .models import Product
from marketplaces.services import process_marketplace_feeds
from marketplaces.models import Marketplace, MarketplaceListing, PriceHistory

class MarketplaceIntegrationTest(TestCase):
    def setUp(self):
        # Simple product for linking listings
        self.product = Product.objects.create(
            name='Test Product',
            brand='TestBrand',
            category='General merchandise',
            is_demo=False,
        )
        # Dummy feed data mimicking successful adapter responses
        self.dummy_feeds = {
            'amazon_in': {
                'status': 'success',
                'marketplace': 'Amazon India',
                'code': 'amazon_in',
                'items': [
                    {
                        'id': 'AMZ123',
                        'marketplace': 'Amazon India',
                        'code': 'amazon_in',
                        'title': 'Test Product on Amazon',
                        'url': 'https://www.amazon.in/dp/AMZ123',
                        'price': 123.45,
                        'original_price': 150.00,
                        'discount_percent': 18.0,
                        'seller': 'AmazonSeller',
                        'rating': 4.5,
                        'rating_count': 10,
                        'availability': True,
                        'shipping': 'Free Shipping',
                        'is_demo': False,
                    }
                ]
            },
            'flipkart': {
                'status': 'success',
                'marketplace': 'Flipkart',
                'code': 'flipkart',
                'items': [
                    {
                        'id': 'FK123',
                        'marketplace': 'Flipkart',
                        'code': 'flipkart',
                        'title': 'Test Product on Flipkart',
                        'url': 'https://www.flipkart.com/p/FK123',
                        'price': 124.00,
                        'original_price': 155.00,
                        'discount_percent': 20.0,
                        'seller': 'FlipkartSeller',
                        'rating': 4.3,
                        'rating_count': 8,
                        'availability': True,
                        'shipping': 'Free',
                        'is_demo': False,
                    }
                ]
            }
        }

    def test_process_marketplace_feeds_creates_listings_and_history(self):
        saved = process_marketplace_feeds(self.product, self.dummy_feeds)
        # Expect two listings (one per marketplace)
        self.assertEqual(len(saved), 2)
        self.assertTrue(Marketplace.objects.filter(code='amazon_in').exists())
        self.assertTrue(Marketplace.objects.filter(code='flipkart').exists())
        self.assertEqual(MarketplaceListing.objects.filter(product=self.product).count(), 2)
        # Each listing should have an associated price history entry
        self.assertEqual(PriceHistory.objects.filter(product=self.product).count(), 2)
        # Verify fields of one listing for sanity
        amazon_listing = MarketplaceListing.objects.get(marketplace__code='amazon_in')
        self.assertEqual(amazon_listing.marketplace_product_id, 'AMZ123')
        self.assertEqual(float(amazon_listing.current_price), 123.45)
