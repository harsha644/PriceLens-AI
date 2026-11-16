from django.urls import path
from .views import (
    MarketplaceStatusView,
    MarketplaceSearchPostView,
    MarketplaceComparePostView,
    ProductComparisonView,
    ProductPriceHistoryView,
    MarketplaceSearchLiveView,
)

urlpatterns = [
    path('status/', MarketplaceStatusView.as_view(), name='marketplace_status'),
    path('search/', MarketplaceSearchPostView.as_view(), name='marketplace_search_post'),
    path('compare/', MarketplaceComparePostView.as_view(), name='marketplace_compare_post'),
    path('compare/<int:product_id>/', ProductComparisonView.as_view(), name='product_comparison'),
    path('price-history/<int:product_id>/', ProductPriceHistoryView.as_view(), name='product_price_history'),
    path('search-live/', MarketplaceSearchLiveView.as_view(), name='marketplace_search_live'),
]
