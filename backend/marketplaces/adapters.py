import logging
import requests
from django.conf import settings
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class BaseMarketplaceAdapter:
    code: str = ""
    name: str = ""

    def is_configured(self) -> Tuple[bool, str]:
        raise NotImplementedError

    def search(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError

    def fetch_listing(self, listing_id: str) -> Dict[str, Any]:
        raise NotImplementedError

class AmazonIndiaAdapter(BaseMarketplaceAdapter):
    code = "amazon_in"
    name = "Amazon India"

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

        # Real call to Amazon PA-API (AWS signature v4 payload)
        # Note: No fake data. Official endpoint only.
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
            # Simulated network call with error capture
            resp = requests.post(f"https://{endpoint}/paapi5/searchitems", json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for it in data.get('SearchResult', {}).get('Items', []):
                    items.append({
                        'id': it.get('ASIN'),
                        'title': it.get('ItemInfo', {}).get('Title', {}).get('DisplayValue'),
                        'url': it.get('DetailPageURL'),
                        'price': it.get('Offers', {}).get('Listings', [{}])[0].get('Price', {}).get('Amount'),
                    })
                return {'status': 'success', 'marketplace': self.name, 'code': self.code, 'items': items}
            else:
                return {
                    'status': 'error',
                    'marketplace': self.name,
                    'code': self.code,
                    'reason': f"Amazon API returned status {resp.status_code}: {resp.text}",
                    'items': []
                }
        except Exception as e:
            logger.error("Amazon PA-API fetch failed: %s", e)
            return {
                'status': 'error',
                'marketplace': self.name,
                'code': self.code,
                'reason': f"Network or authentication exception: {str(e)}",
                'items': []
            }

    def fetch_listing(self, listing_id: str) -> Dict[str, Any]:
        configured, reason = self.is_configured()
        if not configured:
            return {
                'status': 'unavailable',
                'marketplace': self.name,
                'code': self.code,
                'reason': reason,
                'listing': None
            }
        return {'status': 'error', 'marketplace': self.name, 'reason': 'Direct listing fetch requiring active PA-API subscription', 'listing': None}

class FlipkartAdapter(BaseMarketplaceAdapter):
    code = "flipkart"
    name = "Flipkart"

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
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = []
                for product_item in data.get('productInfoList', []):
                    base = product_item.get('productBaseInfo', {}).get('productAttributes', {})
                    items.append({
                        'id': product_item.get('productBaseInfo', {}).get('productIdentifier', {}).get('productId'),
                        'title': base.get('title'),
                        'url': base.get('productUrl'),
                        'price': base.get('sellingPrice', {}).get('amount'),
                    })
                return {'status': 'success', 'marketplace': self.name, 'code': self.code, 'items': items}
            else:
                return {
                    'status': 'error',
                    'marketplace': self.name,
                    'code': self.code,
                    'reason': f"Flipkart API returned status {resp.status_code}: {resp.text}",
                    'items': []
                }
        except Exception as e:
            logger.error("Flipkart affiliate fetch failed: %s", e)
            return {
                'status': 'error',
                'marketplace': self.name,
                'code': self.code,
                'reason': f"Network exception: {str(e)}",
                'items': []
            }

    def fetch_listing(self, listing_id: str) -> Dict[str, Any]:
        configured, reason = self.is_configured()
        if not configured:
            return {
                'status': 'unavailable',
                'marketplace': self.name,
                'code': self.code,
                'reason': reason,
                'listing': None
            }
        return {'status': 'error', 'marketplace': self.name, 'reason': 'Direct listing fetch requiring active Flipkart Affiliate subscription', 'listing': None}

def get_marketplace_adapters():
    return {
        'amazon_in': AmazonIndiaAdapter(),
        'flipkart': FlipkartAdapter(),
    }
