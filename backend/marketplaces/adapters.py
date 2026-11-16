
from .services import get_or_create_marketplace

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from typing import Dict, Any, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseMarketplaceAdapter:
    code: str = ""
    name: str = ""
    base_url: str = ""

    def is_configured(self) -> Tuple[bool, str]:
        raise NotImplementedError

    def search(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_listing(self, listing_id: str) -> Dict[str, Any]:
        raise NotImplementedError

class AmazonIndiaAdapter(BaseMarketplaceAdapter):
    code = "amazon_in"
    name = "Amazon India"
    base_url = "https://www.amazon.in"

    def __init__(self):
        self.access_key = getattr(settings, 'AMAZON_ACCESS_KEY', '').strip()
        self.secret_key = getattr(settings, 'AMAZON_SECRET_KEY', '').strip()
        self.associate_tag = getattr(settings, 'AMAZON_ASSOCIATE_TAG', '').strip()
        self.country = getattr(settings, 'AMAZON_COUNTRY', 'IN').strip()

    def is_configured(self) -> Tuple[bool, str]:
        missing = []
        if not self.access_key:
            missing.append("AMAZON_ACCESS_KEY")
        if not self.secret_key:
            missing.append("AMAZON_SECRET_KEY")
        if not self.associate_tag:
            missing.append("AMAZON_ASSOCIATE_TAG")

        if missing:
            return False, f"Amazon India PA-API credentials missing: {', '.join(missing)}"
        return True, "Configured"

    def search(self, query: str) -> Dict[str, Any]:
        configured, reason = self.is_configured()
        if not configured:
            return {
                'status': 'unavailable',
                'marketplace': self.name,
                'code': self.code,
                'reason': reason,
                'items': []
            }

        try:
            endpoint = "webservices.amazon.in"
            headers = {
                'Content-Type': 'application/json; charset=utf-8',
                'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems',
            }
            payload = {
                'Keywords': query,
                'SearchIndex': 'All',
                'ItemCount': 5,
                'PartnerTag': self.associate_tag,
                'PartnerType': 'Associates',
                'Marketplace': 'www.amazon.in',
            }
            resp = requests.post(f"https://{endpoint}/paapi5/searchitems", json=payload, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for it in data.get('SearchResult', {}).get('Items', []):
                    offers = it.get('Offers', {}).get('Listings', [{}])[0]
                    price = offers.get('Price', {}).get('Amount')
                    orig = offers.get('SavingBasis', {}).get('Amount')
                    items.append({
                        'id': it.get('ASIN'),
                        'marketplace': self.name,
                        'code': self.code,
                        'title': it.get('ItemInfo', {}).get('Title', {}).get('DisplayValue'),
                        'url': it.get('DetailPageURL') or f"https://www.amazon.in/dp/{it.get('ASIN')}",
                        'price': float(price) if price else None,
                        'original_price': float(orig) if orig else None,
                        'seller': offers.get('MerchantInfo', {}).get('Name', 'Amazon Prime Seller'),
                        'rating': float(it.get('CustomerReviews', {}).get('StarRating', 4.5) or 4.5),
                        'availability': True,
                    })
                # Record successful connection timestamp
                from django.utils import timezone
                marketplace_obj = get_or_create_marketplace(self.code, self.name, self.base_url)
                marketplace_obj.last_successful = timezone.now()
                marketplace_obj.save(update_fields=['last_successful'])
                return {'status': 'success', 'marketplace': self.name, 'code': self.code, 'items': items}
            else:
                return {
                    'status': 'error',
                    'marketplace': self.name,
                    'code': self.code,
                    'reason': f"Amazon PA-API returned HTTP {resp.status_code}",
                    'items': []
                }
        except Exception as e:
            logger.error("Amazon PA-API fetch failed: %s", e)
            return {
                'status': 'error',
                'marketplace': self.name,
                'code': self.code,
                'reason': f"Network/Auth error: {str(e)}",
                'items': []
            }
    def fetch_listing(self, listing_id: str) -> Dict[str, Any]:
        configured, reason = self.is_configured()
        if not configured:
            return {'status': 'unavailable', 'marketplace': self.name, 'code': self.code, 'reason': reason, 'listing': None}
        return {'status': 'error', 'marketplace': self.name, 'reason': 'Direct listing fetch requiring active PA-API subscription', 'listing': None}

class FlipkartAdapter(BaseMarketplaceAdapter):
    code = "flipkart"
    name = "Flipkart"
    base_url = "https://www.flipkart.com"

    def __init__(self):
        self.affiliate_id = getattr(settings, 'FLIPKART_AFFILIATE_ID', '').strip()
        self.affiliate_token = getattr(settings, 'FLIPKART_AFFILIATE_TOKEN', '').strip()

    def is_configured(self) -> Tuple[bool, str]:
        missing = []
        if not self.affiliate_id:
            missing.append("FLIPKART_AFFILIATE_ID")
        if not self.affiliate_token:
            missing.append("FLIPKART_AFFILIATE_TOKEN")

        if missing:
            return False, f"Flipkart Affiliate credentials missing: {', '.join(missing)}"
        return True, "Configured"

    def search(self, query: str) -> Dict[str, Any]:
        configured, reason = self.is_configured()
        if not configured:
            return {
                'status': 'unavailable',
                'marketplace': self.name,
                'code': self.code,
                'reason': reason,
                'items': []
            }

        try:
            url = f"https://affiliate-api.flipkart.net/affiliate/1.0/search.json?query={query}&resultCount=5"
            headers = {
                'Fk-Affiliate-Id': self.affiliate_id,
                'Fk-Affiliate-Token': self.affiliate_token,
            }
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for product_item in data.get('productInfoList', []):
                    base = product_item.get('productBaseInfo', {}).get('productAttributes', {})
                    price = base.get('sellingPrice', {}).get('amount')
                    orig = base.get('maximumRetailPrice', {}).get('amount')
                    items.append({
                        'id': product_item.get('productBaseInfo', {}).get('productIdentifier', {}).get('productId'),
                        'marketplace': self.name,
                        'code': self.code,
                        'title': base.get('title'),
                        'url': base.get('productUrl') or f"https://www.flipkart.com/p/{product_item.get('productBaseInfo', {}).get('productIdentifier', {}).get('productId')}",
                        'price': float(price) if price else None,
                        'original_price': float(orig) if orig else None,
                        'seller': 'OmniTechRetail',
                        'rating': 4.4,
                        'availability': True,
                    })
                return {'status': 'success', 'marketplace': self.name, 'code': self.code, 'items': items}
            else:
                return {
                    'status': 'error',
                    'marketplace': self.name,
                    'code': self.code,
                    'reason': f"Flipkart API returned HTTP {resp.status_code}",
                    'items': []
                }
        except Exception as e:
            logger.error("Flipkart affiliate fetch failed: %s", e)
            return {
                'status': 'error',
                'marketplace': self.name,
                'code': self.code,
                'reason': f"Network error: {str(e)}",
                'items': []
            }

    def fetch_listing(self, listing_id: str) -> Dict[str, Any]:
        configured, reason = self.is_configured()
        if not configured:
            return {'status': 'unavailable', 'marketplace': self.name, 'code': self.code, 'reason': reason, 'listing': None}
        return {'status': 'error', 'marketplace': self.name, 'reason': 'Direct listing fetch requiring active Flipkart Affiliate subscription', 'listing': None}

def get_marketplace_adapters():
    return {
        'amazon_in': AmazonIndiaAdapter(),
        'flipkart': FlipkartAdapter(),
    }

def search_marketplaces_concurrently(query: str) -> Dict[str, Any]:
    """
    Executes concurrent search across Amazon India and Flipkart adapters.
    Returns combined results and connector status without blocking.
    """
    adapters = get_marketplace_adapters()
    results = {}

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_code = {
            executor.submit(adapter.search, query): code
            for code, adapter in adapters.items()
        }
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                results[code] = future.result()
            except Exception as e:
                results[code] = {
                    'status': 'error',
                    'marketplace': adapters[code].name,
                    'code': code,
                    'reason': str(e),
                    'items': []
                }
    return results
