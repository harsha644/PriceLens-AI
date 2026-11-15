import re
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from typing import List, Dict, Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords

from .models import ProductReview, ReviewAnalysis
from catalog.models import Product

try:
    STOP_WORDS = set(stopwords.words('english'))
except Exception:
    import nltk
    nltk.download('stopwords', quiet=True)
    STOP_WORDS = set(stopwords.words('english'))

# Extra common non-informative words
STOP_WORDS.update({'phone', 'product', 'item', 'device', 'bought', 'buy', 'one', 'get', 'also'})

class ReviewAnalysisService:
    vader = SentimentIntensityAnalyzer()

    @classmethod
    def analyze_product_reviews(cls, product: Product, include_demo: bool = True) -> ReviewAnalysis:
        qs = product.reviews.all()
        if not include_demo:
            qs = qs.filter(is_demo=False)

        reviews_list = list(qs)
        total_reviews = len(reviews_list)

        if total_reviews == 0:
            analysis, _ = ReviewAnalysis.objects.update_or_create(
                product=product,
                defaults={
                    'total_reviews': 0,
                    'average_rating': Decimal('0.00'),
                    'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                    'sentiment_distribution': {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0},
                    'sentiment_score': Decimal('0.00'),
                    'top_positive_words': [],
                    'top_negative_words': [],
                    'duplicate_count': 0,
                    'similar_count': 0,
                    'rating_sentiment_mismatches': 0,
                    'suspicious_indicators': []
                }
            )
            return analysis

        # 1. Rating Distribution and Average
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_rating_sum = 0.0
        for r in reviews_list:
            star = int(round(float(r.rating)))
            star = max(1, min(5, star))
            rating_counts[star] += 1
            total_rating_sum += float(r.rating)

        avg_rating = round(total_rating_sum / total_reviews, 2)

        # 2. VADER + TextBlob Sentiment Analysis
        pos_count = 0
        neu_count = 0
        neg_count = 0
        compound_sum = 0.0

        pos_texts = []
        neg_texts = []
        mismatches = 0
        cleaned_texts = []

        for r in reviews_list:
            text = (r.review_text or '').strip()
            title = (r.review_title or '').strip()
            full_text = f"{title} {text}".strip()
            cleaned_texts.append(full_text.lower())

            # Sentiment calculation
            vader_score = cls.vader.polarity_scores(full_text)['compound']
            tb_score = TextBlob(full_text).sentiment.polarity
            combined_score = (vader_score * 0.7) + (tb_score * 0.3)
            compound_sum += combined_score

            if combined_score >= 0.05:
                pos_count += 1
                pos_texts.append(full_text)
            elif combined_score <= -0.05:
                neg_count += 1
                neg_texts.append(full_text)
            else:
                neu_count += 1

            # Rating vs Sentiment Mismatch check
            star_float = float(r.rating)
            if star_float >= 4.0 and combined_score <= -0.2:
                mismatches += 1
            elif star_float <= 2.0 and combined_score >= 0.2:
                mismatches += 1

        pct_pos = round((pos_count / total_reviews) * 100, 1)
        pct_neu = round((neu_count / total_reviews) * 100, 1)
        pct_neg = round((neg_count / total_reviews) * 100, 1)
        avg_compound = round(compound_sum / total_reviews, 3)

        # 3. Top Positive and Negative Words
        def extract_keywords(texts: List[str]) -> List[Dict[str, Any]]:
            words = []
            for t in texts:
                tokens = re.findall(r'\b[a-zA-Z]{3,}\b', t.lower())
                for tok in tokens:
                    if tok not in STOP_WORDS:
                        words.append(tok)
            counter = Counter(words)
            return [{'word': word, 'count': count} for word, count in counter.most_common(8)]

        top_pos = extract_keywords(pos_texts)
        top_neg = extract_keywords(neg_texts)

        # 4. Exact Duplicate Detection
        text_freq = Counter(cleaned_texts)
        duplicate_count = sum(cnt - 1 for cnt in text_freq.values() if cnt > 1)

        # 5. Similar Reviews (TF-IDF Cosine Similarity)
        similar_count = 0
        if len(cleaned_texts) >= 2:
            try:
                vectorizer = TfidfVectorizer(stop_words='english', max_features=500)
                tfidf_matrix = vectorizer.fit_transform(cleaned_texts)
                sim_matrix = cosine_similarity(tfidf_matrix)
                n = len(cleaned_texts)
                for i in range(n):
                    for j in range(i + 1, n):
                        # If texts are not identical but cosine similarity > 0.85
                        if cleaned_texts[i] != cleaned_texts[j] and sim_matrix[i][j] >= 0.85:
                            similar_count += 1
            except Exception:
                similar_count = 0

        # 6. Suspicious Pattern Indicators (Never called 'fake reviews', always 'potential indicators')
        indicators = []
        if duplicate_count > 0:
            indicators.append({
                'type': 'repeated_text',
                'severity': 'medium' if duplicate_count < 3 else 'high',
                'detail': f"{duplicate_count} reviews have identical content across different submissions."
            })

        if similar_count > 0:
            indicators.append({
                'type': 'high_similarity_cluster',
                'severity': 'medium',
                'detail': f"{similar_count} review pairs exhibit near-identical phrasing and structure."
            })

        if mismatches > 0:
            indicators.append({
                'type': 'rating_sentiment_mismatch',
                'severity': 'low' if mismatches <= 2 else 'medium',
                'detail': f"{mismatches} reviews show strong divergence between star rating and sentiment tone."
            })

        # Generic short text check
        generic_count = 0
        for ct in cleaned_texts:
            tokens = ct.split()
            if len(tokens) <= 4 or (len(set(tokens)) <= 2 and len(tokens) >= 3):
                generic_count += 1

        if generic_count > 0:
            indicators.append({
                'type': 'generic_text',
                'severity': 'low',
                'detail': f"{generic_count} reviews contain very short or repetitive generic comments."
            })

        # Burst timing check (e.g. >= 3 reviews within 15 minutes)
        sorted_dates = sorted([r.created_at for r in reviews_list if r.created_at])
        burst_found = False
        if len(sorted_dates) >= 3:
            for i in range(len(sorted_dates) - 2):
                if sorted_dates[i + 2] - sorted_dates[i] <= timedelta(minutes=15):
                    burst_found = True
                    break
        if burst_found:
            indicators.append({
                'type': 'burst_timing',
                'severity': 'medium',
                'detail': "Cluster of reviews detected within a narrow timeframe."
            })

        # 7. Persist to ReviewAnalysis
        analysis, _ = ReviewAnalysis.objects.update_or_create(
            product=product,
            defaults={
                'total_reviews': total_reviews,
                'average_rating': Decimal(str(avg_rating)),
                'rating_distribution': rating_counts,
                'sentiment_distribution': {
                    'positive': pct_pos,
                    'neutral': pct_neu,
                    'negative': pct_neg
                },
                'sentiment_score': Decimal(str(avg_compound)),
                'top_positive_words': top_pos,
                'top_negative_words': top_neg,
                'duplicate_count': duplicate_count,
                'similar_count': similar_count,
                'rating_sentiment_mismatches': mismatches,
                'suspicious_indicators': indicators
            }
        )

        return analysis
