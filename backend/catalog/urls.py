from django.urls import path
from .views import (
    ProductListCreateView,
    ProductDetailView,
    ProductSearchView,
    ProductImageUploadView,
    ProductIdentifyImageView,
    ProductConfirmView,
    ProductMatchView,
    ProductCategoriesView,
    ProductPriceHistoryProxyView,
)

urlpatterns = [
    # Catalog endpoints requested in Master Prompt
    path('', ProductListCreateView.as_view(), name='catalog_root'),
    path('products/', ProductListCreateView.as_view(), name='catalog_products_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='catalog_product_detail_direct'),
    path('products/<int:id>/price-history/', ProductPriceHistoryProxyView.as_view(), name='catalog_product_price_history'),
    path('search/', ProductSearchView.as_view(), name='catalog_search_post'),
    path('upload-image/', ProductImageUploadView.as_view(), name='catalog_upload_image'),
    path('identify-image/', ProductIdentifyImageView.as_view(), name='catalog_identify_image'),
    path('confirm-product/', ProductConfirmView.as_view(), name='catalog_confirm_product'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('match/', ProductMatchView.as_view(), name='product_match_catalog'),
    path('<int:pk>/match/', ProductMatchView.as_view(), name='product_match_detail'),
    path('categories/', ProductCategoriesView.as_view(), name='product_categories'),
]
