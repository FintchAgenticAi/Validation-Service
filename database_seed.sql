USE validation_db;

INSERT INTO validation_categories (category_name, description)
VALUES
    ('Integrity', 'Basic data integrity checks'),
    ('Business', 'Business validation rules')
ON DUPLICATE KEY UPDATE description = VALUES(description);

INSERT INTO validation_rules
    (rule_code, rule_name, description, severity_level, category_id, status, is_system_rule, created_by)
SELECT 'VR_001_NULL_CHECK', 'Mandatory null check', 'Reject records missing mandatory fields', 'HIGH', category_id, 'active', 'Y', 'system'
FROM validation_categories WHERE category_name = 'Integrity'
ON DUPLICATE KEY UPDATE rule_name = VALUES(rule_name), status = 'active';

INSERT INTO validation_rules
    (rule_code, rule_name, description, severity_level, category_id, status, is_system_rule, created_by)
SELECT 'VR_002_MAX_LENGTH_CHECK', 'Maximum length check', 'Reject values exceeding the configured length', 'MEDIUM', category_id, 'active', 'Y', 'system'
FROM validation_categories WHERE category_name = 'Business'
ON DUPLICATE KEY UPDATE rule_name = VALUES(rule_name), status = 'active';

INSERT INTO validation_rules
    (rule_code, rule_name, description, severity_level, category_id, status, is_system_rule, created_by)
SELECT 'VR_003_ALLOWED_ENUM_CHECK', 'Allowed values check', 'Reject values outside the configured whitelist', 'MEDIUM', category_id, 'active', 'Y', 'system'
FROM validation_categories WHERE category_name = 'Business'
ON DUPLICATE KEY UPDATE rule_name = VALUES(rule_name), status = 'active';

INSERT INTO validation_rule_versions
    (rule_id, version_no, effective_from, status, change_log, created_by)
SELECT rule_id, '1.0', NOW(), 'active', 'Initial database-backed rule configuration', 'system'
FROM validation_rules r
WHERE r.rule_code IN ('VR_001_NULL_CHECK', 'VR_002_MAX_LENGTH_CHECK', 'VR_003_ALLOWED_ENUM_CHECK')
  AND NOT EXISTS (
      SELECT 1 FROM validation_rule_versions v
      WHERE v.rule_id = r.rule_id AND v.status = 'active'
  );

INSERT INTO validation_rule_methods (version_id, method_name, method_path, entry_point, description)
SELECT v.version_id, r.rule_code,
       CASE r.rule_code
           WHEN 'VR_001_NULL_CHECK' THEN 'validation_rules.rules.business.VR_001_null_check.MandatoryNullCheck'
           WHEN 'VR_002_MAX_LENGTH_CHECK' THEN 'validation_rules.rules.business.VR_002_max_length.MaxLengthCheck'
           WHEN 'VR_003_ALLOWED_ENUM_CHECK' THEN 'validation_rules.rules.business.VR_003_allowed_values.AllowedValuesCheck'
       END,
       'apply', 'Python implementation for the validation rule'
FROM validation_rules r
JOIN validation_rule_versions v ON v.rule_id = r.rule_id AND v.status = 'active'
WHERE NOT EXISTS (
    SELECT 1 FROM validation_rule_methods m WHERE m.version_id = v.version_id
);

INSERT INTO validation_rule_parameters
    (method_id, param_name, data_type, is_required, default_value, description)
SELECT m.method_id, p.param_name, p.data_type, 'Y', p.default_value, p.description
FROM validation_rule_methods m
JOIN validation_rules r ON r.rule_code = m.method_name
JOIN (
    SELECT 'VR_001_NULL_CHECK' AS rule_code, 'mandatory_columns' AS param_name, 'json' AS data_type,
           '["market_timestamp", "asset_symbol", "price"]' AS default_value, 'Required record columns' AS description
    UNION ALL SELECT 'VR_002_MAX_LENGTH_CHECK', 'target_column', 'string', 'asset_symbol', 'Column to inspect'
    UNION ALL SELECT 'VR_002_MAX_LENGTH_CHECK', 'max_length', 'int', '5', 'Maximum number of characters'
    UNION ALL SELECT 'VR_003_ALLOWED_ENUM_CHECK', 'target_column', 'string', 'currency', 'Column to inspect'
    UNION ALL SELECT 'VR_003_ALLOWED_ENUM_CHECK', 'allowed_values', 'json', '["USD", "EUR", "GBP"]', 'Accepted values'
) p ON p.rule_code = r.rule_code
WHERE NOT EXISTS (
    SELECT 1 FROM validation_rule_parameters existing
    WHERE existing.method_id = m.method_id AND existing.param_name = p.param_name
);