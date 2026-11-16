from django.urls import path
from .views import (
    ReviewAnalyzePostView,
    ReviewCSVUploadGlobalView,
    ProductReviewListView,
    ReviewCSVUploadView,
    ProductReviewAnalysisView,
)

urlpatterns = [
    path('analyze/', ReviewAnalyzePostView.as_view(), name='review_analyze_post'),
    path('upload-csv/', ReviewCSVUploadGlobalView.as_view(), name='review_upload_csv_global'),
    path('<int:product_id>/', ProductReviewListView.as_view(), name='product_reviews'),
    path('<int:product_id>/upload-csv/', ReviewCSVUploadView.as_view(), name='review_upload_csv'),
    path('<int:product_id>/analysis/', ProductReviewAnalysisView.as_view(), name='review_analysis'),
]
