import io
import pandas as pd
from decimal import Decimal
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ProductReview, ReviewAnalysis
from .serializers import ProductReviewSerializer, ManualReviewCreateSerializer, ReviewAnalysisSerializer
from .services import ReviewAnalysisService
from catalog.models import Product

class ProductReviewListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        demo_only = request.query_params.get('is_demo', '').lower() in ['true', '1']

        qs = product.reviews.all()
        if demo_only:
            qs = qs.filter(is_demo=True)
        elif not include_demo:
            qs = qs.filter(is_demo=False)

        serializer = ProductReviewSerializer(qs.order_by('-created_at')[:100], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        is_demo = request.data.get('is_demo', False)

        # Allow single or bulk array
        data = request.data.get('reviews') if 'reviews' in request.data else request.data
        if isinstance(data, list):
            created_reviews = []
            for item in data:
                ser = ManualReviewCreateSerializer(data=item)
                if ser.is_valid():
                    rev = ProductReview.objects.create(
                        product=product,
                        user=request.user,
                        source='manual',
                        reviewer_name=ser.validated_data.get('reviewer_name', 'Anonymous') or 'Anonymous',
                        review_title=ser.validated_data.get('review_title', ''),
                        review_text=ser.validated_data['review_text'],
                        rating=ser.validated_data['rating'],
                        is_verified_purchase=ser.validated_data.get('is_verified_purchase', False),
                        is_demo=is_demo
                    )
                    created_reviews.append(rev)
            # Re-run analysis
            ReviewAnalysisService.analyze_product_reviews(product, include_demo=True)
            return Response({'message': f'Successfully added {len(created_reviews)} reviews.'}, status=status.HTTP_201_CREATED)
        else:
            ser = ManualReviewCreateSerializer(data=data)
            if ser.is_valid():
                rev = ProductReview.objects.create(
                    product=product,
                    user=request.user,
                    source='manual',
                    reviewer_name=ser.validated_data.get('reviewer_name', 'Anonymous') or 'Anonymous',
                    review_title=ser.validated_data.get('review_title', ''),
                    review_text=ser.validated_data['review_text'],
                    rating=ser.validated_data['rating'],
                    is_verified_purchase=ser.validated_data.get('is_verified_purchase', False),
                    is_demo=is_demo
                )
                ReviewAnalysisService.analyze_product_reviews(product, include_demo=True)
                return Response(ProductReviewSerializer(rev).data, status=status.HTTP_201_CREATED)
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

class ReviewCSVUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response({'error': 'No CSV file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_file.name.lower().endswith('.csv'):
            return Response({'error': 'File must be in CSV format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_csv(io.StringIO(csv_file.read().decode('utf-8', errors='ignore')))
        except Exception as e:
            return Response({'error': f'Failed to parse CSV file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Normalize column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Identify required columns
        text_col = None
        for col in ['review_text', 'text', 'comment', 'review', 'body']:
            if col in df.columns:
                text_col = col
                break

        rating_col = None
        for col in ['rating', 'stars', 'score']:
            if col in df.columns:
                rating_col = col
                break

        if not text_col or not rating_col:
            return Response({
                'error': f'CSV must include at least review text and rating columns. Found: {list(df.columns)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        name_col = next((c for c in ['reviewer_name', 'name', 'author', 'user'] if c in df.columns), None)
        title_col = next((c for c in ['review_title', 'title', 'headline'] if c in df.columns), None)

        imported_count = 0
        is_demo = request.data.get('is_demo', False) in ['true', 'True', True, 1]

        for _, row in df.iterrows():
            raw_text = str(row[text_col]).strip() if pd.notna(row[text_col]) else ""
            if not raw_text or raw_text.lower() == 'nan':
                continue

            try:
                raw_rating = float(row[rating_col])
                clamped_rating = max(1.0, min(5.0, raw_rating))
            except (ValueError, TypeError):
                continue

            reviewer = str(row[name_col]).strip() if (name_col and pd.notna(row[name_col])) else "Anonymous"
            title = str(row[title_col]).strip() if (title_col and pd.notna(row[title_col])) else ""

            ProductReview.objects.create(
                product=product,
                user=request.user,
                source='csv',
                reviewer_name=reviewer,
                review_title=title,
                review_text=raw_text,
                rating=Decimal(str(round(clamped_rating, 1))),
                is_demo=is_demo
            )
            imported_count += 1

        # Automatically update analysis
        analysis = ReviewAnalysisService.analyze_product_reviews(product, include_demo=True)
        return Response({
            'message': f'Successfully ingested {imported_count} reviews from CSV.',
            'total_imported': imported_count,
            'analysis': ReviewAnalysisSerializer(analysis).data
        }, status=status.HTTP_201_CREATED)

class ProductReviewAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        include_demo = request.query_params.get('include_demo', '').lower() in ['true', '1']
        force_refresh = request.query_params.get('refresh', '').lower() in ['true', '1']

        try:
            analysis = product.analysis
            if force_refresh:
                analysis = ReviewAnalysisService.analyze_product_reviews(product, include_demo=include_demo)
        except ReviewAnalysis.DoesNotExist:
            analysis = ReviewAnalysisService.analyze_product_reviews(product, include_demo=include_demo)

        serializer = ReviewAnalysisSerializer(analysis)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        include_demo = request.data.get('include_demo', True)
        analysis = ReviewAnalysisService.analyze_product_reviews(product, include_demo=include_demo)
        return Response(ReviewAnalysisSerializer(analysis).data, status=status.HTTP_200_OK)
