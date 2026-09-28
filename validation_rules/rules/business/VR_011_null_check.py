# validation_rules/rules/business/VR_011_null_check.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class NullCheck(BaseValidationRule):
    """
    Checks that critical columns are not null.
    """
    
    RULE_CODE = "VR_011"
    RULE_NAME = "Null Check (Critical Columns)"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        critical_columns = params.get("critical_columns", [])
        
        if not critical_columns:
            raise ValueError("'critical_columns' parameter is required")
        
        for col in critical_columns:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
        
        # Fail if any critical column is null
        invalid_mask = pd.Series([False] * len(df), index=df.index)
        for col in critical_columns:
            invalid_mask = invalid_mask | df[col].isna()
            # Also treat empty strings as null
            invalid_mask = invalid_mask | (df[col].astype(str).str.strip() == "")
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "critical_columns": critical_columns,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }