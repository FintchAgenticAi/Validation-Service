# validation_rules/rules/business/VR_007_net_assets.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class NetAssetsCheck(BaseValidationRule):
    """
    Validates Net Assets ≤ Total Assets.
    Detects: Year 2017
    """
    
    RULE_CODE = "VR_007"
    RULE_NAME = "Net Assets vs Total Assets Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        net_assets_column = params.get("net_assets_column", "Net assets ($B)")
        total_assets_column = params.get("total_assets_column", "Total assets ($B)")
        tolerance = params.get("tolerance", 0)
        
        for col in [net_assets_column, total_assets_column]:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
        
        net_values = pd.to_numeric(df[net_assets_column], errors="coerce")
        total_values = pd.to_numeric(df[total_assets_column], errors="coerce")
        
        invalid_mask = net_values > (total_values + tolerance)
        invalid_mask = invalid_mask | net_values.isna() | total_values.isna()
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "net_assets_column": net_assets_column,
            "total_assets_column": total_assets_column,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }