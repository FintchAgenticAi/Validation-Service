# validation_rules/rules/business/VR_012_numeric_type.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class NumericTypeCheck(BaseValidationRule):
    """
    Checks that columns can be parsed as numeric.
    Detects: "$11.49B", "18.09 %", "FY 1993"
    """
    
    RULE_CODE = "VR_012"
    RULE_NAME = "Numeric Type Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        target_columns = params.get("target_columns", [])
        
        if not target_columns:
            raise ValueError("'target_columns' parameter is required")
        
        invalid_mask = pd.Series([False] * len(df), index=df.index)
        for col in target_columns:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
            numeric = pd.to_numeric(df[col], errors="coerce")
            invalid_mask = invalid_mask | numeric.isna()
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "target_columns": target_columns,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }