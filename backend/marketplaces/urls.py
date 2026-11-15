from django.urls import path
from .views import (
    MarketplaceStatusView,
    ProductComparisonView,
    MarketplaceSearchLiveView,
)

urlpatterns = [
    path('status/', MarketplaceStatusView.as_view(), name='marketplace_status'),
    path('compare/<int:product_id>/', ProductComparisonView.as_view(), name='product_comparison'),
    path('search-live/', MarketplaceSearchLiveView.as_view(), name='marketplace_search_live'),
]
