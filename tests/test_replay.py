import pytest
import sqlite3
import pandas as pd
from src.database import AuditDatabase
from src.rules import RuleEngine

def test_deterministic_replay():
    # Verify that running rule evaluations returns identical outputs given the same database snapshot
    db = AuditDatabase("data/synapse_audit.db")
    db.run_compliance_audit()
    
    conn = sqlite3.connect("data/synapse_audit.db")
    df1 = pd.read_sql_query("SELECT * FROM compliance_audit_results", conn)
    
    # Re-run compliance audit
    db.run_compliance_audit()
    df2 = pd.read_sql_query("SELECT * FROM compliance_audit_results", conn)
    conn.close()
    
    # Drop audit_id from comparison since it is an auto-incrementing key
    df1 = df1.drop(columns=["audit_id"])
    df2 = df2.drop(columns=["audit_id"])
    
    # Ensure they are identical
    pd.testing.assert_frame_equal(df1, df2)
