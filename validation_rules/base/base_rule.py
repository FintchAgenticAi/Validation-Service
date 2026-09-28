# validation_rules/base/base_rule.py
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Tuple

class BaseValidationRule(ABC):
    """
    Abstract Base Class for all Business Rule and Integrity Validation Rules.
    """
    
    @abstractmethod
    def apply(self, df: pd.DataFrame, params: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
        """
        Executes validation rule on input DataFrame.
        
        Args:
            df (pd.DataFrame): Ingestion batch dataset.
            params (Dict): Dynamic configuration limits/parameters from DB.
            
        Returns:
            Tuple containing:
            - passed_df (pd.DataFrame): Records meeting the rule criteria.
            - failed_df (pd.DataFrame): Discarded or quarantined records.
            - metrics (Dict): Summary execution statistics.
        """
        pass