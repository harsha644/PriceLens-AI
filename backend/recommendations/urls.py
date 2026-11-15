from django.urls import path
from .views import (
    ProductRecommendationView,
    TopRecommendationsView,
    SearchHistoryListView,
    SearchHistoryDetailView,
)

urlpatterns = [
    path('product/<int:product_id>/', ProductRecommendationView.as_view(), name='product_recommendation'),
    path('top/', TopRecommendationsView.as_view(), name='top_recommendations'),
    path('history/', SearchHistoryListView.as_view(), name='search_history_list'),
    path('history/<int:pk>/', SearchHistoryDetailView.as_view(), name='search_history_detail'),
]
