# Validation Methodology

We perform validation by auditing model predictions against a gold-standard benchmark slice.

## Processing Sequence
1. **Adjudication**: Establish ground truth via dual human-coder agreement.
2. **Text Verification**: Map dosage entities to verify accuracy in matching context.
3. **Statistical Analysis**: Calculate Precision, Recall, F1, and Cohen's Kappa to measure classifier strength.
4. **Deniability Risk Scoring**: Aggregate modifier missing cases and overcoded levels to compute a Claim Deniability Risk Index.
