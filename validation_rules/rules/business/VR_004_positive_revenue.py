# validation_rules/rules/business/VR_004_positive_revenue.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class PositiveRevenueCheck(BaseValidationRule):
    """
    Validates that Revenue is strictly positive.
    Detects: Year 2011 → Revenue = -27
    """
    
    RULE_CODE = "VR_004"
    RULE_NAME = "Positive Revenue Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        target_column = params.get("target_column", "Revenue ($B)")
        allow_zero = params.get("allow_zero", False)
        
        if target_column not in df.columns:
            raise ValueError(f"Column '{target_column}' not found")
        
        numeric_values = pd.to_numeric(df[target_column], errors="coerce")
        
        if allow_zero:
            invalid_mask = numeric_values < 0
        else:
            invalid_mask = numeric_values <= 0
        
        invalid_mask = invalid_mask | numeric_values.isna()
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "target_column": target_column,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }