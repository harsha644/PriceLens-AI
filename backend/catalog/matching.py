from rapidfuzz import fuzz
from typing import Dict, Any, Tuple, List

class ProductMatchingService:
    @staticmethod
    def normalize_spec(value: str) -> str:
        if not value:
            return ""
        return str(value).strip().lower().replace(" ", "").replace("-", "")

    @classmethod
    def match_products(cls, target_product: Dict[str, Any], candidate: Dict[str, Any]) -> Tuple[float, List[str], bool]:
        """
        Compare two products using strict spec matching and fuzzy text matching.
        Rule: Exact comparison of model number, storage, RAM, colour, variant.
        Never treat different variants as the same product.
        Returns: (match_score: float, reasons: List[str], is_variant_compatible: bool)
        """
        reasons = []
        is_compatible = True

        # Check model number if present in both
        t_model_no = cls.normalize_spec(target_product.get('model_number', ''))
        c_model_no = cls.normalize_spec(candidate.get('model_number', ''))
        if t_model_no and c_model_no:
            if t_model_no == c_model_no:
                reasons.append(f"Exact match on model number: {target_product.get('model_number')}")
            else:
                reasons.append(f"Model number mismatch: '{target_product.get('model_number')}' vs '{candidate.get('model_number')}'")
                is_compatible = False

        # Strict Spec checks: RAM, Storage, Colour, Variant
        strict_specs = [
            ('ram', 'RAM'),
            ('storage', 'Storage'),
            ('colour', 'Colour'),
            ('variant', 'Variant')
        ]

        for key, label in strict_specs:
            t_val = cls.normalize_spec(target_product.get(key, ''))
            c_val = cls.normalize_spec(candidate.get(key, ''))
            if t_val and c_val:
                if t_val == c_val:
                    reasons.append(f"Exact match on {label}: {target_product.get(key)}")
                else:
                    reasons.append(f"{label} mismatch: '{target_product.get(key)}' vs '{candidate.get(key)}'")
                    is_compatible = False

        # If brand differs, not compatible
        t_brand = cls.normalize_spec(target_product.get('brand', ''))
        c_brand = cls.normalize_spec(candidate.get('brand', ''))
        if t_brand and c_brand and t_brand != c_brand:
            reasons.append(f"Brand mismatch: '{target_product.get('brand')}' vs '{candidate.get('brand')}'")
            is_compatible = False
        elif t_brand and c_brand and t_brand == c_brand:
            reasons.append(f"Exact match on Brand: {target_product.get('brand')}")

        # RapidFuzz text similarity on Title / Name
        t_name = str(target_product.get('name', ''))
        c_name = str(candidate.get('name', ''))
        token_sort_ratio = fuzz.token_sort_ratio(t_name, c_name)
        reasons.append(f"Title similarity score: {round(token_sort_ratio, 1)}%")

        if not is_compatible:
            # When variant / spec mismatch occurs, score is capped strictly at 0-25
            final_score = min(token_sort_ratio * 0.25, 25.0)
            reasons.append("Different variant or model specification detected: Products cannot be merged.")
            return round(final_score, 2), reasons, False

        # If compatible, blend token similarity and exact matches
        final_score = token_sort_ratio
        return round(float(final_score), 2), reasons, True
