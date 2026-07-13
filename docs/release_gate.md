# Release Gate Policy

Before a new clinical NLP model version or prompt variant is approved for staging or production, it must pass the SynapseAudit release gate.

## Gate Criteria & Thresholds

| Metric | Threshold Rule | Action on Failure |
| :--- | :--- | :--- |
| **Exact Match Accuracy** | Must be $\ge$ baseline model (v1) | Block deployment |
| **Modifier Accuracy** | Must not drop by $> 1\%$ | Block deployment |
| **HCC Miss Rate** | Must not increase by $> 0.5\%$ | Block deployment |
| **Unit Confusion Rate** | Must be $0\%$ | Block deployment / Immediate Rollback |
| **Claim Deniability Risk Index** | Must be $\le 0.10$ | Block deployment |
| **Cohen's Kappa ($\kappa$)** | Must be $\ge 0.70$ | Warning / Audit Required |

## Automated Gate Check
The CLI run gate (`src/release_gate.py`) evaluates these rules programmatically. If any blocking criteria fails, the command exits with code `1`, causing CI/CD build failure.
