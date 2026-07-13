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

-- 3. Unit Mismatch Frequency (Unit Confusion)
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

-- 5. Claim Deniability Risk Index (CDRI)
SELECT
    p.model_version,
    p.prompt_version,
    (COUNT(CASE WHEN c.error_type IN ('wrong_modifier', 'ncci_conflict') THEN 1 END) * 1.5 + 
     COUNT(CASE WHEN c.error_type = 'overcode' THEN 1 END))::NUMERIC / COUNT(DISTINCT e.record_id) AS claim_deniability_risk_index
FROM clinical_encounters e
JOIN model_predictions p ON e.record_id = p.record_id
LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
    AND p.model_version = c.model_version 
    AND p.prompt_version = c.prompt_version
GROUP BY p.model_version, p.prompt_version;

-- 6. Model-to-Model Regression Comparison
SELECT
    v1.record_id,
    v1.predicted_codes AS v1_codes,
    v2.predicted_codes AS v2_codes,
    e.ground_truth_codes
FROM model_predictions v1
JOIN model_predictions v2 ON v1.record_id = v2.record_id AND v1.model_version = 'clinical-nlp-v1' AND v2.model_version = 'clinical-nlp-v2'
JOIN clinical_encounters e ON v1.record_id = e.record_id
WHERE v1.predicted_codes != v2.predicted_codes;
