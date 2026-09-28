# validation_rules/rules/business/VR_002_max_length.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule

class MaxLengthCheck(BaseValidationRule):
    """
    Removes records where the character length of a target column exceeds the max_length parameter.
    """
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        column = params.get("target_column")
        max_len = params.get("max_length", 10)
        
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in dataset for max length check.")
            
        # Calculate character lengths (handling non-string values safely)
        char_lengths = df[column].astype(str).str.len()
        valid_mask = char_lengths <= max_len
        
        passed_df = df[valid_mask].copy()
        failed_df = df[~valid_mask].copy()
        
        metrics = {
            "rule_code": "VR_002_MAX_LENGTH_CHECK",
            "target_column": column,
            "max_allowed_length": max_len,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df)
        }
        
        return passed_df, failed_df, metrics