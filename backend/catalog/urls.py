from django.urls import path
from .views import (
    ProductListCreateView,
    ProductDetailView,
    ProductImageUploadView,
    ProductMatchView,
    ProductCategoriesView,
)

urlpatterns = [
    path('', ProductListCreateView.as_view(), name='product_list_create'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('upload-image/', ProductImageUploadView.as_view(), name='product_image_upload'),
    path('match/', ProductMatchView.as_view(), name='product_match_catalog'),
    path('<int:pk>/match/', ProductMatchView.as_view(), name='product_match_detail'),
    path('categories/', ProductCategoriesView.as_view(), name='product_categories'),
]
