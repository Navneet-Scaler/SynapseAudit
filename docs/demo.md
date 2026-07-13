# Demo Walkthrough Guide

Follow these steps to demonstrate the engine to compliance officers or engineering teams:

1. **Start Streamlit Dashboard**:
   ```bash
   streamlit run dashboards/app.py
   ```
2. **Review Regression Metrics**:
   - Show the bar chart demonstrating performance differences between the baseline (`v1`) and candidate (`v2`). Highlight that the Cardiology specialty has dropped in F1-score due to specificity regression.
3. **Show Explainable Highlighted Audit**:
   - Navigate to the **Explainable Audit Ledger** tab.
   - Select record `REC001`. Show the highlighted text highlighting systolic heart failure and the missing modifier 25 error.
4. **Trigger Release Gate Fail**:
   - Run `python3 src/release_gate.py` to show how the gate automatically blocks candidate model v2 from production.
