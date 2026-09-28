# validation_rules/rules/business/VR_001_null_check.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule

class MandatoryNullCheck(BaseValidationRule):
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        mandatory_cols = params.get("mandatory_columns", [])
        
        # Check which columns actually exist in the dataframe
        cols_to_check = [col for col in mandatory_cols if col in df.columns]
        
        # Row mask where all mandatory columns are non-null
        valid_mask = df[cols_to_check].notna().all(axis=1)
        
        passed_df = df[valid_mask].copy()
        failed_df = df[~valid_mask].copy()
        
        metrics = {
            "rule_code": "VR_001_NULL_CHECK",
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "checked_columns": cols_to_check
        }
        
        return passed_df, failed_df, metrics