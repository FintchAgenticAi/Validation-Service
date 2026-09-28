# validation_rules/rules/business/VR_008_earnings_equation.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class EarningsEquationCheck(BaseValidationRule):
    """
    Validates Earnings = EPS × Shares Outstanding.
    Detects: Year 2019
    """
    
    RULE_CODE = "VR_008"
    RULE_NAME = "Earnings Equation Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        eps_column = params.get("eps_column", "EPS ($)")
        shares_column = params.get("shares_column", "Shares Outstanding (B)")
        earnings_column = params.get("earnings_column", "Earnings ($B)")
        tolerance = params.get("tolerance", 0.05)
        
        for col in [eps_column, shares_column, earnings_column]:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found")
        
        eps = pd.to_numeric(df[eps_column], errors="coerce")
        shares = pd.to_numeric(df[shares_column], errors="coerce")
        earnings = pd.to_numeric(df[earnings_column], errors="coerce")
        
        expected = eps * shares
        diff = (earnings - expected).abs()
        rel_diff = diff / expected.abs().replace(0, 1)
        
        invalid_mask = rel_diff > tolerance
        invalid_mask = invalid_mask | eps.isna() | shares.isna() | earnings.isna()
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "formula": "EPS × Shares == Earnings",
            "tolerance": tolerance,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }