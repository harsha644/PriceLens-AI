from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Product
from .matching import ProductMatchingService
from recommendations.models import SearchHistory

class CatalogAndMatchingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', password='Password123!')
        self.client.force_authenticate(user=self.user)

        self.p1 = Product.objects.create(
            name='Samsung Galaxy S24 Ultra',
            brand='Samsung',
            model='Galaxy S24 Ultra',
            category='Smartphones',
            model_number='SM-S928B',
            variant='12GB+256GB',
            ram='12GB',
            storage='256GB',
            colour='Titanium Gray',
            is_demo=False
        )

        self.p1_demo = Product.objects.create(
            name='Samsung Galaxy S24 Ultra Demo',
            brand='Samsung',
            model='Galaxy S24 Ultra',
            category='Smartphones',
            model_number='SM-S928B',
            variant='12GB+512GB',
            ram='12GB',
            storage='512GB',
            colour='Titanium Gray',
            is_demo=True
        )

    def test_search_and_demo_isolation(self):
        # Default search excludes demo items
        res = self.client.get('/api/catalog/?q=Samsung')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in res.data]
        self.assertIn(self.p1.id, ids)
        self.assertNotIn(self.p1_demo.id, ids)

        # Explicitly asking for demo
        demo_res = self.client.get('/api/catalog/?q=Samsung&include_demo=true')
        self.assertEqual(demo_res.status_code, status.HTTP_200_OK)
        demo_ids = [p['id'] for p in demo_res.data]
        self.assertIn(self.p1.id, demo_ids)
        self.assertIn(self.p1_demo.id, demo_ids)

        # Verifies SearchHistory saved
        self.assertTrue(SearchHistory.objects.filter(user=self.user, query='Samsung').exists())

    def test_matching_exact_variant_compatibility(self):
        target = {
            'name': 'Samsung Galaxy S24 Ultra',
            'brand': 'Samsung',
            'model_number': 'SM-S928B',
            'ram': '12GB',
            'storage': '256GB',
            'colour': 'Titanium Gray',
            'variant': '12GB+256GB'
        }
        candidate_same = {
            'name': 'Samsung Galaxy S24 Ultra 5G (Titanium Gray, 256 GB)',
            'brand': 'Samsung',
            'model_number': 'SM-S928B',
            'ram': '12GB',
            'storage': '256GB',
            'colour': 'Titanium Gray',
            'variant': '12GB+256GB'
        }
        score, reasons, compatible = ProductMatchingService.match_products(target, candidate_same)
        self.assertTrue(compatible)
        self.assertGreater(score, 60.0)
        self.assertTrue(any('Exact match on model number' in r for r in reasons))

    def test_matching_variant_edge_cases_rejects_different_variants(self):
        target = {
            'name': 'Samsung Galaxy S24 Ultra',
            'brand': 'Samsung',
            'model_number': 'SM-S928B',
            'ram': '12GB',
            'storage': '256GB',
            'colour': 'Titanium Gray',
            'variant': '12GB+256GB'
        }
        # Candidate with different storage: 512GB vs 256GB
        candidate_diff_storage = {
            'name': 'Samsung Galaxy S24 Ultra 5G 512GB',
            'brand': 'Samsung',
            'model_number': 'SM-S928B',
            'ram': '12GB',
            'storage': '512GB',
            'colour': 'Titanium Gray',
            'variant': '12GB+512GB'
        }
        score, reasons, compatible = ProductMatchingService.match_products(target, candidate_diff_storage)
        self.assertFalse(compatible)
        self.assertLessEqual(score, 25.0)
        self.assertTrue(any('Storage mismatch' in r for r in reasons))

        # Candidate with different model number
        candidate_diff_model = {
            'name': 'Samsung Galaxy S24 Plus',
            'brand': 'Samsung',
            'model_number': 'SM-S926B',
            'ram': '12GB',
            'storage': '256GB',
            'colour': 'Titanium Gray',
            'variant': '12GB+256GB'
        }
        score2, reasons2, compatible2 = ProductMatchingService.match_products(target, candidate_diff_model)
        self.assertFalse(compatible2)
        self.assertTrue(any('Model number mismatch' in r for r in reasons2))
