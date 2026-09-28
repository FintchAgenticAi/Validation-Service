# validation_rules/rules/business/VR_009_earnings_revenue.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class EarningsRevenueCheck(BaseValidationRule):
    """
    Validates Earnings ≤ Revenue.
    Detects: Year 2021
    """
    
    RULE_CODE = "VR_009"
    RULE_NAME = "Earnings vs Revenue Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        earnings_column = params.get("earnings_column", "Earnings ($B)")
        revenue_column = params.get("revenue_column", "Revenue ($B)")
        tolerance = params.get("tolerance", 0)
        
        for col in [earnings_column, revenue_column]:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
        
        earnings = pd.to_numeric(df[earnings_column], errors="coerce")
        revenue = pd.to_numeric(df[revenue_column], errors="coerce")
        
        invalid_mask = earnings > (revenue + tolerance)
        invalid_mask = invalid_mask | earnings.isna() | revenue.isna()
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "earnings_column": earnings_column,
            "revenue_column": revenue_column,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }