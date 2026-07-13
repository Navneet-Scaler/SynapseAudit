-- SynapseAudit PostgreSQL DDL Schema Setup

CREATE TABLE IF NOT EXISTS clinical_encounters (
    record_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    encounter_id VARCHAR(50) NOT NULL,
    specialty VARCHAR(50) NOT NULL,
    note_text TEXT NOT NULL,
    note_section VARCHAR(50) NOT NULL,
    ground_truth_codes TEXT NOT NULL, -- Comma-separated list of ICD-10 and CPT codes
    ground_truth_modifiers TEXT -- Comma-separated list of CPT modifiers
);

CREATE TABLE IF NOT EXISTS model_predictions (
    prediction_id SERIAL PRIMARY KEY,
    record_id VARCHAR(50) REFERENCES clinical_encounters(record_id),
    model_version VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    predicted_codes TEXT NOT NULL, -- Comma-separated list of predicted codes
    predicted_modifiers TEXT, -- Comma-separated list of CPT modifiers
    confidence_scores TEXT, -- Comma-separated list of floats matching predicted_codes
    token_attributions TEXT -- JSON string mapping token spans to predicted codes
);

CREATE TABLE IF NOT EXISTS compliance_audit_results (
    audit_id SERIAL PRIMARY KEY,
    record_id VARCHAR(50) REFERENCES clinical_encounters(record_id),
    model_version VARCHAR(50) NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    error_type VARCHAR(50) NOT NULL, -- e.g., missing_icd10, wrong_modifier, unit_confusion, etc.
    risk_score DOUBLE PRECISION NOT NULL,
    details TEXT
);
