from django.conf import settings
from decimal import Decimal
from typing import Dict, Any, List
from catalog.models import Product
from marketplaces.models import MarketplaceListing
from reviews.models import ReviewAnalysis
from .models import UserRecommendation

class RecommendationService:
    DEFAULT_WEIGHTS = {
        'price': 0.30,
        'discount': 0.15,
        'rating': 0.20,
        'sentiment': 0.20,
        'availability': 0.10,
        'seller': 0.05,
    }

    @classmethod
    def get_weights(cls) -> Dict[str, float]:
        configured = getattr(settings, 'RECOMMENDATION_WEIGHTS', cls.DEFAULT_WEIGHTS)
        # Normalize weights so sum equals 1.0
        total = sum(configured.values())
        if total > 0:
            return {k: v / total for k, v in configured.items()}
        return cls.DEFAULT_WEIGHTS

    @classmethod
    def generate_recommendation_for_product(cls, product: Product, user=None, include_demo: bool = True) -> Dict[str, Any]:
        weights = cls.get_weights()
        listings_qs = product.listings.all()
        if not include_demo:
            listings_qs = listings_qs.filter(is_demo=False)

        listings = list(listings_qs)
        if not listings:
            return {
                'product_id': product.id,
                'product_name': product.name,
                'score': 0.0,
                'best_listing': None,
                'factor_breakdown': {},
                'explanation': f"No marketplace listings currently available for {product.name}."
            }

        # Analysis data
        try:
            analysis = product.analysis
            sentiment_compound = float(analysis.sentiment_score) # -1.0 to 1.0
            pos_pct = float(analysis.sentiment_distribution.get('positive', 0))
        except Exception:
            sentiment_compound = 0.0
            pos_pct = 50.0

        sentiment_factor = max(0.0, min(1.0, (sentiment_compound + 1.0) / 2.0))

        # Price pool min / max
        prices = [float(l.current_price) for l in listings if l.current_price > 0]
        min_price = min(prices) if prices else 1.0
        max_price = max(prices) if prices else 1.0
        price_range = max(1.0, max_price - min_price)

        ranked_listings = []

        for l in listings:
            price = float(l.current_price)
            # Price score (cheaper gets higher score)
            if max_price == min_price:
                price_factor = 1.0
            else:
                price_factor = (max_price - price) / price_range

            discount_factor = min(1.0, float(l.discount_percent or 0) / 100.0)
            rating_factor = min(1.0, float(l.rating or 0) / 5.0)
            avail_factor = 1.0 if l.is_available else 0.0
            seller_factor = 1.0 if l.seller_name and 'retail' in l.seller_name.lower() or 'appario' in l.seller_name.lower() or l.rating_count > 500 else 0.7

            factors = {
                'price_factor': round(price_factor, 3),
                'discount_factor': round(discount_factor, 3),
                'rating_factor': round(rating_factor, 3),
                'sentiment_factor': round(sentiment_factor, 3),
                'availability_factor': round(avail_factor, 3),
                'seller_factor': round(seller_factor, 3),
            }

            total_score = (
                (price_factor * weights['price']) +
                (discount_factor * weights['discount']) +
                (rating_factor * weights['rating']) +
                (sentiment_factor * weights['sentiment']) +
                (avail_factor * weights['availability']) +
                (seller_factor * weights['seller'])
            ) * 100.0
            total_score = round(max(0.0, min(100.0, total_score)), 2)

            ranked_listings.append({
                'listing': l,
                'score': total_score,
                'factors': factors
            })

        ranked_listings.sort(key=lambda x: x['score'], reverse=True)
        best = ranked_listings[0]
        best_listing = best['listing']

        # Plain language explanation
        explanation_parts = [
            f"Top recommendation for {product.name} is on {best_listing.marketplace.name} (Score: {best['score']}/100)."
        ]
        if best_listing.current_price == Decimal(str(min_price)):
            explanation_parts.append(f"Offers the most competitive price at ₹{best_listing.current_price:,.2f}.")
        else:
            explanation_parts.append(f"Priced at ₹{best_listing.current_price:,.2f}.")

        if best_listing.discount_percent > 0:
            explanation_parts.append(f"Includes a {best_listing.discount_percent}% direct discount.")

        explanation_parts.append(f"Backed by a {best_listing.rating}★ rating ({best_listing.rating_count} reviews) and {pos_pct}% positive sentiment.")

        if best_listing.shipping_info:
            explanation_parts.append(f"Shipping: {best_listing.shipping_info}.")

        full_explanation = " ".join(explanation_parts)

        # Save to UserRecommendation
        user_recommendation, _ = UserRecommendation.objects.update_or_create(
            user=user if (user and user.is_authenticated) else None,
            product=product,
            defaults={
                'score': Decimal(str(best['score'])),
                'best_listing': best_listing,
                'factor_breakdown': best['factors'],
                'plain_language_explanation': full_explanation
            }
        )

        return {
            'product_id': product.id,
            'product_name': product.name,
            'score': best['score'],
            'best_listing_id': best_listing.id,
            'marketplace': best_listing.marketplace.name,
            'price': float(best_listing.current_price),
            'factor_breakdown': best['factors'],
            'explanation': full_explanation,
            'ranked_options': [
                {
                    'listing_id': item['listing'].id,
                    'marketplace': item['listing'].marketplace.name,
                    'price': float(item['listing'].current_price),
                    'rating': float(item['listing'].rating),
                    'score': item['score'],
                    'url': item['listing'].product_url,
                }
                for item in ranked_listings
            ]
        }
