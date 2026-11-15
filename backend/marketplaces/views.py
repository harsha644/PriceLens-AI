from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Min, Max, Avg
from .models import Marketplace, MarketplaceListing, PriceHistory
from .serializers import MarketplaceListingSerializer, PriceHistorySerializer
from .adapters import get_marketplace_adapters
from catalog.models import Product
from catalog.serializers import ProductSerializer

class MarketplaceStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        adapters = get_marketplace_adapters()
        status_report = {}
        for code, adapter in adapters.items():
            configured, reason = adapter.is_configured()
            status_report[code] = {
                'name': adapter.name,
                'code': code,
                'status': 'available' if configured else 'unavailable',
                'reason': reason,
                'is_configured': configured
            }
        return Response(status_report, status=status.HTTP_200_OK)

class ProductComparisonView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        demo_only = request.query_params.get('is_demo', '').lower() in ['true', '1']

        listings_qs = product.listings.all()
        if demo_only:
            listings_qs = listings_qs.filter(is_demo=True)
        elif not include_demo:
            listings_qs = listings_qs.filter(is_demo=False)

        listings_data = MarketplaceListingSerializer(listings_qs, many=True).data

        # Connector status
        adapters = get_marketplace_adapters()
        connector_status = {}
        for code, adapter in adapters.items():
            configured, reason = adapter.is_configured()
            connector_status[code] = {
                'name': adapter.name,
                'status': 'available' if configured else 'unavailable',
                'reason': reason,
            }

        # Pricing statistics
        prices = [float(l['current_price']) for l in listings_data if l.get('current_price')]
        lowest_price = min(prices) if prices else None
        highest_price = max(prices) if prices else None
        price_diff = (highest_price - lowest_price) if (lowest_price and highest_price) else 0

        best_deal = None
        if listings_data:
            available_listings = [l for l in listings_data if l.get('is_available')]
            pool = available_listings if available_listings else listings_data
            best_deal = min(pool, key=lambda x: float(x.get('current_price', 999999999)))

        return Response({
            'product': ProductSerializer(product, context={'request': request}).data,
            'listings': listings_data,
            'connector_status': connector_status,
            'summary': {
                'lowest_price': lowest_price,
                'highest_price': highest_price,
                'max_savings': round(price_diff, 2),
                'best_deal': best_deal,
                'total_listings': len(listings_data),
            }
        }, status=status.HTTP_200_OK)

class ProductPriceHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        demo_only = request.query_params.get('is_demo', '').lower() in ['true', '1']

        history_qs = product.price_history.select_related('listing__marketplace').all()
        if demo_only:
            history_qs = history_qs.filter(is_demo=True)
        elif not include_demo:
            history_qs = history_qs.filter(is_demo=False)

        history_qs = history_qs.order_by('timestamp')

        prices = [float(h.price) for h in history_qs]
        current_price = prices[-1] if prices else None
        lowest_price = min(prices) if prices else None
        highest_price = max(prices) if prices else None
        avg_price = round(sum(prices) / len(prices), 2) if prices else None

        # Build timeline series by marketplace
        series = []
        amz_points = []
        fk_points = []

        for h in history_qs:
            ts_iso = h.timestamp.isoformat()
            ts_label = h.timestamp.strftime('%Y-%m-%d')
            val = float(h.price)
            code = h.listing.marketplace.code

            series.append({
                'timestamp': ts_iso,
                'date': ts_label,
                'price': val,
                'marketplace': h.listing.marketplace.name,
                'code': code,
            })

            if code == 'amazon_in':
                amz_points.append({'date': ts_label, 'price': val})
            elif code == 'flipkart':
                fk_points.append({'date': ts_label, 'price': val})

        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'stats': {
                'current_price': current_price,
                'lowest_price': lowest_price,
                'highest_price': highest_price,
                'average_price': avg_price,
                'total_data_points': len(prices)
            },
            'series': series,
            'amazon_series': amz_points,
            'flipkart_series': fk_points,
        }, status=status.HTTP_200_OK)

class MarketplaceSearchLiveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'Search query parameter "q" is required.'}, status=status.HTTP_400_BAD_REQUEST)

        adapters = get_marketplace_adapters()
        results = {}
        for code, adapter in adapters.items():
            results[code] = adapter.search(query)

        return Response(results, status=status.HTTP_200_OK)
