from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from decimal import Decimal
from catalog.models import Product
from .models import Marketplace, MarketplaceListing, PriceHistory
from .adapters import AmazonIndiaAdapter, FlipkartAdapter

class MarketplaceAndComparisonTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='mpuser', password='Password123!')
        self.client.force_authenticate(user=self.user)

        self.amazon = Marketplace.objects.create(name='Amazon India', code='amazon_in', base_url='https://www.amazon.in')
        self.flipkart = Marketplace.objects.create(name='Flipkart', code='flipkart', base_url='https://www.flipkart.com')

        self.product = Product.objects.create(
            name='Test Headphone',
            brand='TestBrand',
            category='Audio',
            is_demo=False
        )

        self.listing_amz = MarketplaceListing.objects.create(
            product=self.product,
            marketplace=self.amazon,
            marketplace_product_id='TEST_AMZ_1',
            title='Test Headphone on Amazon',
            product_url='https://www.amazon.in/dp/TEST_AMZ_1',
            current_price=Decimal('4999.00'),
            original_price=Decimal('5999.00'),
            discount_percent=Decimal('16.67'),
            seller_name='Amazon Seller',
            rating=Decimal('4.5'),
            rating_count=200,
            is_available=True,
            is_demo=False
        )

        self.listing_fk = MarketplaceListing.objects.create(
            product=self.product,
            marketplace=self.flipkart,
            marketplace_product_id='TEST_FK_1',
            title='Test Headphone on Flipkart',
            product_url='https://www.flipkart.com/p/TEST_FK_1',
            current_price=Decimal('4799.00'),
            original_price=Decimal('5999.00'),
            discount_percent=Decimal('20.00'),
            seller_name='Flipkart Seller',
            rating=Decimal('4.3'),
            rating_count=150,
            is_available=True,
            is_demo=False
        )

    def test_adapter_unconfigured_status(self):
        adapter = AmazonIndiaAdapter()
        # With blank credentials
        with patch.object(adapter, 'access_key', ''), patch.object(adapter, 'secret_key', ''):
            configured, reason = adapter.is_configured()
            self.assertFalse(configured)
            self.assertIn("missing", reason.lower())
            search_res = adapter.search('test')
            self.assertEqual(search_res['status'], 'unavailable')
            self.assertIn("missing", search_res['reason'].lower())

    @patch('marketplaces.adapters.requests.post')
    def test_amazon_adapter_mock_http(self, mock_post):
        adapter = AmazonIndiaAdapter()
        adapter.access_key = 'FAKE_KEY'
        adapter.secret_key = 'FAKE_SECRET'
        adapter.associate_tag = 'FAKE_TAG'

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'SearchResult': {
                'Items': [{
                    'ASIN': 'B0XYZ123',
                    'DetailPageURL': 'https://www.amazon.in/dp/B0XYZ123',
                    'ItemInfo': {'Title': {'DisplayValue': 'Real Mock Product'}},
                    'Offers': {'Listings': [{'Price': {'Amount': 4999.0}}]}
                }]
            }
        }
        mock_post.return_value = mock_resp

        result = adapter.search('Real Mock Product')
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['id'], 'B0XYZ123')

    def test_marketplace_status_endpoint(self):
        res = self.client.get('/api/marketplaces/status/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('amazon_in', res.data)
        self.assertIn('flipkart', res.data)
        self.assertIn('status', res.data['amazon_in'])

    def test_comparison_endpoint(self):
        res = self.client.get(f'/api/marketplaces/compare/{self.product.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['listings']), 2)
        self.assertEqual(float(res.data['summary']['lowest_price']), 4799.00)
        self.assertEqual(float(res.data['summary']['highest_price']), 4999.00)
        self.assertEqual(float(res.data['summary']['max_savings']), 200.00)
        self.assertIn('connector_status', res.data)
