# Data Sources

SynapseAudit processes clinical datasets for offline validation:

## 1. MIMIC-IV-Note
- **Discharge Summaries**: Detailed summaries containing admission reasons, hospital courses, discharge diagnoses, and medication dosage details.
- **Radiology Reports**: Imaging descriptions with anatomical findings and procedure details.

## 2. MTSamples
- Specialty transcripts (e.g., Cardiology, Orthopedics, Endocrinology) representing ambulatory encounters and specialty consult notes.

## 3. Synthetic Edge-Cases
- Manually designed scenarios containing tricky billing triggers, such as:
  - Separate E/M and procedure on the same day (Modifier 25 check).
  - Mutually exclusive procedures (NCCI check).
  - Dosages with critical units (e.g., `mg` vs `mcg` for levothyroxine, insulin units).
  - Specific chronic disease indicators that map to CMS HCC risk categories.
