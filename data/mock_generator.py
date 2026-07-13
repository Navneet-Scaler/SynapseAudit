import os
import json
import sqlite3

MOCK_ENCOUNTERS = [
    {
        "record_id": "REC001",
        "patient_id": "PT101",
        "encounter_id": "ENC201",
        "specialty": "Cardiology",
        "note_text": "DISCHARGE SUMMARY\nPatient presented with worsening chronic systolic heart failure (NYHA Class III). Underwent diagnostic cardiac catheterization and separate cardiovascular evaluation on the same day.\nMedications: Lisinopril 10 mg daily.",
        "note_section": "Discharge Summary",
        "ground_truth_codes": "I50.23,93451,99213",
        "ground_truth_modifiers": "99213:25",
        "v1_codes": "I50.23,93451,99213",
        "v1_modifiers": "99213:25",
        "v1_conf": "0.95,0.91,0.89",
        "v2_codes": "I50.9,93451,99213",  # Regression: I50.9 (unspecified heart failure) instead of I50.23 (systolic chronic)
        "v2_modifiers": "99213",        # Regression: Missing modifier 25 on E/M code
        "v2_conf": "0.85,0.92,0.88"
    },
    {
        "record_id": "REC002",
        "patient_id": "PT102",
        "encounter_id": "ENC202",
        "specialty": "Endocrinology",
        "note_text": "CONSULTATION NOTE\nHistory of hypothyroidism. Current dosage of levothyroxine is 100 mcg daily.",
        "note_section": "Consultation",
        "ground_truth_codes": "E03.9",
        "ground_truth_modifiers": "",
        "v1_codes": "E03.9",
        "v1_modifiers": "",
        "v1_conf": "0.98",
        "v2_codes": "E03.9",
        "v2_modifiers": "",
        "v2_conf": "0.97",
        # Note: We will dynamically simulate unit mismatch in parser/rules for v2 by checking dosage logic
    },
    {
        "record_id": "REC003",
        "patient_id": "PT103",
        "encounter_id": "ENC203",
        "specialty": "Orthopedics",
        "note_text": "CLINICAL NOTE\nPatient seen for post-operative evaluation of knee arthroscopy. Active rehabilitation recommended. Diabetic mellitus type 2 also documented and managed.",
        "note_section": "Progress Note",
        "ground_truth_codes": "M23.22,E11.9", # HCC Code E11.9
        "ground_truth_modifiers": "",
        "v1_codes": "M23.22,E11.9",
        "v1_modifiers": "",
        "v1_conf": "0.94,0.90",
        "v2_codes": "M23.22", # Regression: missed HCC condition (E11.9)
        "v2_modifiers": "",
        "v2_conf": "0.95"
    },
    {
        "record_id": "REC004",
        "patient_id": "PT104",
        "encounter_id": "ENC204",
        "specialty": "Cardiology",
        "note_text": "DISCHARGE SUMMARY\nAdmitted for acute on chronic diastolic heart failure. Infusion of furosemide initiated. Lisinopril 20 mg daily.",
        "note_section": "Discharge Summary",
        "ground_truth_codes": "I50.33",
        "ground_truth_modifiers": "",
        "v1_codes": "I50.33",
        "v1_modifiers": "",
        "v1_conf": "0.93",
        "v2_codes": "I50.33",
        "v2_modifiers": "",
        "v2_conf": "0.94"
    },
    {
        "record_id": "REC005",
        "patient_id": "PT105",
        "encounter_id": "ENC205",
        "specialty": "Orthopedics",
        "note_text": "CLINICAL NOTE\nPhysical therapy evaluation conducted today. Duplicate codes 97110 and 97110 matched.",
        "note_section": "Progress Note",
        "ground_truth_codes": "97110",
        "ground_truth_modifiers": "",
        "v1_codes": "97110",
        "v1_modifiers": "",
        "v1_conf": "0.96",
        "v2_codes": "97110,97110", # Rule failure: duplicate code matching
        "v2_modifiers": "",
        "v2_conf": "0.95,0.85"
    }
]

def generate_db(db_path="data/synapse_audit.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables (SQLite compatible DDL matching PostgreSQL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinical_encounters (
        record_id TEXT PRIMARY KEY,
        patient_id TEXT NOT NULL,
        encounter_id TEXT NOT NULL,
        specialty TEXT NOT NULL,
        note_text TEXT NOT NULL,
        note_section TEXT NOT NULL,
        ground_truth_codes TEXT NOT NULL,
        ground_truth_modifiers TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_predictions (
        prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT REFERENCES clinical_encounters(record_id),
        model_version TEXT NOT NULL,
        prompt_version TEXT NOT NULL,
        predicted_codes TEXT NOT NULL,
        predicted_modifiers TEXT,
        confidence_scores TEXT,
        token_attributions TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compliance_audit_results (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_id TEXT REFERENCES clinical_encounters(record_id),
        model_version TEXT NOT NULL,
        prompt_version TEXT NOT NULL,
        error_type TEXT NOT NULL,
        risk_score REAL NOT NULL,
        details TEXT
    );
    """)

    # Clear existing data
    cursor.execute("DELETE FROM compliance_audit_results")
    cursor.execute("DELETE FROM model_predictions")
    cursor.execute("DELETE FROM clinical_encounters")

    # Insert mock records
    for r in MOCK_ENCOUNTERS:
        cursor.execute("""
        INSERT INTO clinical_encounters (record_id, patient_id, encounter_id, specialty, note_text, note_section, ground_truth_codes, ground_truth_modifiers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r["record_id"], r["patient_id"], r["encounter_id"], r["specialty"], r["note_text"], r["note_section"], r["ground_truth_codes"], r["ground_truth_modifiers"]))

        # Insert Version 1 (Baseline)
        cursor.execute("""
        INSERT INTO model_predictions (record_id, model_version, prompt_version, predicted_codes, predicted_modifiers, confidence_scores, token_attributions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r["record_id"], "clinical-nlp-v1", "baseline_prompt", r["v1_codes"], r["v1_modifiers"], r["v1_conf"], "{}"))

        # Insert Version 2 (Candidate with regressions)
        cursor.execute("""
        INSERT INTO model_predictions (record_id, model_version, prompt_version, predicted_codes, predicted_modifiers, confidence_scores, token_attributions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r["record_id"], "clinical-nlp-v2", "candidate_prompt", r["v2_codes"], r["v2_modifiers"], r["v2_conf"], "{}"))

    conn.commit()
    conn.close()
    print(f"Mock database populated successfully at {db_path}!")

if __name__ == "__main__":
    generate_db()
