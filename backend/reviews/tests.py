from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from catalog.models import Product
from .models import ProductReview, ReviewAnalysis
from .services import ReviewAnalysisService

class ReviewAnalysisServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='revtester', password='Password123!')
        self.client.force_authenticate(user=self.user)

        self.product = Product.objects.create(
            name='Test Smartphone',
            brand='TechBrand',
            category='Smartphones',
            is_demo=False
        )

    def test_review_analysis_known_sentiment_and_words(self):
        ProductReview.objects.create(
            product=self.product,
            reviewer_name='Reviewer 1',
            review_title='Incredible experience',
            review_text='This is absolutely wonderful and excellent! Superb performance and great battery life.',
            rating=Decimal('5.0'),
            is_demo=False
        )
        ProductReview.objects.create(
            product=self.product,
            reviewer_name='Reviewer 2',
            review_title='Horrible product',
            review_text='Worst quality ever. Terrible customer service and defective charging port.',
            rating=Decimal('1.0'),
            is_demo=False
        )

        analysis = ReviewAnalysisService.analyze_product_reviews(self.product, include_demo=False)
        self.assertEqual(analysis.total_reviews, 2)
        self.assertEqual(float(analysis.average_rating), 3.0)
        self.assertGreater(analysis.sentiment_distribution['positive'], 0)
        self.assertGreater(analysis.sentiment_distribution['negative'], 0)
        pos_words = [w['word'] for w in analysis.top_positive_words]
        self.assertTrue(any(x in pos_words for x in ['excellent', 'superb', 'wonderful', 'battery']))

    def test_duplicate_and_similar_detection(self):
        # 1. Exact duplicate reviews
        dup_text = "Good battery life and nice screen display"
        ProductReview.objects.create(product=self.product, review_text=dup_text, rating=Decimal('4.0'), is_demo=False)
        ProductReview.objects.create(product=self.product, review_text=dup_text, rating=Decimal('4.0'), is_demo=False)
        ProductReview.objects.create(product=self.product, review_text=dup_text, rating=Decimal('4.0'), is_demo=False)

        # 2. Near-duplicate similar review
        similar_text = "Good battery life and very nice screen display"
        ProductReview.objects.create(product=self.product, review_text=similar_text, rating=Decimal('4.0'), is_demo=False)

        analysis = ReviewAnalysisService.analyze_product_reviews(self.product, include_demo=False)
        # There are 3 identical copies -> duplicate_count = 2
        self.assertEqual(analysis.duplicate_count, 2)
        # Check suspicious indicator wording (strictly potential indicators)
        indicator_types = [ind['type'] for ind in analysis.suspicious_indicators]
        self.assertIn('repeated_text', indicator_types)
        for ind in analysis.suspicious_indicators:
            self.assertNotIn('fake review', ind['detail'].lower())

    def test_rating_sentiment_mismatch(self):
        # 5 star rating with strongly negative text
        ProductReview.objects.create(
            product=self.product,
            review_text="Completely broken, awful experience, worst quality.",
            rating=Decimal('5.0'),
            is_demo=False
        )
        analysis = ReviewAnalysisService.analyze_product_reviews(self.product, include_demo=False)
        self.assertGreaterEqual(analysis.rating_sentiment_mismatches, 1)

    def test_manual_review_post_api(self):
        data = {
            'reviewer_name': 'Tester Ravi',
            'review_title': 'Decent buy',
            'review_text': 'Value for money product with fast delivery.',
            'rating': '4.0'
        }
        res = self.client.post(f'/api/reviews/{self.product.id}/', data=data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ProductReview.objects.filter(product=self.product).count(), 1)
