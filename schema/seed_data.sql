-- Seed data for SynapseAudit PostgreSQL schema

INSERT INTO clinical_encounters (record_id, patient_id, encounter_id, specialty, note_text, note_section, ground_truth_codes, ground_truth_modifiers)
VALUES (
    'REC001', 
    'PT101', 
    'ENC201', 
    'Cardiology', 
    'Patient presented with chronic systolic heart failure NYHA Class III. Lisinopril 10 mg daily.', 
    'Discharge Summary', 
    'I50.23,93451,99213', 
    '99213:25'
);

INSERT INTO model_predictions (record_id, model_version, prompt_version, predicted_codes, predicted_modifiers, confidence_scores, token_attributions)
VALUES (
    'REC001', 
    'clinical-nlp-v1', 
    'baseline_prompt', 
    'I50.23,93451,99213', 
    '99213:25', 
    '0.95,0.91,0.89', 
    '{}'
);
