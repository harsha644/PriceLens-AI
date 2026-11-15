from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from catalog.models import Product
from marketplaces.models import Marketplace, MarketplaceListing
from .models import SearchHistory, UserRecommendation
from .services import RecommendationService

class RecommendationAndHistoryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', password='Password123!')
        self.client.force_authenticate(user=self.user1)

        self.amz = Marketplace.objects.create(name='Amazon India', code='amazon_in', base_url='https://www.amazon.in')
        self.product = Product.objects.create(name='Laptop Pro', brand='BrandX', category='Laptops', is_demo=False)

        self.listing = MarketplaceListing.objects.create(
            product=self.product,
            marketplace=self.amz,
            marketplace_product_id='AMZ-LAP-1',
            title='Laptop Pro 16GB',
            product_url='https://www.amazon.in/dp/LAP1',
            current_price=Decimal('79990.00'),
            original_price=Decimal('89990.00'),
            discount_percent=Decimal('11.11'),
            seller_name='Authorized Retailer',
            rating=Decimal('4.7'),
            rating_count=350,
            is_available=True,
            is_demo=False
        )

    def test_recommendation_scoring_and_explanation(self):
        rec = RecommendationService.generate_recommendation_for_product(
            product=self.product,
            user=self.user1,
            include_demo=False
        )
        self.assertGreater(rec['score'], 50.0)
        self.assertIn('Laptop Pro', rec['explanation'])
        self.assertIn('Amazon India', rec['explanation'])
        self.assertIn('79,990', rec['explanation'])
        self.assertTrue(UserRecommendation.objects.filter(product=self.product).exists())

    def test_search_history_object_level_permissions(self):
        # User 1 history
        h1 = SearchHistory.objects.create(user=self.user1, query='Macbook M3', category='Laptops')
        # User 2 history
        h2 = SearchHistory.objects.create(user=self.user2, query='iPhone 15', category='Smartphones')

        # User 1 lists history: only sees own entries
        res = self.client.get('/api/recommendations/history/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        queries = [item['query'] for item in res.data]
        self.assertIn('Macbook M3', queries)
        self.assertNotIn('iPhone 15', queries)

        # User 1 attempts to delete User 2's history: should return 404 or 403
        del_res = self.client.delete(f'/api/recommendations/history/{h2.id}/')
        self.assertIn(del_res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(SearchHistory.objects.filter(id=h2.id).exists())

        # User 1 deletes their own history
        own_del_res = self.client.delete(f'/api/recommendations/history/{h1.id}/')
        self.assertEqual(own_del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SearchHistory.objects.filter(id=h1.id).exists())
