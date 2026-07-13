import sqlite3
import pandas as pd
import json
import os

class AuditExporter:
    def __init__(self, db_path="data/synapse_audit.db"):
        self.db_path = db_path

    def export_all(self, output_dir="data/exports"):
        os.makedirs(output_dir, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        df_encounters = pd.read_sql_query("SELECT * FROM clinical_encounters", conn)
        df_predictions = pd.read_sql_query("SELECT * FROM model_predictions", conn)
        df_audit = pd.read_sql_query("SELECT * FROM compliance_audit_results", conn)
        conn.close()

        # CSV Exports
        df_encounters.to_csv(f"{output_dir}/encounters.csv", index=False)
        df_predictions.to_csv(f"{output_dir}/predictions.csv", index=False)
        df_audit.to_csv(f"{output_dir}/audit_results.csv", index=False)

        # JSON Exports
        df_audit.to_json(f"{output_dir}/audit_results.json", orient="records", indent=2)

        # Parquet Exports (try pyarrow or fastparquet if available, fallback to CSV/JSON)
        try:
            df_audit.to_parquet(f"{output_dir}/audit_results.parquet", index=False)
            print("Successfully exported Parquet files.")
        except ImportError:
            print("Parquet export skipped: pyarrow or fastparquet not installed.")

        print(f"Exported all datasets to {output_dir}/ successfully.")

if __name__ == "__main__":
    exporter = AuditExporter()
    exporter.export_all()
