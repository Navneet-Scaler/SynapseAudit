# SynapseAudit

**SynapseAudit** is a production-grade, offline, deterministic regression and compliance engine designed for Clinical NLP coding quality assurance. It helps clinical coding QA teams and ML engineers stress-test and audit model outputs (ICD-10, CPT, modifiers, and HCC risk adjustments) against a human-adjudicated gold-standard dataset before releasing new prompts or updated model checkpoints.

## Key Features

- **Clinical Section & Entity Parser**: Token-span parsing mapped to ground truth ICD-10 and CPT codes.
- **Deterministic Rules Engine**: Automated compliance checks for:
  - **Modifier 25 Eligibility**: Catching missing modifier 25 when billing a procedure and E/M on the same day.
  - **HCC Capture Gap**: Flagging missed Hierarchical Condition Categories (e.g., Type 2 Diabetes).
  - **Duplicate Billing Detection**: Identifying duplicated procedure codes.
  - **Unit Mismatch**: Catching dosage unit confusion (e.g., matching `mg` instead of `mcg` for levothyroxine).
- **PostgreSQL Compliance Analytics**: Pre-packaged queries evaluating drift and error rates by specialty.
- **Explainable Audit Ledger**: A Streamlit dashboard utilizing interactive, HTML-based note highlighting to trace code matches to source notes.
- **Release Gates**: An automated CLI release checker that exits with a failure code when accuracy or modifier checks drop below baseline.

---

## Tech Stack & Setup

### Prerequisites
- Python 3.9+
- SQLite (pre-installed; runs standard PostgreSQL-compatible queries)

### Installation
1. Clone the repository and initialize the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install requirements:
   ```bash
   pip install pandas numpy plotly streamlit pytest
   ```

3. Populate the mock database with baseline (`v1`) and candidate (`v2`) clinical records:
   ```bash
   python3 data/mock_generator.py
   ```

---

## Running the Application

### 1. Run Automated Unit Tests
To run compliance rule checks and metric validations:
```bash
PYTHONPATH=. python3 -m pytest tests/
```

### 2. Run the Release Gate Check
Simulate a CI/CD build run to verify if the candidate release candidate (`v2`) meets safety standards:
```bash
PYTHONPATH=. python3 src/release_gate.py
```
*(This will exit with code `1` and block the pipeline because `v2` contains regression errors)*

### 3. Launch the Interactive Dashboard
Launch the Streamlit app to explore the Explainable Audit Ledger and Specialty analytics:
```bash
streamlit run dashboards/app.py
```

---

## Project Structure

```
├── README.md
├── PRD.md
├── Strategic_Pivot_Report.md
├── analytical_queries.sql
├── data/
│   ├── mock_generator.py      # Generates synthetic clinical notes database
│   └── synapse_audit.db       # Local database
├── schema/
│   └── database_setup.sql     # PostgreSQL DDL setup schema
├── src/
│   ├── dataset_loader.py      # Dataset pipeline
│   ├── parser.py              # Clinical NLP parser (text highlighter spans)
│   ├── rules.py               # Deterministic compliance rules
│   ├── metrics.py             # F1, Cohen's Kappa, CDRI
│   ├── regression.py          # Version delta engine
│   ├── database.py            # SQLite analytics interface
│   └── release_gate.py        # CLI release validator
├── dashboards/
│   └── app.py                 # Streamlit UI
└── tests/
    ├── test_rules.py          # Rules unit tests
    └── test_regression.py     # Metrics unit tests
```
