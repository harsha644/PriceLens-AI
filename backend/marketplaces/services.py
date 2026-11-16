import logging
from typing import Dict, Any, List
from django.conf import settings
from .models import Marketplace, MarketplaceListing, PriceHistory
from catalog.models import Product

logger = logging.getLogger(__name__)

def get_or_create_marketplace(code: str, name: str, base_url: str) -> Marketplace:
    """Ensure a Marketplace DB entry exists for the given adapter.
    This is idempotent and safe to call on each request.
    """
    marketplace, _ = Marketplace.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'base_url': base_url,
            'is_active': True,
        },
    )
    return marketplace

def upsert_listing(product: Product, item: Dict[str, Any]) -> MarketplaceListing:
    """Create or update a MarketplaceListing for a product based on a feed item.
    The feed item dict follows the structure returned by adapters.
    """
    code = item.get('code')
    marketplace = get_or_create_marketplace(
        code=code,
        name=item.get('marketplace', code),
        base_url=item.get('url', '')
    )
    listing, created = MarketplaceListing.objects.update_or_create(
        product=product,
        marketplace=marketplace,
        marketplace_product_id=item.get('id'),
        defaults={
            'title': item.get('title', ''),
            'product_url': item.get('url', ''),
            'current_price': item.get('price') or 0,
            'original_price': item.get('original_price') or 0,
            'discount_percent': item.get('discount_percent') or 0,
            'seller_name': item.get('seller', ''),
            'rating': item.get('rating') or 0,
            'rating_count': item.get('rating_count') or 0,
            'is_available': item.get('availability', True),
            'shipping_info': item.get('shipping', ''),
            'is_demo': item.get('is_demo', False),
        }
    )
    # Record price history regardless of creation state
    PriceHistory.objects.create(
        listing=listing,
        product=product,
        price=listing.current_price,
        is_demo=listing.is_demo,
    )
    return listing

def process_marketplace_feeds(product: Product, feeds: Dict[str, Any]) -> List[MarketplaceListing]:
    """Iterate over the concurrent marketplace feed results and persist listings.
    Returns a list of created/updated MarketplaceListing objects.
    """
    saved_listings = []
    for code, feed in feeds.items():
        if feed.get('status') != 'success':
            logger.warning(f"Marketplace {code} returned non‑success status: {feed.get('reason')}")
            continue
        for item in feed.get('items', []):
            try:
                listing = upsert_listing(product, item)
                saved_listings.append(listing)
            except Exception as e:
                logger.error(f"Failed to upsert listing for product {product.id} from {code}: {e}")
    return saved_listings
