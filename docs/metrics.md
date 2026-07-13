# Validation Metrics Reference

SynapseAudit evaluates clinical coding using several key metrics:

## 1. Classification Metrics
- **Precision**: How many predicted codes were correct.
- **Recall**: How many actual codes the model found.
- **F1 Score**: Harmonic mean of Precision and Recall.
- **Exact Match (EM)**: Percent of encounters where the predicted set of codes perfectly matches the ground truth set.

## 2. Agreement Statistics
- **Cohen’s Kappa ($\kappa$)**:
  $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
  Used to determine if the model is operating at a level of agreement with gold-standard human coders that exceeds chance.
  - $\kappa > 0.8$: Excellent agreement
  - $0.6 < \kappa \le 0.8$: Substantial agreement
  - $\kappa \le 0.6$: Unacceptable for clinical billing.

## 3. Financial & Compliance Indicators
- **Claim Deniability Risk Index (CDRI)**:
  $$\text{CDRI} = \frac{\text{NCCI Violations} \times 1.5 + \text{Wrong Modifier} \times 1.5 + \text{Overcoded E/M Level}}{\text{Total Encounters}}$$
- **HCC Capture Rate**:
  $$\text{HCC Capture Rate} = \frac{\text{True Positive HCC Codes Extracted}}{\text{Gold Standard HCC Codes}}$$
- **Unit Mismatch Error Rate**: Percentage of matches where dosage units specified in notes do not match the predicted code context.
