from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from catalog.models import Product
from marketplaces.models import Marketplace, MarketplaceListing, PriceHistory
from reviews.models import ProductReview

class Command(BaseCommand):
    help = "Seed clearly labelled demo products, listings, and price history (is_demo=True)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data (all flagged with is_demo=True)...")

        # 1. Marketplaces
        amazon, _ = Marketplace.objects.get_or_create(
            code='amazon_in',
            defaults={'name': 'Amazon India', 'base_url': 'https://www.amazon.in', 'is_active': True}
        )
        flipkart, _ = Marketplace.objects.get_or_create(
            code='flipkart',
            defaults={'name': 'Flipkart', 'base_url': 'https://www.flipkart.com', 'is_active': True}
        )

        # 2. Demo Products
        demo_products = [
            {
                'name': 'Samsung Galaxy S24 Ultra 5G',
                'brand': 'Samsung',
                'model': 'Galaxy S24 Ultra',
                'category': 'Smartphones',
                'model_number': 'SM-S928B',
                'variant': '12GB+256GB',
                'ram': '12GB',
                'storage': '256GB',
                'colour': 'Titanium Gray',
                'amazon_price': Decimal('129999.00'),
                'amazon_orig': Decimal('134999.00'),
                'flipkart_price': Decimal('126999.00'),
                'flipkart_orig': Decimal('134999.00'),
            },
            {
                'name': 'Apple iPhone 15 Pro',
                'brand': 'Apple',
                'model': 'iPhone 15 Pro',
                'category': 'Smartphones',
                'model_number': 'MTV03HN/A',
                'variant': '128GB',
                'ram': '8GB',
                'storage': '128GB',
                'colour': 'Natural Titanium',
                'amazon_price': Decimal('127990.00'),
                'amazon_orig': Decimal('134900.00'),
                'flipkart_price': Decimal('129900.00'),
                'flipkart_orig': Decimal('134900.00'),
            },
            {
                'name': 'Sony WH-1000XM5 Wireless Headphones',
                'brand': 'Sony',
                'model': 'WH-1000XM5',
                'category': 'Audio',
                'model_number': 'WH1000XM5/B',
                'variant': 'Standard',
                'ram': '',
                'storage': '',
                'colour': 'Black',
                'amazon_price': Decimal('28990.00'),
                'amazon_orig': Decimal('34990.00'),
                'flipkart_price': Decimal('29990.00'),
                'flipkart_orig': Decimal('34990.00'),
            },
            {
                'name': 'Apple MacBook Air M3',
                'brand': 'Apple',
                'model': 'MacBook Air 13-inch M3',
                'category': 'Laptops',
                'model_number': 'MRXN3HN/A',
                'variant': '8GB+256GB',
                'ram': '8GB',
                'storage': '256GB',
                'colour': 'Space Grey',
                'amazon_price': Decimal('104990.00'),
                'amazon_orig': Decimal('114900.00'),
                'flipkart_price': Decimal('102990.00'),
                'flipkart_orig': Decimal('114900.00'),
            }
        ]

        now = timezone.now()

        for item in demo_products:
            prod, created = Product.objects.get_or_create(
                brand=item['brand'],
                model_number=item['model_number'],
                variant=item['variant'],
                is_demo=True,
                defaults={
                    'name': item['name'],
                    'model': item['model'],
                    'category': item['category'],
                    'ram': item['ram'],
                    'storage': item['storage'],
                    'colour': item['colour'],
                }
            )

            # Amazon Listing
            amz_listing, _ = MarketplaceListing.objects.get_or_create(
                marketplace=amazon,
                marketplace_product_id=f"DEMO-AMZ-{prod.id}",
                defaults={
                    'product': prod,
                    'title': f"{prod.name} ({prod.colour}) - Demo Amazon Listing",
                    'product_url': f"https://www.amazon.in/dp/DEMO{prod.id}",
                    'current_price': item['amazon_price'],
                    'original_price': item['amazon_orig'],
                    'discount_percent': round(((item['amazon_orig'] - item['amazon_price']) / item['amazon_orig']) * 100, 2),
                    'seller_name': 'Appario Retail Pvt Ltd',
                    'rating': Decimal('4.6'),
                    'rating_count': 1420,
                    'is_available': True,
                    'shipping_info': 'FREE Prime Delivery within 24 hours',
                    'is_demo': True,
                }
            )

            # Flipkart Listing
            fk_listing, _ = MarketplaceListing.objects.get_or_create(
                marketplace=flipkart,
                marketplace_product_id=f"DEMO-FK-{prod.id}",
                defaults={
                    'product': prod,
                    'title': f"{prod.name} ({prod.colour}) - Demo Flipkart Listing",
                    'product_url': f"https://www.flipkart.com/demo-p-{prod.id}",
                    'current_price': item['flipkart_price'],
                    'original_price': item['flipkart_orig'],
                    'discount_percent': round(((item['flipkart_orig'] - item['flipkart_price']) / item['flipkart_orig']) * 100, 2),
                    'seller_name': 'OmniTechRetail',
                    'rating': Decimal('4.4'),
                    'rating_count': 980,
                    'is_available': True,
                    'shipping_info': 'FREE Delivery by Tomorrow',
                    'is_demo': True,
                }
            )

            # Price History for charts (last 30 days)
            for days_ago in range(30, 0, -5):
                hist_time = now - timedelta(days=days_ago)
                fluctuation = Decimal(str((days_ago % 3) * 500))
                PriceHistory.objects.get_or_create(
                    listing=amz_listing,
                    product=prod,
                    is_demo=True,
                    price=item['amazon_price'] + fluctuation,
                    timestamp=hist_time
                )
                PriceHistory.objects.get_or_create(
                    listing=fk_listing,
                    product=prod,
                    is_demo=True,
                    price=item['flipkart_price'] + (fluctuation * Decimal('1.2')),
                    timestamp=hist_time
                )

            # Demo Reviews for analysis testing
            sample_reviews = [
                ("Aman Sharma", 5.0, "Absolute beast of a phone!", "The battery life, display, and camera zoom are mind-blowing. Truly premium experience.", False),
                ("Priya Verma", 4.0, "Great performance, slightly bulky", "Runs every game smoothly. Camera is top notch. Slightly heavy in hand but worth the price.", False),
                ("Karthik R.", 5.0, "Best flagship device this year", "Switched from my old device and couldn't be happier. Screen brightness outdoors is unmatched.", False),
                ("Rohan Mehta", 1.0, "Poor delivery and heating issue", "Device gets warm while charging. Delivery box was damaged. Not satisfied with customer support.", False),
                ("Sneha Nair", 5.0, "Absolute beast of a phone!", "The battery life, display, and camera zoom are mind-blowing. Truly premium experience.", True), # duplicate
                ("Vikram Das", 2.0, "Expected better battery", "Battery drops quickly on 5G. Needs software optimization.", False),
                ("BotUser1", 5.0, "Good product", "Good good good good nice phone", False), # generic text
                ("BotUser2", 5.0, "Good product", "Good good good good nice phone", True), # duplicate generic
            ]

            for reviewer, rating, title, text, is_dup in sample_reviews:
                ProductReview.objects.get_or_create(
                    product=prod,
                    reviewer_name=reviewer,
                    review_title=title,
                    review_text=text,
                    rating=Decimal(str(rating)),
                    is_demo=True,
                    defaults={'is_verified_purchase': not is_dup}
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded demo data with is_demo=True."))
