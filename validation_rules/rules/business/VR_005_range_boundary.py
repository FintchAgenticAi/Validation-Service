# validation_rules/rules/business/VR_005_range_boundary.py
import pandas as pd
from typing import Dict, Tuple
from validation_rules.base.base_rule import BaseValidationRule


class RangeBoundaryCheck(BaseValidationRule):
    """
    Validates numeric value within min/max range.
    Detects: Year 2013 → Operating Margin = 125
    """
    
    RULE_CODE = "VR_005"
    RULE_NAME = "Range Boundary Check"
    
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        target_column = params.get("target_column")
        min_value = params.get("min_value")
        max_value = params.get("max_value")
        inclusive = params.get("inclusive", True)
        
        if target_column not in df.columns:
            raise ValueError(f"Column '{target_column}' not found")
        
        numeric_values = pd.to_numeric(df[target_column], errors="coerce")
        
        invalid_mask = numeric_values.isna()
        
        if min_value is not None:
            if inclusive:
                invalid_mask = invalid_mask | (numeric_values < min_value)
            else:
                invalid_mask = invalid_mask | (numeric_values <= min_value)
        
        if max_value is not None:
            if inclusive:
                invalid_mask = invalid_mask | (numeric_values > max_value)
            else:
                invalid_mask = invalid_mask | (numeric_values >= max_value)
        
        passed_df = df[~invalid_mask].copy()
        failed_df = df[invalid_mask].copy()
        
        return passed_df, failed_df, {
            "rule_code": self.RULE_CODE,
            "rule_name": self.RULE_NAME,
            "target_column": target_column,
            "min_value": min_value,
            "max_value": max_value,
            "total_scanned": len(df),
            "passed_count": len(passed_df),
            "failed_count": len(failed_df),
            "status": "success" if len(failed_df) == 0 else "failed"
        }