# Architecture Design Document

SynapseAudit acts as an offline deterministic validation gate.

## System Block Diagram
```
[Raw Clinical Data] --> [Model Version Inference] 
                              |
                              v
                 [Dataset Loader Engine] 
                              |
                              v
                [Deterministic Rule Validator] 
                              |
                              v
                    [SQL Analytics & Metrics]
                              |
                              v
          +-------------------+-------------------+
          |                                       |
          v                                       v
[Plotly Explanatory Ledger]             [CI/CD Release Gate CLI]
```

## Component Breakdown

1. **Parser Pipeline (`src/parser.py`)**: Uses optimized regex matching rules to locate ICD-10 and CPT concept occurrences.
2. **Rules Engine (`src/rules.py`)**: Validates relationships between codes.
3. **Database Connector (`src/database.py`)**: Interfaces with SQLite locally while using standard ANSI SQL queries.
4. **Interactive Dashboard (`dashboards/app.py`)**: Realizes visual analysis and interactive text highlight mappings.
