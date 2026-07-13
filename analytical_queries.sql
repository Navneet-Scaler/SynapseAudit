-- SynapseAudit PostgreSQL Analytical Queries for Clinical Coding Compliance

-- 1. Model Version Drift by Specialty
SELECT 
    p.model_version,
    p.prompt_version,
    e.specialty,
    c.error_type,
    COUNT(c.audit_id) AS error_count,
    COUNT(DISTINCT e.record_id) AS total_records,
    ROUND(COUNT(c.audit_id)::NUMERIC / COUNT(DISTINCT e.record_id), 4) AS error_rate,
    ROUND(AVG(c.risk_score)::NUMERIC, 4) AS risk_index
FROM clinical_encounters e
JOIN model_predictions p ON e.record_id = p.record_id
LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
    AND p.model_version = c.model_version 
    AND p.prompt_version = c.prompt_version
GROUP BY p.model_version, p.prompt_version, e.specialty, c.error_type
ORDER BY e.specialty, error_rate DESC;

-- 2. HCC Miss Rate by Chronic Condition
SELECT
    p.model_version,
    p.prompt_version,
    COUNT(CASE WHEN c.error_type = 'hcc_miss' THEN 1 END) AS error_count,
    COUNT(DISTINCT e.record_id) AS total_records,
    ROUND(COUNT(CASE WHEN c.error_type = 'hcc_miss' THEN 1 END)::NUMERIC / COUNT(DISTINCT e.record_id), 4) AS error_rate
FROM clinical_encounters e
JOIN model_predictions p ON e.record_id = p.record_id
LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
    AND p.model_version = c.model_version 
    AND p.prompt_version = c.prompt_version
GROUP BY p.model_version, p.prompt_version;

-- 3. Unit Confusion Frequency
SELECT
    p.model_version,
    p.prompt_version,
    COUNT(CASE WHEN c.error_type = 'unit_confusion' THEN 1 END) AS error_count,
    COUNT(DISTINCT e.record_id) AS total_records,
    ROUND(COUNT(CASE WHEN c.error_type = 'unit_confusion' THEN 1 END)::NUMERIC / COUNT(DISTINCT e.record_id), 4) AS error_rate
FROM clinical_encounters e
JOIN model_predictions p ON e.record_id = p.record_id
LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
    AND p.model_version = c.model_version 
    AND p.prompt_version = c.prompt_version
GROUP BY p.model_version, p.prompt_version;

-- 4. Modifier Failure Rate
SELECT
    p.model_version,
    p.prompt_version,
    COUNT(CASE WHEN c.error_type = 'wrong_modifier' THEN 1 END) AS error_count,
    COUNT(DISTINCT e.record_id) AS total_records,
    ROUND(COUNT(CASE WHEN c.error_type = 'wrong_modifier' THEN 1 END)::NUMERIC / COUNT(DISTINCT e.record_id), 4) AS error_rate
FROM clinical_encounters e
JOIN model_predictions p ON e.record_id = p.record_id
LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
    AND p.model_version = c.model_version 
    AND p.prompt_version = c.prompt_version
GROUP BY p.model_version, p.prompt_version;
