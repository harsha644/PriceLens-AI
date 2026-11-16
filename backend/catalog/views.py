from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from decimal import Decimal
from .models import Product, ProductCategory, ProductImage
from .serializers import (
    ProductSerializer,
    ProductCategorySerializer,
    ProductImageSerializer,
    ProductImageUploadSerializer,
    ProductConfirmSerializer,
)
from .vision import ProductVisionEngine, PRODUCT_CATEGORIES
from .matching import ProductMatchingService
from recommendations.models import SearchHistory
from marketplaces.adapters import search_marketplaces_concurrently
from marketplaces.models import MarketplaceListing, PriceHistory
from marketplaces.services import process_marketplace_feeds

class ProductListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '').strip()
        brand = request.query_params.get('brand', '').strip()
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        demo_only = request.query_params.get('is_demo', '').lower() in ['true', '1']
        ordering = request.query_params.get('ordering', '-created_at')

        qs = Product.objects.all()

        if demo_only:
            qs = qs.filter(is_demo=True)
        elif not include_demo:
            qs = qs.filter(is_demo=False)

        if category:
            qs = qs.filter(category__iexact=category)
        if brand:
            qs = qs.filter(brand__iexact=brand)

        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(model__icontains=query) |
                Q(model_number__icontains=query) |
                Q(category__icontains=query) |
                Q(variant__icontains=query) |
                Q(colour__icontains=query) |
                Q(size__icontains=query) |
                Q(material__icontains=query)
            )
            # Record user search history
            if request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    query=query,
                    category=category,
                    filters={'brand': brand, 'include_demo': include_demo}
                )

        # Ordering
        if ordering == 'name':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-created_at')

        # Return flat list of products as expected by tests
        serializer = ProductSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


        query = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '').strip()
        brand = request.query_params.get('brand', '').strip()
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        demo_only = request.query_params.get('is_demo', '').lower() in ['true', '1']
        ordering = request.query_params.get('ordering', '-created_at')

        qs = Product.objects.all()

        if demo_only:
            qs = qs.filter(is_demo=True)
        elif not include_demo:
            qs = qs.filter(is_demo=False)

        if category:
            qs = qs.filter(category__iexact=category)
        if brand:
            qs = qs.filter(brand__iexact=brand)

        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(model__icontains=query) |
                Q(model_number__icontains=query) |
                Q(category__icontains=query) |
                Q(variant__icontains=query) |
                Q(colour__icontains=query) |
                Q(size__icontains=query) |
                Q(material__icontains=query)
            )
            # Record user search history
            if request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    query=query,
                    category=category,
                    filters={'brand': brand, 'include_demo': include_demo}
                )

        # Ordering
        if ordering == 'name':
            qs = qs.order_by('name')
        else:
            qs = qs.order_by('-created_at')

        # Return flat list of products as expected by tests
        serializer = ProductSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductSearchView(APIView):
    """
    POST /api/catalog/search/
    Dynamic universal product search:
    Matches against catalog and queries Amazon India & Flipkart concurrently.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        category = request.data.get('category', '').strip()
        brand = request.data.get('brand', '').strip()
        include_demo = request.data.get('include_demo', True)

        if not query:
            return Response({'error': 'Search query is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Record search history
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            category=category,
            filters={'brand': brand, 'include_demo': include_demo}
        )

        # 1. Search database catalog
        catalog_qs = Product.objects.all() if include_demo else Product.objects.filter(is_demo=False)
        if category:
            catalog_qs = catalog_qs.filter(category__iexact=category)
        if brand:
            catalog_qs = catalog_qs.filter(brand__iexact=brand)

        candidate_input = {'name': query, 'brand': brand, 'category': category}

        matched_products = []
        for prod in catalog_qs[:50]:
            target_dict = {
                'name': prod.name,
                'brand': prod.brand,
                'model': prod.model,
                'model_number': prod.model_number,
                'variant': prod.variant,
                'ram': prod.ram,
                'storage': prod.storage,
                'colour': prod.colour,
                'size': prod.size,
                'material': prod.material,
                'category': prod.category,
            }
            match_res = ProductMatchingService.match_products(target_dict, candidate_input)
            if match_res['match_score'] > 20.0 or match_res['is_compatible']:
                matched_products.append({
                    'product': ProductSerializer(prod, context={'request': request}).data,
                    'match_score': match_res['match_score'],
                    'match_type': match_res['match_type'],
                    'reasons': match_res['reasons'],
                    'mismatches': match_res['mismatches'],
                    'rank_weight': match_res['rank_weight']
                })

        # Sort exact matches first, then by match score
        matched_products.sort(key=lambda x: x['rank_weight'], reverse=True)

        # 2. Trigger concurrent marketplace search on Amazon India & Flipkart
        marketplace_results = search_marketplaces_concurrently(query)

        return Response({
            'query': query,
            'category': category,
            'brand': brand,
            'catalog_matches_count': len(matched_products),
            'exact_matches': [m for m in matched_products if m['match_type'] == 'exact_match'],
            'similar_alternatives': [m for m in matched_products if m['match_type'] != 'exact_match'],
            'marketplace_feeds': marketplace_results
        }, status=status.HTTP_200_OK)

class ProductIdentifyImageView(APIView):
    """
    POST /api/catalog/identify-image/
    Processes uploaded image with Pillow & OpenCV, extracts color, texture, geometry,
    identifies likely category and characteristics across all 22 product categories,
    and returns searchable attributes with confidence score.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProductImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        file_bytes = image_file.read()

        try:
            recognition_result = ProductVisionEngine.identify_product(file_bytes, image_file.name)
        except Exception as e:
            return Response({'error': f'Computer vision processing failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Match identified features against existing products
        candidate_dict = {
            'name': recognition_result['searchable_description'],
            'brand': recognition_result.get('brand', ''),
            'category': recognition_result['category'],
            'colour': recognition_result['colour'],
        }

        existing_candidates = []
        for prod in Product.objects.all()[:30]:
            target_dict = {
                'name': prod.name,
                'brand': prod.brand,
                'category': prod.category,
                'colour': prod.colour,
                'variant': prod.variant,
            }
            match_res = ProductMatchingService.match_products(target_dict, candidate_dict)
            if match_res['match_score'] > 30:
                existing_candidates.append({
                    'product_id': prod.id,
                    'name': prod.name,
                    'brand': prod.brand,
                    'category': prod.category,
                    'match_score': match_res['match_score'],
                    'match_type': match_res['match_type'],
                    'reasons': match_res['reasons'],
                })

        existing_candidates.sort(key=lambda x: x['match_score'], reverse=True)

        return Response({
            'recognition': recognition_result,
            'existing_matches': existing_candidates[:5],
            'categories_available': PRODUCT_CATEGORIES,
        }, status=status.HTTP_200_OK)

class ProductConfirmView(APIView):
    """
    POST /api/catalog/confirm-product/
    Allows user to confirm or edit identified product details, creates or updates
    the Product in MySQL, and automatically launches concurrent Amazon & Flipkart search.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProductConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        cat_name = data.get('category', 'General merchandise')

        # Link or create category
        cat_rel, _ = ProductCategory.objects.get_or_create(name=cat_name)

        product, created = Product.objects.get_or_create(
            brand=data['brand'],
            name=data['name'],
            variant=data.get('variant', ''),
            defaults={
                'category': cat_name,
                'category_rel': cat_rel,
                'model': data.get('model', ''),
                'model_number': data.get('model_number', ''),
                'ram': data.get('ram', ''),
                'storage': data.get('storage', ''),
                'colour': data.get('colour', ''),
                'size': data.get('size', ''),
                'material': data.get('material', ''),
                'specifications': data.get('specifications', {}),
                'is_demo': data.get('is_demo', False),
            }
        )

        # Trigger concurrent Amazon & Flipkart search
        search_term = f"{product.brand} {product.name}".strip()
        marketplace_feeds = search_marketplaces_concurrently(search_term)

        # Trigger concurrent Amazon & Flipkart search
        search_term = f"{product.brand} {product.name}".strip()
        marketplace_feeds = search_marketplaces_concurrently(search_term)

        # Persist marketplace listings and price history
        saved_listings = process_marketplace_feeds(product, marketplace_feeds)

        # Serialize stored listings for response
        listings_data = []
        for l in saved_listings:
            listings_data.append({
                'id': l.id,
                'marketplace': l.marketplace.name,
                'code': l.marketplace.code,
                'title': l.title,
                'url': l.product_url,
                'current_price': float(l.current_price),
                'original_price': float(l.original_price) if l.original_price else None,
                'discount_percent': float(l.discount_percent),
                'seller': l.seller_name,
                'rating': float(l.rating),
                'is_available': l.is_available,
                'shipping': l.shipping_info,
                'is_demo': l.is_demo,
            })

        return Response({
            'message': 'Product confirmed and marketplace data saved.',
            'product': ProductSerializer(product, context={'request': request}).data,
            'is_newly_created': created,
            'marketplace_feeds': marketplace_feeds,
            'stored_listings': listings_data,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ProductDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return Response({'message': 'Product deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

class ProductImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProductImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image_file = serializer.validated_data['image']
        product_id = serializer.validated_data.get('product_id')
        is_primary = serializer.validated_data.get('is_primary', False)
        confirmed = serializer.validated_data.get('confirmed_by_user', True)

        if not confirmed:
            return Response({'error': 'Image upload requires manual user confirmation before attachment.'}, status=status.HTTP_400_BAD_REQUEST)

        if product_id:
            product = get_object_or_404(Product, pk=product_id)
            if is_primary:
                ProductImage.objects.filter(product=product).update(is_primary=False)
            image_instance = ProductImage.objects.create(
                product=product,
                image=image_file,
                is_primary=is_primary,
                confirmed_by_user=True
            )
            return Response(ProductImageSerializer(image_instance, context={'request': request}).data, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Image validated successfully. Confirm product to attach.'}, status=status.HTTP_200_OK)

class ProductMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        candidate = request.data
        if pk:
            target_product = get_object_or_404(Product, pk=pk)
            target_dict = {
                'name': target_product.name,
                'brand': target_product.brand,
                'model': target_product.model,
                'model_number': target_product.model_number,
                'variant': target_product.variant,
                'ram': target_product.ram,
                'storage': target_product.storage,
                'colour': target_product.colour,
                'size': target_product.size,
                'material': target_product.material,
                'category': target_product.category,
            }
            res = ProductMatchingService.match_products(target_dict, candidate)
            return Response({
                'target_product_id': target_product.id,
                'target_name': target_product.name,
                'candidate': candidate,
                **res
            })
        else:
            include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
            products = Product.objects.all() if include_demo else Product.objects.filter(is_demo=False)
            results = []
            for prod in products[:100]:
                target_dict = {
                    'name': prod.name,
                    'brand': prod.brand,
                    'model': prod.model,
                    'model_number': prod.model_number,
                    'variant': prod.variant,
                    'ram': prod.ram,
                    'storage': prod.storage,
                    'colour': prod.colour,
                    'size': prod.size,
                    'material': prod.material,
                    'category': prod.category,
                }
                match_res = ProductMatchingService.match_products(target_dict, candidate)
                results.append({
                    'product_id': prod.id,
                    'product_name': prod.name,
                    'brand': prod.brand,
                    'category': prod.category,
                    **match_res
                })
            results.sort(key=lambda x: x['rank_weight'], reverse=True)
            return Response({'matches': results[:15]})

class ProductCategoriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):


        db_categories = list(Product.objects.values_list('category', flat=True).distinct())
        all_categories = sorted(list(set(db_categories + PRODUCT_CATEGORIES)))
        brands = sorted(list(set(b for b in Product.objects.values_list('brand', flat=True).distinct() if b)))
        return Response({
            'categories': all_categories,
            'brands': brands,
        })

class ProductPriceHistoryProxyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        product = get_object_or_404(Product, pk=id)
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        history_qs = product.price_history.select_related('listing__marketplace').all()
        if not include_demo:
            history_qs = history_qs.filter(is_demo=False)

        history_qs = history_qs.order_by('timestamp')
        prices = [float(h.price) for h in history_qs]
        series = [
            {
                'timestamp': h.timestamp.isoformat(),
                'date': h.timestamp.strftime('%Y-%m-%d'),
                'price': float(h.price),
                'marketplace': h.listing.marketplace.name,
                'code': h.listing.marketplace.code,
            }
            for h in history_qs
        ]

        return Response({
            'product_id': product.id,
            'product_name': product.name,
            'stats': {
                'current_price': prices[-1] if prices else None,
                'lowest_price': min(prices) if prices else None,
                'highest_price': max(prices) if prices else None,
                'total_points': len(prices)
            },
            'series': series
        }, status=status.HTTP_200_OK)
