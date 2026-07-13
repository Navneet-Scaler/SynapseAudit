import sqlite3
import pandas as pd
from src.rules import RuleEngine

class AuditDatabase:
    def __init__(self, db_path="data/synapse_audit.db"):
        self.db_path = db_path
        self.rule_engine = RuleEngine()

    def run_compliance_audit(self):
        """
        Runs all deterministic compliance rules on model predictions and populates the compliance_audit_results table.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing compliance results
        cursor.execute("DELETE FROM compliance_audit_results")
        
        # Fetch predictions and notes
        cursor.execute("""
            SELECT p.record_id, p.model_version, p.prompt_version, p.predicted_codes, p.predicted_modifiers, e.note_text 
            FROM model_predictions p
            JOIN clinical_encounters e ON p.record_id = e.record_id
        """)
        predictions = cursor.fetchall()
        
        for record_id, model_version, prompt_version, predicted_codes, predicted_modifiers, note_text in predictions:
            violations = self.rule_engine.evaluate_rules(predicted_codes, predicted_modifiers, note_text)
            
            pass
            
            for v in violations:
                cursor.execute("""
                    INSERT INTO compliance_audit_results (record_id, model_version, prompt_version, error_type, risk_score, details)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (record_id, model_version, prompt_version, v["error_type"], v["risk_score"], v["details"]))
                
        conn.commit()
        conn.close()

    def get_drift_by_specialty(self):
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            p.model_version,
            p.prompt_version,
            e.specialty,
            c.error_type,
            COUNT(c.audit_id) AS error_count,
            COUNT(DISTINCT e.record_id) AS total_records,
            ROUND(CAST(COUNT(c.audit_id) AS REAL) / COUNT(DISTINCT e.record_id), 4) AS error_rate,
            ROUND(AVG(c.risk_score), 4) AS risk_index
        FROM clinical_encounters e
        JOIN model_predictions p ON e.record_id = p.record_id
        LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
            AND p.model_version = c.model_version 
            AND p.prompt_version = c.prompt_version
        GROUP BY p.model_version, p.prompt_version, e.specialty, c.error_type
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_modifier_failure_rate(self):
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            p.model_version,
            COUNT(CASE WHEN c.error_type = 'wrong_modifier' THEN 1 END) AS error_count,
            COUNT(DISTINCT e.record_id) AS total_records
        FROM clinical_encounters e
        JOIN model_predictions p ON e.record_id = p.record_id
        LEFT JOIN compliance_audit_results c ON e.record_id = c.record_id 
            AND p.model_version = c.model_version 
            AND p.prompt_version = c.prompt_version
        GROUP BY p.model_version
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
