from django.urls import path
from .views import (
    ProductReviewListView,
    ReviewCSVUploadView,
    ProductReviewAnalysisView,
)

urlpatterns = [
    path('<int:product_id>/', ProductReviewListView.as_view(), name='product_reviews'),
    path('<int:product_id>/upload-csv/', ReviewCSVUploadView.as_view(), name='review_upload_csv'),
    path('<int:product_id>/analysis/', ProductReviewAnalysisView.as_view(), name='review_analysis'),
]
