import sys
from src.database import AuditDatabase
from src.dataset_loader import DatasetLoader
from src.regression import RegressionEngine

def run_release_gate():
    print("====================================================")
    print("        SYNAPSEAUDIT: RUNNING RELEASE GATE          ")
    print("====================================================\n")
    
    db = AuditDatabase()
    db.run_compliance_audit()
    
    loader = DatasetLoader()
    regression = RegressionEngine(loader)
    
    comparison = regression.compare_versions()
    
    # Run tests on threshold gates
    # Target: clinical-nlp-v2 vs baseline clinical-nlp-v1
    print("Specialty regression check:")
    passed = True
    for spec, metrics in comparison.items():
        print(f"  - {spec}: v1 F1={metrics['v1_f1']}, v2 F1={metrics['v2_f1']}, Delta={metrics['delta']}")
        if metrics['delta'] < -0.05:
            print(f"    [FAIL] Regression in {spec} exceeds tolerance threshold (> -0.05)!")
            passed = False
            
    # Check compliance rules
    conn = db.db_path
    import sqlite3
    c = sqlite3.connect(conn)
    cursor = c.cursor()
    
    # Check for unit confusion
    cursor.execute("""
        SELECT COUNT(*) FROM compliance_audit_results 
        WHERE model_version = 'clinical-nlp-v2' AND error_type = 'unit_confusion'
    """)
    unit_confusions = cursor.fetchone()[0]
    
    print(f"\nUnit Confusion Count for Candidate: {unit_confusions}")
    if unit_confusions > 0:
        print("  [FAIL] Critical safety failure: Unit confusion rate is not 0%!")
        passed = False
    else:
        print("  [PASS] No unit confusion detected.")
        
    # Check modifier failures
    cursor.execute("""
        SELECT COUNT(*) FROM compliance_audit_results 
        WHERE model_version = 'clinical-nlp-v2' AND error_type = 'wrong_modifier'
    """)
    wrong_modifiers = cursor.fetchone()[0]
    print(f"Modifier Violation Count for Candidate: {wrong_modifiers}")
    if wrong_modifiers > 0:
        print("  [FAIL] Wrong modifier occurrences detected!")
        passed = False
    else:
        print("  [PASS] Modifier rules satisfied.")
        
    c.close()
    
    print("\n====================================================")
    if passed:
        print("        RELEASE GATE SUMMARY: PASSED               ")
        print("====================================================")
        sys.exit(0)
    else:
        print("        RELEASE GATE SUMMARY: FAILED (BLOCKED)     ")
        print("====================================================")
        sys.exit(1)

if __name__ == "__main__":
    run_release_gate()
