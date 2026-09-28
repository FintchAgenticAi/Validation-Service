# validation_rules/rules/business/VR_006_debt_liabilities.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class DebtLiabilitiesCheck(BaseValidationRule):
    """
    Validates Total Debt ≤ Total Liabilities.
    Detects: Year 2015
    """
    
    RULE_CODE = "VR_006"
    RULE_NAME = "Debt vs Liabilities Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        left_column = params.get("left_column", "Total debt ($B)")
        right_column = params.get("right_column", "Total liabilities ($B)")
        tolerance = params.get("tolerance", 0)
        
        if left_column not in df.columns:
            raise ValueError(f"Column '{left_column}' not found")
        if right_column not in df.columns:
            raise ValueError(f"Column '{right_column}' not found")
        
        left_values = pd.to_numeric(df[left_column], errors="coerce")
        right_values = pd.to_numeric(df[right_column], errors="coerce")
        
        invalid_mask = left_values > (right_values + tolerance)
        invalid_mask = invalid_mask | left_values.isna() | right_values.isna()
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "left_column": left_column,
            "right_column": right_column,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }