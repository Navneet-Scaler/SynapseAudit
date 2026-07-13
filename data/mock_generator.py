import os
import json
import sqlite3

MOCK_ENCOUNTERS = [
    {
        "record_id": "REC001",
        "patient_id": "PT101",
        "encounter_id": "ENC201",
        "specialty": "Cardiology",
        "note_text": (
            "CHIEF COMPLAINT:\n"
            "Worsening shortness of breath, orthopnea, and severe bilateral lower extremity edema.\n\n"
            "HISTORY OF PRESENT ILLNESS:\n"
            "The patient is a 67-year-old male with a history of long-standing coronary artery disease, "
            "status-post coronary artery bypass graft (CABG) surgery in 2018, who presents with a three-week "
            "history of progressive dyspnea on exertion. He reports needing to sleep on three pillows "
            "due to orthopnea. On physical exam, there is marked jugular venous distention and 3+ pitting "
            "edema bilaterally up to the mid-calf. This is consistent with an acute exacerbation of chronic "
            "systolic heart failure, NYHA Class III, Stage C. During this admission, a diagnostic cardiac "
            "catheterization was performed to evaluate graft patency, alongside a separate comprehensive "
            "cardiovascular evaluation.\n\n"
            "CURRENT MEDICATIONS:\n"
            "1. Lisinopril 10 mg PO daily for blood pressure control and afterload reduction."
        ),
        "note_section": "Discharge Summary",
        "ground_truth_codes": "I50.23,93451,99213",
        "ground_truth_modifiers": "99213:25",
        "v1_codes": "I50.23,93451,99213",
        "v1_modifiers": "99213:25",
        "v1_conf": "0.95,0.91,0.89",
        "v2_codes": "I50.9,93451,99213",  # Regression: general heart failure instead of chronic systolic
        "v2_modifiers": "99213",        # Regression: Missing modifier 25
        "v2_conf": "0.85,0.92,0.88"
    },
    {
        "record_id": "REC002",
        "patient_id": "PT102",
        "encounter_id": "ENC202",
        "specialty": "Endocrinology",
        "note_text": (
            "REASON FOR VISIT:\n"
            "Routine follow-up evaluation for chronic hypothyroidism and thyroid hormone replacement titration.\n\n"
            "CLINICAL ASSESSMENT:\n"
            "The patient is a 45-year-old female who was diagnosed with primary hypothyroidism six years ago. "
            "She reports some improvement in her global symptoms, though she still complains of occasional "
            "afternoon fatigue, mild cold intolerance, and xerosis. Her latest thyroid-stimulating hormone (TSH) "
            "level was slightly elevated at 5.2 mIU/L, indicating inadequate replacement.\n\n"
            "PLAN & MEDICATION DISPOSITION:\n"
            "We will adjust her thyroid hormone replacement strategy. She will continue taking levothyroxine "
            "at the slightly adjusted dosage of 100 mcg daily. We will repeat her TSH and free T4 levels "
            "in approximately six to eight weeks."
        ),
        "note_section": "Consultation",
        "ground_truth_codes": "E03.9",
        "ground_truth_modifiers": "",
        "v1_codes": "E03.9",
        "v1_modifiers": "",
        "v1_conf": "0.98",
        "v2_codes": "E03.9",
        "v2_modifiers": "",
        "v2_conf": "0.97",
    },
    {
        "record_id": "REC003",
        "patient_id": "PT103",
        "encounter_id": "ENC203",
        "specialty": "Orthopedics",
        "note_text": (
            "POSTOPERATIVE CLINICAL PROGRESS NOTE:\n"
            "The patient is a 54-year-old male who is currently six weeks status-post left knee arthroscopy "
            "with partial medial meniscectomy for a chronic meniscus tear. Overall, he is progressing well. "
            "Active range of motion is 0 to 115 degrees with mild discomfort at terminal flexion. "
            "He will proceed with structured physical therapy and active rehabilitation exercises twice a week.\n\n"
            "COMORBIDITIES MANAGEMENT:\n"
            "The patient's co-existing diabetic mellitus type 2 remains stable. He reports compliance with "
            "his oral hypoglycemic agents and denies any neuropathic symptoms or visual changes."
        ),
        "note_section": "Progress Note",
        "ground_truth_codes": "M23.22,E11.9",
        "ground_truth_modifiers": "",
        "v1_codes": "M23.22,E11.9",
        "v1_modifiers": "",
        "v1_conf": "0.94,0.90",
        "v2_codes": "M23.22",  # Regression: missed HCC code (E11.9)
        "v2_modifiers": "",
        "v2_conf": "0.95"
    },
    {
        "record_id": "REC004",
        "patient_id": "PT104",
        "encounter_id": "ENC204",
        "specialty": "Cardiology",
        "note_text": (
            "ADMISSION NOTE:\n"
            "The patient is an 81-year-old female admitted with a two-day history of worsening orthopnea and paroxysmal "
            "nocturnal dyspnea. Echocardiogram reveals an ejection fraction of 55% with marked diastolic dysfunction, "
            "consistent with an acute exacerbation of chronic diastolic heart failure. An intravenous infusion of "
            "furosemide was initiated to promote diuresis.\n\n"
            "DISCHARGE MEDICATION REGIMEN:\n"
            "1. Lisinopril 20 mg PO daily for hypertensive and cardiac remodeling management."
        ),
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
        "note_text": (
            "REHABILITATION SESSION SUMMARY:\n"
            "The patient attended a scheduled physical therapy evaluation today to address range of motion limitations "
            "following left hip arthroplasty. A series of therapeutic exercises were initiated. Unfortunately, "
            "due to a billing database duplication error, duplicate codes 97110 and 97110 were registered for the "
            "same physical therapy session."
        ),
        "note_section": "Progress Note",
        "ground_truth_codes": "97110",
        "ground_truth_modifiers": "",
        "v1_codes": "97110",
        "v1_modifiers": "",
        "v1_conf": "0.96",
        "v2_codes": "97110,97110",  # Regression: Duplicate codes
        "v2_modifiers": "",
        "v2_conf": "0.95,0.85"
    },
    {
        "record_id": "REC006",
        "patient_id": "PT106",
        "encounter_id": "ENC206",
        "specialty": "Gastroenterology",
        "note_text": (
            "PROCEDURE REPORT:\n"
            "The patient underwent a scheduled diagnostic colonoscopy today to investigate a history of lower "
            "abdominal discomfort. The scope was advanced successfully to the cecum. A history of mild "
            "gastroesophageal reflux disease (GERD) was also noted during the pre-operative history and physical."
        ),
        "note_section": "Procedure Note",
        "ground_truth_codes": "45378,K21.9",
        "ground_truth_modifiers": "",
        "v1_codes": "45378,K21.9",
        "v1_modifiers": "",
        "v1_conf": "0.95,0.92",
        "v2_codes": "45378,K21.9",
        "v2_modifiers": "",
        "v2_conf": "0.94,0.93"
    },
    {
        "record_id": "REC007",
        "patient_id": "PT107",
        "encounter_id": "ENC207",
        "specialty": "Neurology",
        "note_text": (
            "NEUROLOGICAL CONSULTATION:\n"
            "The patient is a 29-year-old female presenting with a history of recurrent, unilateral migraine headaches "
            "associated with photophobia and nausea. Symptoms are partially relieved by sleep. We will initiate a trial "
            "of sumatriptan 50 mg PO at the onset of migraine symptoms."
        ),
        "note_section": "Consultation",
        "ground_truth_codes": "G43.909",
        "ground_truth_modifiers": "",
        "v1_codes": "G43.909",
        "v1_modifiers": "",
        "v1_conf": "0.97",
        "v2_codes": "G43.909",
        "v2_modifiers": "",
        "v2_conf": "0.96"
    },
    {
        "record_id": "REC008",
        "patient_id": "PT108",
        "encounter_id": "ENC208",
        "specialty": "Pulmonology",
        "note_text": (
            "CLINICAL PROGRESS NOTE:\n"
            "The patient is an 64-year-old male with a history of tobacco abuse who is evaluated today for progressive "
            "dyspnea. Pulmonary function tests demonstrate airflow obstruction consistent with chronic obstructive "
            "pulmonary disease (COPD). The patient will be started on an albuterol rescue inhaler as needed."
        ),
        "note_section": "Progress Note",
        "ground_truth_codes": "J44.9",
        "ground_truth_modifiers": "",
        "v1_codes": "J44.9",
        "v1_modifiers": "",
        "v1_conf": "0.94",
        "v2_codes": "J44.9",
        "v2_modifiers": "",
        "v2_conf": "0.95"
    },
    {
        "record_id": "REC009",
        "patient_id": "PT109",
        "encounter_id": "ENC209",
        "specialty": "Nephrology",
        "note_text": (
            "NEPHROLOGY CLINICAL PROGRESS NOTE:\n"
            "The patient is an 72-year-old male with a history of hypertension and vascular disease who is seen for "
            "follow-up of chronic kidney disease, stage 3. Latest metabolic panel shows a stable creatinine level of "
            "1.8 mg/dL with a calculated eGFR of 38 mL/min/1.73m2."
        ),
        "note_section": "Progress Note",
        "ground_truth_codes": "N18.3",
        "ground_truth_modifiers": "",
        "v1_codes": "N18.3",
        "v1_modifiers": "",
        "v1_conf": "0.93",
        "v2_codes": "N18.3",
        "v2_modifiers": "",
        "v2_conf": "0.94"
    },
    {
        "record_id": "REC010",
        "patient_id": "PT110",
        "encounter_id": "ENC210",
        "specialty": "Oncology",
        "note_text": (
            "ONCOLOGY CONSULTATION NOTE:\n"
            "The patient is a 61-year-old female diagnosed with invasive ductal carcinoma of the breast, stage II. "
            "We discussed active adjuvant chemotherapy strategies and scheduled her first cycle for next week."
        ),
        "note_section": "Consultation",
        "ground_truth_codes": "C50.919",
        "ground_truth_modifiers": "",
        "v1_codes": "C50.919",
        "v1_modifiers": "",
        "v1_conf": "0.96",
        "v2_codes": "C50.919",
        "v2_modifiers": "",
        "v2_conf": "0.95"
    }
]

def generate_db(db_path="data/synapse_audit.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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

    cursor.execute("DELETE FROM compliance_audit_results")
    cursor.execute("DELETE FROM model_predictions")
    cursor.execute("DELETE FROM clinical_encounters")

    for r in MOCK_ENCOUNTERS:
        cursor.execute("""
        INSERT INTO clinical_encounters (record_id, patient_id, encounter_id, specialty, note_text, note_section, ground_truth_codes, ground_truth_modifiers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (r["record_id"], r["patient_id"], r["encounter_id"], r["specialty"], r["note_text"], r["note_section"], r["ground_truth_codes"], r["ground_truth_modifiers"]))

        cursor.execute("""
        INSERT INTO model_predictions (record_id, model_version, prompt_version, predicted_codes, predicted_modifiers, confidence_scores, token_attributions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r["record_id"], "clinical-nlp-v1", "baseline_prompt", r["v1_codes"], r["v1_modifiers"], r["v1_conf"], "{}"))

        cursor.execute("""
        INSERT INTO model_predictions (record_id, model_version, prompt_version, predicted_codes, predicted_modifiers, confidence_scores, token_attributions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (r["record_id"], "clinical-nlp-v2", "candidate_prompt", r["v2_codes"], r["v2_modifiers"], r["v2_conf"], "{}"))

    conn.commit()
    conn.close()
    print(f"Mock database populated successfully at {db_path}!")

if __name__ == "__main__":
    generate_db()
