from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import SearchHistory, UserRecommendation
from .serializers import SearchHistorySerializer, UserRecommendationSerializer
from .services import RecommendationService
from catalog.models import Product

class IsOwnerPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class ProductRecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        result = RecommendationService.generate_recommendation_for_product(
            product=product,
            user=request.user,
            include_demo=include_demo
        )
        return Response(result, status=status.HTTP_200_OK)

class TopRecommendationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        products_qs = Product.objects.all()
        if not include_demo:
            products_qs = products_qs.filter(is_demo=False)

        recommendations = []
        for prod in products_qs[:10]:
            rec = RecommendationService.generate_recommendation_for_product(
                product=prod,
                user=request.user,
                include_demo=include_demo
            )
            if rec.get('best_listing_id'):
                recommendations.append(rec)

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return Response(recommendations, status=status.HTTP_200_OK)

class SearchHistoryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Strict object-level isolation: only return the logged-in user's entries
        history = SearchHistory.objects.filter(user=request.user).order_by('-created_at')[:50]
        serializer = SearchHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        # Clear all user's search history
        deleted_count, _ = SearchHistory.objects.filter(user=request.user).delete()
        return Response({'message': f'Deleted {deleted_count} search history items.'}, status=status.HTTP_200_OK)

class SearchHistoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerPermission]

    def delete(self, request, pk):
        item = get_object_or_404(SearchHistory, pk=pk)
        self.check_object_permissions(request, item)
        item.delete()
        return Response({'message': 'Search history entry deleted.'}, status=status.HTTP_204_NO_CONTENT)
