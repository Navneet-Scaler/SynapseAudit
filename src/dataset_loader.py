import os
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "synapse_audit.db")

class DatasetLoader:
    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = db_path

    def load_encounters(self):
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM clinical_encounters", conn)
        conn.close()
        return df

    def load_predictions(self, model_version=None):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT * FROM model_predictions"
        if model_version:
            query += f" WHERE model_version = '{model_version}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def get_versions(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT model_version, prompt_version FROM model_predictions")
        versions = cursor.fetchall()
        conn.close()
        return [{"model_version": v[0], "prompt_version": v[1]} for v in versions]
