# Versioning & Snapshot Tracking

SynapseAudit supports side-by-side comparison of different model configurations.

## Schema Entities
Every predicted code runs inside a context consisting of:
- `model_version`: e.g., `gpt-4o-2024-05-13`, `llama-3-70b-instruct`.
- `prompt_version`: e.g., `v1.2_sys_instructions`, `v2.0_few_shot_modifier`.

## Drift Analysis
By tracking predictions across versions, the engine calculates:
- **Specialty Drift**: The percentage difference in error rates for a specific specialty between `v1` and `v2`.
- **Code Frequency Drift**: Detects if a new prompt version causes the system to over-predict specific codes (e.g., billing 99214 instead of 99213).
- **Regression Flags**: Automatically flags if a code that was correctly predicted in `v1` is missed in `v2`.
