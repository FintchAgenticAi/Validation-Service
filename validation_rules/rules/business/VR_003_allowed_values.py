# validation_rules/rules/business/VR_003_allowed_values.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule

class AllowedValuesCheck(BaseValidationRule):
    """
    Validates that field values belong to an allowed whitelist set (e.g., allowed ISO currencies).
    """
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        column = params.get("target_column")
        allowed_set = params.get("allowed_values", [])
        
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in dataset for allowed values check.")
            
        valid_mask = df[column].isin(allowed_set)
        
        passed_df = df[valid_mask].copy()
        failed_df = df[~valid_mask].copy()
        
        metrics = {
            "rule_code": "VR_003_ALLOWED_ENUM_CHECK",
            "target_column": column,
            "allowed_values": allowed_set,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df)
        }
        
        return passed_df, failed_df, metrics