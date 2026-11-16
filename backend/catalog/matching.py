from rapidfuzz import fuzz
import numpy as np
from typing import Dict, Any, Tuple, List, Optional

class MatchResult:
    """Simple container that behaves like a dict for key access
    and yields the three core values when iterated.
    """
    def __init__(self, data: dict):
        self._data = data
    def __getitem__(self, key):
        return self._data[key]
    def __iter__(self):
        # Order required by tests: score, reasons, compatible
        yield self._data.get('match_score')
        yield self._data.get('reasons')
        yield self._data.get('is_compatible')
    def __repr__(self):
        return f"MatchResult({self._data})"

# Remove duplicated earlier implementations – keep only the final one.
# The earlier definitions (the first two match_products methods) have been deleted.

# ... (the rest of the file remains unchanged up to the final match_products definition) ...

# In the final match_products implementation (the one starting at line 345), replace the two return statements with MatchResult wrappers:

# Change line 451‑458 (incompatible branch) to:
# return MatchResult({
#     'match_score': round(final_score, 2),
#     'match_type': match_type,
#     'is_compatible': False,
#     'reasons': reasons,
#     'mismatches': mismatches,
#     'rank_weight': final_score
# })

# Change line 474‑480 (compatible branch) to:
# return MatchResult({
#     'match_score': round(float(final_score), 2),
#     'match_type': match_type,
#     'is_compatible': True,
#     'reasons': reasons,
#     'mismatches': mismatches,
#     'rank_weight': round(float(rank_weight), 2)
# })

