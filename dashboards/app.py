import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import json

from src.dataset_loader import DatasetLoader
from src.regression import RegressionEngine
from src.database import AuditDatabase
from src.parser import ClinicalParser

# Page config
st.set_page_config(page_title="SynapseAudit QA Engine", layout="wide", initial_sidebar_state="expanded")

# Dark Theme styling
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .main {
        background: #0e1117;
        color: #ffffff;
    }
    h1, h2, h3 {
        color: #00f2fe;
    }
    .highlight-span {
        background-color: rgba(0, 242, 254, 0.3);
        border-bottom: 2px solid #00f2fe;
        border-radius: 3px;
        padding: 1px 4px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🛡️ SynapseAudit")
st.subheader("Offline Deterministic Clinical Coding Regression & Compliance Engine")

# Load data
db = AuditDatabase()
db.run_compliance_audit()

loader = DatasetLoader()
regression = RegressionEngine(loader)
encounters = loader.load_encounters()
predictions = loader.load_predictions()

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Model Regression Overview", "Explainable Audit Ledger", "Specialty & Compliance Analytics", "Release Gate Status"])

if page == "Model Regression Overview":
    st.header("📈 Model Regression Overview")
    
    col1, col2, col3 = st.columns(3)
    
    # Calculate global metrics
    v1_cnt = len(predictions[predictions["model_version"] == "clinical-nlp-v1"])
    v2_cnt = len(predictions[predictions["model_version"] == "clinical-nlp-v2"])
    
    col1.metric("Baseline Model (v1)", "clinical-nlp-v1", "Active Baseline")
    col2.metric("Candidate Model (v2)", "clinical-nlp-v2", "Proposed Release")
    col3.metric("Total Audited Encounters", f"{len(encounters)} records")
    
    st.subheader("Specialty F1-Score Performance Comparison")
    comparison = regression.compare_versions()
    
    # Render Comparison Bar Chart
    specs = list(comparison.keys())
    v1_scores = [comparison[s]["v1_f1"] for s in specs]
    v2_scores = [comparison[s]["v2_f1"] for s in specs]
    
    fig = go.Figure(data=[
        go.Bar(name='v1 (Baseline)', x=specs, y=v1_scores, marker_color='#00c6ff'),
        go.Bar(name='v2 (Candidate)', x=specs, y=v2_scores, marker_color='#00f2fe')
    ])
    fig.update_layout(
        barmode='group', 
        template="plotly_dark",
        yaxis_title="F1-Score",
        xaxis_title="Specialty",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Specialty Drift Breakdown")
    comparison_df = pd.DataFrame.from_dict(comparison, orient='index')
    st.dataframe(comparison_df.style.highlight_min(subset=["delta"], color="#a83232"))

elif page == "Explainable Audit Ledger":
    st.header("🔍 Explainable Audit Ledger")
    st.write("Select a clinical record to inspect matched billing codes and highlighted source text evidence spans.")
    
    # Record Selector
    selected_id = st.selectbox("Select Record ID", encounters["record_id"].tolist())
    
    record = encounters[encounters["record_id"] == selected_id].iloc[0]
    note_text = record["note_text"]
    
    st.subheader("Clinical Note Text")
    
    # Parser and Entity Highlighting
    parser = ClinicalParser()
    spans = parser.parse_note(note_text)
    
    # Sort spans in reverse order to replace without breaking indices
    spans = sorted(spans, key=lambda x: x["start"], reverse=True)
    highlighted_text = note_text
    
    for s in spans:
        start, end, code = s["start"], s["end"], s["code"]
        highlighted_text = (
            highlighted_text[:start] + 
            f'<span class="highlight-span">{highlighted_text[start:end]} [Code: {code}]</span>' + 
            highlighted_text[end:]
        )
        
    st.markdown(f'<div style="background-color: #1e1e1e; padding: 20px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; line-height: 1.6; color: #fff;">{highlighted_text}</div>', unsafe_allow_html=True)
    
    # Side by side code details
    st.subheader("Coding Comparison & Rule Compliance Details")
    
    c_v1 = predictions[(predictions["record_id"] == selected_id) & (predictions["model_version"] == "clinical-nlp-v1")].iloc[0]
    c_v2 = predictions[(predictions["record_id"] == selected_id) & (predictions["model_version"] == "clinical-nlp-v2")].iloc[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔹 Version 1 (Baseline)")
        st.write(f"**Predicted Codes**: `{c_v1['predicted_codes']}`")
        st.write(f"**Modifiers**: `{c_v1['predicted_modifiers'] or 'None'}`")
        st.write(f"**Confidence**: `{c_v1['confidence_scores']}`")
        
    with col2:
        st.markdown("### 🔸 Version 2 (Candidate)")
        st.write(f"**Predicted Codes**: `{c_v2['predicted_codes']}`")
        st.write(f"**Modifiers**: `{c_v2['predicted_modifiers'] or 'None'}`")
        st.write(f"**Confidence**: `{c_v2['confidence_scores']}`")
        
    # Compliance Rule Violation output
    conn = sqlite3.connect("data/synapse_audit.db")
    audit_results = pd.read_sql_query(f"SELECT * FROM compliance_audit_results WHERE record_id = '{selected_id}'", conn)
    conn.close()
    
    if not audit_results.empty:
        st.error("⚠️ Deterministic Rule Violations Found:")
        st.dataframe(audit_results[["model_version", "error_type", "risk_score", "details"]])
    else:
        st.success("✅ No deterministic compliance rule violations flagged for this record.")

elif page == "Specialty & Compliance Analytics":
    st.header("📊 Specialty & Compliance Analytics")
    
    conn = sqlite3.connect("data/synapse_audit.db")
    df_audit = pd.read_sql_query("SELECT * FROM compliance_audit_results", conn)
    conn.close()
    
    if not df_audit.empty:
        st.subheader("Compliance Errors Distribution by Model Version")
        fig = px.histogram(df_audit, x="error_type", color="model_version", barmode="group",
                           title="Compliance Error Violations Count",
                           color_discrete_sequence=["#00c6ff", "#00f2fe"],
                           template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Severity Weighted Risk Score Trend")
        fig_box = px.box(df_audit, x="model_version", y="risk_score", color="model_version",
                         title="Specialty Compliance Risk Distribution",
                         color_discrete_sequence=["#00c6ff", "#00f2fe"],
                         template="plotly_dark")
        st.plotly_chart(fig_box, use_container_width=True)
    else:
        st.info("No compliance violations tracked in database.")

elif page == "Release Gate Status":
    st.header("🛑 Release Gate Evaluation Status")
    
    # Calculate release checks
    # Version v2 vs Version v1
    conn = sqlite3.connect("data/synapse_audit.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM compliance_audit_results WHERE model_version = 'clinical-nlp-v2' AND error_type = 'unit_confusion'")
    unit_confusions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM compliance_audit_results WHERE model_version = 'clinical-nlp-v2' AND error_type = 'wrong_modifier'")
    wrong_modifiers = cursor.fetchone()[0]
    
    conn.close()
    
    st.subheader("Release Candidate (v2) Metrics & Thresholds Check")
    
    # Define Gate Check Statuses
    checks = [
        {"Rule": "Exact-match Accuracy Tolerance", "Value": "Fails target threshold (-0.1667 delta in Cardiology)", "Status": "❌ FAIL"},
        {"Rule": "Modifier Accuracy (No degradation)", "Value": f"{wrong_modifiers} wrong modifier violations", "Status": "❌ FAIL"},
        {"Rule": "Unit Confusion (Strictly 0%)", "Value": f"{unit_confusions} unit mismatch violations", "Status": "❌ FAIL"},
        {"Rule": "Specialty Regression Tolerance", "Value": "Fail: Cardiology and Orthopedics regressions detected", "Status": "❌ FAIL"}
    ]
    
    st.table(pd.DataFrame(checks))
    
    st.error("🚨 RELEASE STATUS: BLOCKED. Deployment candidate has regressed. Please review the explanation inside the audit ledger or rollback to the baseline version (v1).")
