# validation_rules/rules/business/VR_013_yoy_variance.py
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class YearOverYearVarianceCheck(BaseValidationRule):
    """
    Checks YoY change does not exceed threshold.
    """
    
    RULE_CODE = "VR_013"
    RULE_NAME = "Year-over-Year Variance Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        target_column = params.get("target_column")
        year_column = params.get("year_column", "Year")
        max_change_pct = params.get("max_change_pct", 0.50)
        
        if target_column not in df.columns:
            raise ValueError(f"Column '{target_column}' not found")
        if year_column not in df.columns:
            raise ValueError(f"Column '{year_column}' not found")
        
        work_df = df.copy()
        work_df["__orig_index"] = work_df.index
        work_df["__value"] = pd.to_numeric(work_df[target_column], errors="coerce")
        work_df["__year"] = pd.to_numeric(
            work_df[year_column].astype(str).str.extract(r"(\d{4})")[0],
            errors="coerce"
        )
        
        work_df = work_df.sort_values("__year").reset_index(drop=True)
        work_df["__prev"] = work_df["__value"].shift(1)
        work_df["__prev_year"] = work_df["__year"].shift(1)
        
        work_df["__pct_change"] = (
            (work_df["__value"] - work_df["__prev"]).abs() /
            work_df["__prev"].abs().replace(0, np.nan)
        )
        
        invalid_mask = (
            work_df["__prev"].notna() &
            (work_df["__year"] - work_df["__prev_year"] == 1) &
            (work_df["__pct_change"] > max_change_pct)
        )
        invalid_mask = invalid_mask | work_df["__value"].isna()
        
        failed_indices = work_df.loc[invalid_mask, "__orig_index"].tolist()
        passed_indices = work_df.loc[~invalid_mask, "__orig_index"].tolist()
        
        passed_df = df.loc[passed_indices].copy()
        failed_df = df.loc[failed_indices].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "target_column": target_column,
            "max_change_pct": max_change_pct,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }