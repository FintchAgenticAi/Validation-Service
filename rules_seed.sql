-- =============================================================================
-- VALIDATION RULES SEED — Silver Zone
-- =============================================================================
USE validation_db;

-- =============================================================================
-- 1. CATEGORIES
-- =============================================================================
INSERT IGNORE INTO validation_categories (category_name, description) VALUES
('Completeness', 'Null and missing value checks'),
('Type', 'Data type validation'),
('Range', 'Numeric range and boundary checks'),
('Format', 'Pattern and format validation'),
('Uniqueness', 'Duplicate detection'),
('Relationship', 'Cross-column relationship checks'),
('Equation', 'Mathematical equation validation'),
('Time Series', 'Year-over-year and trend checks');

-- =============================================================================
-- 2. RULES
-- =============================================================================
INSERT INTO validation_rules 
(rule_code, rule_name, description, severity_level, category_id, status, created_by) 
VALUES
('VR_001', 'Null Check', 'Critical columns must not be null', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Completeness'),
 'active', 'system'),

('VR_002', 'Max Length Check', 'String must not exceed max length', 'MEDIUM',
 (SELECT category_id FROM validation_categories WHERE category_name='Format'),
 'active', 'system'),

('VR_003', 'Allowed Values Check', 'Value must be in allowed list', 'MEDIUM',
 (SELECT category_id FROM validation_categories WHERE category_name='Format'),
 'active', 'system'),

('VR_004', 'Positive Revenue Check', 'Revenue must be strictly positive', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Range'),
 'active', 'system'),

('VR_005', 'Range Boundary Check', 'Numeric value within min/max range', 'HIGH',
 (SELECT category_id FROM validation_categories WHERE category_name='Range'),
 'active', 'system'),

('VR_006', 'Debt vs Liabilities Check', 'Total Debt must not exceed Total Liabilities', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Relationship'),
 'active', 'system'),

('VR_007', 'Net Assets vs Total Assets Check', 'Net Assets must not exceed Total Assets', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Relationship'),
 'active', 'system'),

('VR_008', 'Earnings Equation Check', 'Earnings = EPS × Shares Outstanding', 'HIGH',
 (SELECT category_id FROM validation_categories WHERE category_name='Equation'),
 'active', 'system'),

('VR_009', 'Earnings vs Revenue Check', 'Earnings must not exceed Revenue', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Relationship'),
 'active', 'system'),

('VR_010', 'Non-Negative Value Check', 'Value must be >= 0', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Range'),
 'active', 'system'),

('VR_011', 'Null Check (Critical)', 'Critical columns must not be null', 'CRITICAL',
 (SELECT category_id FROM validation_categories WHERE category_name='Completeness'),
 'active', 'system'),

('VR_012', 'Numeric Type Check', 'Columns must contain numeric values', 'HIGH',
 (SELECT category_id FROM validation_categories WHERE category_name='Type'),
 'active', 'system'),

('VR_013', 'Year-over-Year Variance Check', 'YoY change must not exceed threshold', 'HIGH',
 (SELECT category_id FROM validation_categories WHERE category_name='Time Series'),
 'active', 'system');

-- =============================================================================
-- 3. VERSIONS
-- =============================================================================
INSERT INTO validation_rule_versions 
(rule_id, version_no, effective_from, status, created_by)
SELECT rule_id, 'v1.0', NOW(), 'active', 'system'
FROM validation_rules
WHERE rule_code IN ('VR_001','VR_002','VR_003','VR_004','VR_005',
                    'VR_006','VR_007','VR_008','VR_009','VR_010',
                    'VR_011','VR_012','VR_013');

