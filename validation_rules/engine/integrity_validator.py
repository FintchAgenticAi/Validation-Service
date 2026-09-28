# validation_rules/engine/integrity_validator.py
import importlib
import pandas as pd
from typing import List, Dict, Tuple

class IntegrityValidatorEngine:
    
    def execute_rule_pipeline(self, df: pd.DataFrame, active_rules_config: List[Dict]) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
        """
        Runs incoming dataframe through a chain of configured business rules.
        """
        current_valid_df = df.copy()
        quarantined_records = pd.DataFrame()
        execution_summary_logs = []
        
        for rule_meta in active_rules_config:
            method_path = rule_meta["method_path"]  # e.g., 'validation_rules.rules.business.VR_001_null_check.MandatoryNullCheck'
            params = rule_meta["parameters"]
            
            # Dynamic Class Instantiation
            module_name, class_name = method_path.rsplit(".", 1)
            module = importlib.import_module(module_name)
            rule_class = getattr(module, class_name)
            rule_instance = rule_class()
            
            # Execute Rule Check
            passed_df, failed_df, metrics = rule_instance.apply(current_valid_df, params)
            
            # Aggregate invalid rows into quarantine pool
            if not failed_df.empty:
                failed_df["failed_rule_code"] = metrics["rule_code"]
                quarantined_records = pd.concat([quarantined_records, failed_df], ignore_index=True)
                
            # Keep passed rows for the next rule in the pipeline
            current_valid_df = passed_df
            execution_summary_logs.append(metrics)
            
            # Halt early if zero clean records remain
            if current_valid_df.empty:
                break
                
        return current_valid_df, quarantined_records, execution_summary_logs