# Explainable Audit Ledger

The Explainable Audit Ledger provides human auditors with clinical evidence justifications for model predictions.

## Evidence Span Highlighting
When an NLP model extracts a code, it must output the exact text span that triggered the code. The ledger maps these spans back to the original clinical note:
- **Highlighted Spans**: The characters in `note_text` starting at `start_char` and ending at `end_char`.
- **Mismatch Explanation**: If the model predicts a code but the gold standard differs, the ledger presents the mismatch classification (e.g., `missing_icd10`, `wrong_modifier`, `unit_confusion`).

## Reviewer Actions
Auditors can inspect records in the UI and toggle:
- **Agree/Disagree**: Flags if the auditor agrees with the candidate's prediction.
- **Rejection Reason**: Captures human-in-the-loop qualitative feedback on prompt regressions.
