from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Product, ProductImage
from .serializers import ProductSerializer, ProductImageSerializer, ProductImageUploadSerializer, ProductMatchRequestSerializer
from .matching import ProductMatchingService
from recommendations.models import SearchHistory

class ProductListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '').strip()
        brand = request.query_params.get('brand', '').strip()
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        demo_only = request.query_params.get('is_demo', '').lower() in ['true', '1']

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
                Q(variant__icontains=query)
            )
            # Record user search history
            if request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    query=query,
                    category=category,
                    filters={'brand': brand, 'include_demo': include_demo}
                )

        serializer = ProductSerializer(qs.order_by('-created_at')[:50], many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        serializer = ProductMatchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        candidate = serializer.validated_data

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
            }
            score, reasons, compatible = ProductMatchingService.match_products(target_dict, candidate)
            return Response({
                'target_product_id': target_product.id,
                'target_name': target_product.name,
                'candidate': candidate,
                'match_score': score,
                'is_compatible': compatible,
                'reasons': reasons
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
                }
                score, reasons, compatible = ProductMatchingService.match_products(target_dict, candidate)
                results.append({
                    'product_id': prod.id,
                    'product_name': prod.name,
                    'brand': prod.brand,
                    'category': prod.category,
                    'match_score': score,
                    'is_compatible': compatible,
                    'reasons': reasons
                })
            results.sort(key=lambda x: x['match_score'], reverse=True)
            return Response({'matches': results[:10]})

class ProductCategoriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = Product.objects.values_list('category', flat=True).distinct()
        brands = Product.objects.values_list('brand', flat=True).distinct()
        return Response({
            'categories': sorted(list(set(c for c in categories if c))),
            'brands': sorted(list(set(b for b in brands if b))),
        })