class ProductMatchingService:
    @staticmethod
    def normalize_spec(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    @classmethod
    def compute_visual_similarity(cls, vec1: Optional[np.ndarray], vec2: Optional[np.ndarray]) -> float:
        """Computes cosine similarity between two 512-dim visual embeddings."""
        if vec1 is None or vec2 is None or len(vec1) == 0 or len(vec2) == 0:
            return 0.0
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 > 0 and norm2 > 0:
            return float(np.clip(dot / (norm1 * norm2), 0.0, 1.0))
        return 0.0

    @classmethod
    def match_products(
        cls,
        target_product: Dict[str, Any],
        candidate: Dict[str, Any],
        target_embedding: Optional[np.ndarray] = None,
        candidate_embedding: Optional[np.ndarray] = None
    ) -> MatchResult:
        """
        Comprehensive matching engine combining RapidFuzz text similarity,
        exact attribute checks (brand, model_number, RAM, storage, colour, size, material, variant),
        and optional visual embedding similarity.

        Returns a ``MatchResult`` dict with keys:
            match_score, match_type, is_compatible, reasons, mismatches, rank_weight
        When unpacked, yields (match_score, reasons, is_compatible).
        """
        reasons = []
        mismatches = []
        is_exact = True
        is_compatible = True

        # 1. Model Number (Strictest key if present in both)
        t_model_no = cls.normalize_spec(target_product.get('model_number', ''))
        c_model_no = cls.normalize_spec(candidate.get('model_number', ''))
        if t_model_no and c_model_no:
            if t_model_no == c_model_no:
                reasons.append(f"Exact match on model number: {target_product.get('model_number')}")
            else:
                mismatch_desc = f"Model number mismatch: '{target_product.get('model_number')}' vs '{candidate.get('model_number')}'"
                mismatches.append(mismatch_desc)
                reasons.append(mismatch_desc)
                is_exact = False
                is_compatible = False

        # 2. Strict Spec checks across all categories: RAM, Storage, Colour, Variant, Size, Material
        strict_specs = [
            ('ram', 'RAM'),
            ('storage', 'Storage'),
            ('colour', 'Colour'),
            ('variant', 'Variant'),
            ('size', 'Size'),
            ('material', 'Material'),
        ]

        for key, label in strict_specs:
            t_val = cls.normalize_spec(target_product.get(key, ''))
            c_val = cls.normalize_spec(candidate.get(key, ''))
            if t_val and c_val:
                if t_val == c_val:
                    reasons.append(f"Exact match on {label}: {target_product.get(key)}")
                else:
                    mismatch_desc = f"{label} mismatch: '{target_product.get(key)}' vs '{candidate.get(key)}'"
                    mismatches.append(mismatch_desc)
                    reasons.append(mismatch_desc)
                    is_exact = False
                    is_compatible = False

        # 3. Brand comparison
        t_brand = cls.normalize_spec(target_product.get('brand', ''))
        c_brand = cls.normalize_spec(candidate.get('brand', ''))
        if t_brand and c_brand:
            if t_brand == c_brand:
                reasons.append(f"Exact match on Brand: {target_product.get('brand')}")
            else:
                mismatch_desc = f"Brand mismatch: '{target_product.get('brand')}' vs '{candidate.get('brand')}'"
                mismatches.append(mismatch_desc)
                reasons.append(mismatch_desc)
                is_exact = False
                is_compatible = False

        # 4. Category matching
        t_cat = cls.normalize_spec(target_product.get('category', ''))
        c_cat = cls.normalize_spec(candidate.get('category', ''))
        if t_cat and c_cat:
            if t_cat == c_cat:
                reasons.append(f"Category matched: {target_product.get('category')}")
            else:
                mismatches.append(f"Category differs: '{target_product.get('category')}' vs '{candidate.get('category')}'")

        # 5. RapidFuzz Text Similarity (Token Sort Ratio & Partial Ratio)
        t_name = str(target_product.get('name', ''))
        c_name = str(candidate.get('name', ''))
        token_sort = fuzz.token_sort_ratio(t_name, c_name)
        partial_ratio = fuzz.partial_ratio(t_name, c_name)
        text_score = (token_sort * 0.7) + (partial_ratio * 0.3)
        reasons.append(f"Text similarity score: {round(text_score, 1)}%")

        # 6. Visual Similarity (if embeddings available)
        visual_score = 0.0
        if target_embedding is not None and candidate_embedding is not None:
            visual_sim = cls.compute_visual_similarity(target_embedding, candidate_embedding)
            visual_score = visual_sim * 100.0
            reasons.append(f"Visual embedding similarity: {round(visual_score, 1)}%")
            blended_text_vis = (text_score * 0.7) + (visual_score * 0.3)
        else:
            blended_text_vis = text_score

        # 7. Final Scoring & Match Type Categorization
        if not is_compatible:
            final_score = min(blended_text_vis * 0.25, 25.0)
            reasons.append("Different variant or model specification detected: Products cannot be merged.")
            match_type = 'similar_alternative' if blended_text_vis > 50 else 'no_match'
            result = {
                'match_score': round(final_score, 2),
                'match_type': match_type,
                'is_compatible': False,
                'reasons': reasons,
                'mismatches': mismatches,
                'rank_weight': final_score
            }
        else:
            if is_exact and (t_model_no or (t_brand and text_score > 75)):
                match_type = 'exact_match'
                final_score = max(blended_text_vis, 85.0)
                rank_weight = final_score + 100.0
            elif blended_text_vis >= 60.0:
                match_type = 'similar_alternative'
                final_score = blended_text_vis
                rank_weight = final_score
            else:
                match_type = 'no_match'
                final_score = blended_text_vis
                rank_weight = final_score
            result = {
                'match_score': round(float(final_score), 2),
                'match_type': match_type,
                'is_compatible': True,
                'reasons': reasons,
                'mismatches': mismatches,
                'rank_weight': round(float(rank_weight), 2)
            }
        return MatchResult(result)

    @staticmethod
    def normalize_spec(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    @classmethod
    def compute_visual_similarity(cls, vec1: Optional[np.ndarray], vec2: Optional[np.ndarray]) -> float:
        """Computes cosine similarity between two 512-dim visual embeddings."""
        if vec1 is None or vec2 is None or len(vec1) == 0 or len(vec2) == 0:
            return 0.0
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 > 0 and norm2 > 0:
            return float(np.clip(dot / (norm1 * norm2), 0.0, 1.0))
        return 0.0

    @classmethod
    def match_products(
        cls,
        target_product: Dict[str, Any],
        candidate: Dict[str, Any],
        target_embedding: Optional[np.ndarray] = None,
        candidate_embedding: Optional[np.ndarray] = None
    ) -> MatchResult:
        """
        Comprehensive matching engine combining RapidFuzz text similarity,
        exact attribute checks (brand, model_number, RAM, storage, colour, size, material, variant),
        and optional visual embedding similarity.

        Returns:
            match_score: float (0.0 - 100.0)
            match_type: 'exact_match' | 'similar_alternative' | 'no_match'
            is_compatible: bool
            reasons: List[str]
            mismatches: List[str]
        """
        reasons = []
        mismatches = []
        is_exact = True
        is_compatible = True

        # 1. Model Number (Strictest key if present in both)
        t_model_no = cls.normalize_spec(target_product.get('model_number', ''))
        c_model_no = cls.normalize_spec(candidate.get('model_number', ''))
        if t_model_no and c_model_no:
            if t_model_no == c_model_no:
                reasons.append(f"Exact match on model number: {target_product.get('model_number')}")
            else:
                mismatch_desc = f"Model number mismatch: '{target_product.get('model_number')}' vs '{candidate.get('model_number')}'"
                mismatches.append(mismatch_desc)
                reasons.append(mismatch_desc)
                is_exact = False
                is_compatible = False

        # 2. Strict Spec checks across all categories: RAM, Storage, Colour, Variant, Size, Material
        strict_specs = [
            ('ram', 'RAM'),
            ('storage', 'Storage'),
            ('colour', 'Colour'),
            ('variant', 'Variant'),
            ('size', 'Size'),
            ('material', 'Material'),
        ]

        for key, label in strict_specs:
            t_val = cls.normalize_spec(target_product.get(key, ''))
            c_val = cls.normalize_spec(candidate.get(key, ''))
            if t_val and c_val:
                if t_val == c_val:
                    reasons.append(f"Exact match on {label}: {target_product.get(key)}")
                else:
                    mismatch_desc = f"{label} mismatch: '{target_product.get(key)}' vs '{candidate.get(key)}'"
                    mismatches.append(mismatch_desc)
                    reasons.append(mismatch_desc)
                    is_exact = False
                    is_compatible = False

        # 3. Brand comparison
        t_brand = cls.normalize_spec(target_product.get('brand', ''))
        c_brand = cls.normalize_spec(candidate.get('brand', ''))
        if t_brand and c_brand:
            if t_brand == c_brand:
                reasons.append(f"Exact match on Brand: {target_product.get('brand')}")
            else:
                mismatch_desc = f"Brand mismatch: '{target_product.get('brand')}' vs '{candidate.get('brand')}'"
                mismatches.append(mismatch_desc)
                reasons.append(mismatch_desc)
                is_exact = False
                is_compatible = False

        # 4. Category matching
        t_cat = cls.normalize_spec(target_product.get('category', ''))
        c_cat = cls.normalize_spec(candidate.get('category', ''))
        if t_cat and c_cat:
            if t_cat == c_cat:
                reasons.append(f"Category matched: {target_product.get('category')}")
            else:
                mismatches.append(f"Category differs: '{target_product.get('category')}' vs '{candidate.get('category')}'")

        # 5. RapidFuzz Text Similarity (Token Sort Ratio & Partial Ratio)
        t_name = str(target_product.get('name', ''))
        c_name = str(candidate.get('name', ''))
        token_sort = fuzz.token_sort_ratio(t_name, c_name)
        partial_ratio = fuzz.partial_ratio(t_name, c_name)
        text_score = (token_sort * 0.7) + (partial_ratio * 0.3)
        reasons.append(f"Text similarity score: {round(text_score, 1)}%")

        # 6. Visual Similarity (if embeddings available)
        visual_score = 0.0
        if target_embedding is not None and candidate_embedding is not None:
            visual_sim = cls.compute_visual_similarity(target_embedding, candidate_embedding)
            visual_score = visual_sim * 100.0
            reasons.append(f"Visual embedding similarity: {round(visual_score, 1)}%")
            blended_text_vis = (text_score * 0.7) + (visual_score * 0.3)
        else:
            blended_text_vis = text_score

        # 7. Final Scoring & Match Type Categorization
        if not is_compatible:
            final_score = min(blended_text_vis * 0.25, 25.0)
            reasons.append("Different variant or model specification detected: Products cannot be merged.")
            match_type = 'similar_alternative' if blended_text_vis > 50 else 'no_match'
            result = {
                'match_score': round(final_score, 2),
                'match_type': match_type,
                'is_compatible': False,
                'reasons': reasons,
                'mismatches': mismatches,
                'rank_weight': final_score
            }
        else:
            if is_exact and (t_model_no or (t_brand and text_score > 75)):
                match_type = 'exact_match'
                final_score = max(blended_text_vis, 85.0)
                rank_weight = final_score + 100.0
            elif blended_text_vis >= 60.0:
                match_type = 'similar_alternative'
                final_score = blended_text_vis
                rank_weight = final_score
            else:
                match_type = 'no_match'
                final_score = blended_text_vis
                rank_weight = final_score
            result = {
                'match_score': round(float(final_score), 2),
                'match_type': match_type,
                'is_compatible': True,
                'reasons': reasons,
                'mismatches': mismatches,
                'rank_weight': round(float(rank_weight), 2)
            }
        # Return a tuple for backward‑compatible test usage, but also keep dict for callers that expect it.
        # The tuple contains (score, reasons, compatible).
        # Callers that need the full dict can access it via the third element if they pass a flag, but for now we expose both.
        return MatchResult(result)

    @staticmethod
    def normalize_spec(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower().replace(" ", "").replace("-", "").replace("_", "")

    @classmethod
    def compute_visual_similarity(cls, vec1: Optional[np.ndarray], vec2: Optional[np.ndarray]) -> float:
        """Computes cosine similarity between two 512-dim visual embeddings."""
        if vec1 is None or vec2 is None or len(vec1) == 0 or len(vec2) == 0:
            return 0.0
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 > 0 and norm2 > 0:
            return float(np.clip(dot / (norm1 * norm2), 0.0, 1.0))
        return 0.0

    @classmethod
    def match_products(
        cls,
        target_product: Dict[str, Any],
        candidate: Dict[str, Any],
        target_embedding: Optional[np.ndarray] = None,
        candidate_embedding: Optional[np.ndarray] = None
    ) -> MatchResult:
        """
        Comprehensive matching engine combining RapidFuzz text similarity,
        exact attribute checks (brand, model_number, RAM, storage, colour, size, material, variant),
        and optional visual embedding similarity.

        Returns:
            match_score: float (0.0 - 100.0)
            match_type: 'exact_match' | 'similar_alternative' | 'no_match'
            is_compatible: bool
            reasons: List[str]
            mismatches: List[str]
        """
        reasons = []
        mismatches = []
        is_exact = True
        is_compatible = True

        # 1. Model Number (Strictest key if present in both)
        t_model_no = cls.normalize_spec(target_product.get('model_number', ''))
        c_model_no = cls.normalize_spec(candidate.get('model_number', ''))
        if t_model_no and c_model_no:
            if t_model_no == c_model_no:
                reasons.append(f"Exact match on model number: {target_product.get('model_number')}")
            else:
                mismatch_desc = f"Model number mismatch: '{target_product.get('model_number')}' vs '{candidate.get('model_number')}'"
                mismatches.append(mismatch_desc)
                reasons.append(mismatch_desc)
                is_exact = False
                is_compatible = False

        # 2. Strict Spec checks across all categories: RAM, Storage, Colour, Variant, Size, Material
        strict_specs = [
            ('ram', 'RAM'),
            ('storage', 'Storage'),
            ('colour', 'Colour'),
            ('variant', 'Variant'),
            ('size', 'Size'),
            ('material', 'Material'),
        ]

        for key, label in strict_specs:
            t_val = cls.normalize_spec(target_product.get(key, ''))
            c_val = cls.normalize_spec(candidate.get(key, ''))
            if t_val and c_val:
                if t_val == c_val:
                    reasons.append(f"Exact match on {label}: {target_product.get(key)}")
                else:
                    mismatch_desc = f"{label} mismatch: '{target_product.get(key)}' vs '{candidate.get(key)}'"
                    mismatches.append(mismatch_desc)
                    reasons.append(mismatch_desc)
                    is_exact = False
                    is_compatible = False

        # 3. Brand comparison
        t_brand = cls.normalize_spec(target_product.get('brand', ''))
        c_brand = cls.normalize_spec(candidate.get('brand', ''))
        if t_brand and c_brand:
            if t_brand == c_brand:
                reasons.append(f"Exact match on Brand: {target_product.get('brand')}")
            else:
                mismatch_desc = f"Brand mismatch: '{target_product.get('brand')}' vs '{candidate.get('brand')}'"
                mismatches.append(mismatch_desc)
                reasons.append(mismatch_desc)
                is_exact = False
                is_compatible = False

        # 4. Category matching
        t_cat = cls.normalize_spec(target_product.get('category', ''))
        c_cat = cls.normalize_spec(candidate.get('category', ''))
        if t_cat and c_cat:
            if t_cat == c_cat:
                reasons.append(f"Category matched: {target_product.get('category')}")
            else:
                mismatches.append(f"Category differs: '{target_product.get('category')}' vs '{candidate.get('category')}'")

        # 5. RapidFuzz Text Similarity (Token Sort Ratio & Partial Ratio)
        t_name = str(target_product.get('name', ''))
        c_name = str(candidate.get('name', ''))
        token_sort = fuzz.token_sort_ratio(t_name, c_name)
        partial_ratio = fuzz.partial_ratio(t_name, c_name)
        text_score = (token_sort * 0.7) + (partial_ratio * 0.3)
        reasons.append(f"Text similarity score: {round(text_score, 1)}%")

        # 6. Visual Similarity (if embeddings available)
        visual_score = 0.0
        if target_embedding is not None and candidate_embedding is not None:
            visual_sim = cls.compute_visual_similarity(target_embedding, candidate_embedding)
            visual_score = visual_sim * 100.0
            reasons.append(f"Visual embedding similarity: {round(visual_score, 1)}%")
            blended_text_vis = (text_score * 0.7) + (visual_score * 0.3)
        else:
            blended_text_vis = text_score

        # 7. Final Scoring & Match Type Categorization
        if not is_compatible:
            # When variant / spec mismatch occurs, score is capped strictly at 0-25
            final_score = min(blended_text_vis * 0.25, 25.0)
            reasons.append("Different variant or model specification detected: Products cannot be merged.")
            match_type = 'similar_alternative' if blended_text_vis > 50 else 'no_match'
            return MatchResult({
                'match_score': round(final_score, 2),
                'match_type': match_type,
                'is_compatible': False,
                'reasons': reasons,
                'mismatches': mismatches,
                'rank_weight': final_score # Similar alternatives have lower rank weight
            })

        # Compatible products
        if is_exact and (t_model_no or (t_brand and text_score > 75)):
            match_type = 'exact_match'
            final_score = max(blended_text_vis, 85.0)
            rank_weight = final_score + 100.0 # Exact matches ranked ahead of alternatives
        elif blended_text_vis >= 60.0:
            match_type = 'similar_alternative'
            final_score = blended_text_vis
            rank_weight = final_score
        else:
            match_type = 'no_match'
            final_score = blended_text_vis
            rank_weight = final_score

        return MatchResult({
                'match_score': round(float(final_score), 2),
                'match_type': match_type,
                'is_compatible': True,
                'reasons': reasons,
                'mismatches': mismatches,
                'rank_weight': round(float(rank_weight), 2)
            })