-- =============================================================================
-- 4. METHODS
-- =============================================================================
INSERT INTO validation_rule_methods 
(version_id, method_name, method_path, entry_point)
SELECT v.version_id,
  CASE r.rule_code
    WHEN 'VR_001' THEN 'MandatoryNullCheck'
    WHEN 'VR_002' THEN 'MaxLengthCheck'
    WHEN 'VR_003' THEN 'AllowedValuesCheck'
    WHEN 'VR_004' THEN 'PositiveRevenueCheck'
    WHEN 'VR_005' THEN 'RangeBoundaryCheck'
    WHEN 'VR_006' THEN 'DebtLiabilitiesCheck'
    WHEN 'VR_007' THEN 'NetAssetsCheck'
    WHEN 'VR_008' THEN 'EarningsEquationCheck'
    WHEN 'VR_009' THEN 'EarningsRevenueCheck'
    WHEN 'VR_010' THEN 'NonNegativeCheck'
    WHEN 'VR_011' THEN 'NullCheck'
    WHEN 'VR_012' THEN 'NumericTypeCheck'
    WHEN 'VR_013' THEN 'YearOverYearVarianceCheck'
  END,
  CONCAT('validation_rules.rules.business.',
    CASE r.rule_code
      WHEN 'VR_001' THEN 'VR_001_null_check.MandatoryNullCheck'
      WHEN 'VR_002' THEN 'VR_002_max_length.MaxLengthCheck'
      WHEN 'VR_003' THEN 'VR_003_allowed_values.AllowedValuesCheck'
      WHEN 'VR_004' THEN 'VR_004_positive_revenue.PositiveRevenueCheck'
      WHEN 'VR_005' THEN 'VR_005_range_boundary.RangeBoundaryCheck'
      WHEN 'VR_006' THEN 'VR_006_debt_liabilities.DebtLiabilitiesCheck'
      WHEN 'VR_007' THEN 'VR_007_net_assets.NetAssetsCheck'
      WHEN 'VR_008' THEN 'VR_008_earnings_equation.EarningsEquationCheck'
      WHEN 'VR_009' THEN 'VR_009_earnings_revenue.EarningsRevenueCheck'
      WHEN 'VR_010' THEN 'VR_010_non_negative.NonNegativeCheck'
      WHEN 'VR_011' THEN 'VR_011_null_check.NullCheck'
      WHEN 'VR_012' THEN 'VR_012_numeric_type.NumericTypeCheck'
      WHEN 'VR_013' THEN 'VR_013_yoy_variance.YearOverYearVarianceCheck'
    END),
  'apply'
FROM validation_rules r
JOIN validation_rule_versions v ON v.rule_id = r.rule_id
WHERE r.rule_code IN ('VR_001','VR_002','VR_003','VR_004','VR_005',
                      'VR_006','VR_007','VR_008','VR_009','VR_010',
                      'VR_011','VR_012','VR_013');

-- =============================================================================
-- 5. PARAMETERS
-- =============================================================================

-- Helper macro: for each rule, insert params
-- We'll do this manually per rule using subqueries.

-- VR_001: Null Check
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'mandatory_columns', 'json', 'Y', 
       '["Year","Revenue ($B)","Earnings ($B)"]'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_001';

-- VR_002: Max Length
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_column', 'string', 'Y', 'asset_symbol'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_002';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'max_length', 'int', 'Y', '5'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_002';

-- VR_003: Allowed Values
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_column', 'string', 'Y', 'currency'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_003';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'allowed_values', 'json', 'Y', '["USD","EUR","GBP"]'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_003';

-- VR_004: Positive Revenue
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_column', 'string', 'Y', 'Revenue ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_004';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'allow_zero', 'bool', 'N', 'false'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_004';

-- VR_005: Range Boundary
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_column', 'string', 'Y', 'Operating Margin (%)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_005';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'min_value', 'float', 'N', '0'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_005';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'max_value', 'float', 'N', '100'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_005';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'inclusive', 'bool', 'N', 'true'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_005';

-- VR_006: Debt vs Liabilities
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'left_column', 'string', 'Y', 'Total debt ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_006';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'right_column', 'string', 'Y', 'Total liabilities ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_006';

-- VR_007: Net Assets
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'net_assets_column', 'string', 'Y', 'Net assets ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_007';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'total_assets_column', 'string', 'Y', 'Total assets ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_007';

-- VR_008: Earnings Equation
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'eps_column', 'string', 'Y', 'EPS ($)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_008';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'shares_column', 'string', 'Y', 'Shares Outstanding (B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_008';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'earnings_column', 'string', 'Y', 'Earnings ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_008';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'tolerance', 'float', 'N', '0.05'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_008';

-- VR_009: Earnings vs Revenue
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'earnings_column', 'string', 'Y', 'Earnings ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_009';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'revenue_column', 'string', 'Y', 'Revenue ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_009';

-- VR_010: Non-Negative
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_column', 'string', 'Y', 'Total debt ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_010';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'allow_zero', 'bool', 'N', 'true'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_010';

-- VR_011: Null Check (Critical)
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'critical_columns', 'json', 'Y',
       '["Year","Revenue ($B)","Earnings ($B)","Market cap ($B)"]'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_011';

-- VR_012: Numeric Type
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_columns', 'json', 'Y',
       '["Revenue ($B)","Earnings ($B)","Market cap ($B)"]'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_012';

-- VR_013: YoY Variance
INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'target_column', 'string', 'Y', 'Revenue ($B)'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_013';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'year_column', 'string', 'N', 'Year'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_013';

INSERT INTO validation_rule_parameters (method_id, param_name, data_type, is_required, default_value)
SELECT m.method_id, 'max_change_pct', 'float', 'N', '0.50'
FROM validation_rule_methods m
JOIN validation_rule_versions v ON v.version_id = m.version_id
JOIN validation_rules r ON r.rule_id = v.rule_id
WHERE r.rule_code = 'VR_013';

-- =============================================================================
-- VERIFY
-- =============================================================================
SELECT 'Rules seeded' AS status;
SELECT rule_id, rule_code, rule_name FROM validation_rules;