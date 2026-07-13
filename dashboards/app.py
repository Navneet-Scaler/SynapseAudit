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
from src.rules import RuleEngine

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
    h1 {
        font-size: 2.2rem !important;
    }
    h2 {
        font-size: 1.6rem !important;
    }
    h3 {
        font-size: 1.25rem !important;
    }
    code {
        font-size: 13px !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    pre {
        white-space: pre-wrap !important;
        word-break: break-word !important;
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
page = st.sidebar.radio("Go to", [
    "Model Regression Overview", 
    "Explainable Audit Ledger", 
    "Specialty & Compliance Analytics", 
    "Model Compare & Prompt Diff",
    "Synthetic Testing Lab",
    "Release Gate Status"
])

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

elif page == "Model Compare & Prompt Diff":
    st.header("🔀 Model Compare & Prompt Diff")
    st.markdown("Inspect structural prompt updates and trace NLP model logic diffs.")
    
    col_diff1, col_diff2 = st.columns(2)
    with col_diff1:
        st.markdown("### 🔹 Baseline System Prompt (v1)")
        st.code(
            "System Prompt: clinical-nlp-v1\n"
            "==============================\n"
            "You are an expert clinical coder. Extract CPT and ICD-10 codes from notes.\n"
            "CRITICAL: If a procedure (e.g. cardiac cath 93451) and E/M visit (e.g. 99213) occur on same day,\n"
            "ensure modifier 25 is attached to the E/M code (format: 99213:25).",
            language="markdown"
        )
    with col_diff2:
        st.markdown("### 🔸 Candidate System Prompt (v2)")
        st.code(
            "System Prompt: clinical-nlp-v2\n"
            "==============================\n"
            "You are a clinical assistant. Extract diagnostic codes and CPT codes from notes.\n"
            "Ensure E/M levels are selected correctly. Ensure all details are matched. Do not hallucinate.",
            language="markdown"
        )
    
    st.info("💡 **Prompt Optimization Review**: The candidate prompt (v2) omitted the explicit rule requiring Modifier 25 attachments for office visits billed alongside procedural evaluations, causing a regression in Cardiology and Orthopedics claim accuracy.")

elif page == "Synthetic Testing Lab":
    st.header("🔬 Synthetic Edge Case Testing Lab")
    st.markdown("Input custom EHR notes to validate NLP extraction and rule check results in real-time.")
    
    template = st.selectbox("Select Sample Note Template", [
        "Select custom text...",
        "Cardiology: Catheterization + E/M on Same Day",
        "Endocrinology: Hypothyroidism Levothyroxine mcg Dosage",
        "Orthopedics: Duplicate PT Code Billing"
    ])
    
    default_text = ""
    if template == "Cardiology: Catheterization + E/M on Same Day":
        default_text = (
            "Patient seen today for worsening systolic heart failure. "
            "Underwent diagnostic cardiac catheterization and separate cardiovascular evaluation. "
            "Codes matched: 93451 and 99213."
        )
    elif template == "Endocrinology: Hypothyroidism Levothyroxine mcg Dosage":
        default_text = (
            "Consultation for thyroid deficiency. Patient started on levothyroxine 100 mcg daily."
        )
    elif template == "Orthopedics: Duplicate PT Code Billing":
        default_text = (
            "Post-op rehabilitation visit. Duplicate physical therapy codes 97110 and 97110 recorded."
        )
        
    custom_note = st.text_area("Clinical Note Text", value=default_text, height=150)
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        pred_codes = st.text_input("Simulated Predicted Codes (comma-separated)", value="93451,99213")
    with col_input2:
        pred_mods = st.text_input("Simulated Predicted Modifiers (e.g. 99213:25)", value="99213")
        
    if st.button("Run Deterministic Audit Checks", type="primary"):
        st.subheader("Analysis & Highlighting Spans")
        
        # Parse entities
        parser = ClinicalParser()
        spans = parser.parse_note(custom_note)
        spans = sorted(spans, key=lambda x: x["start"], reverse=True)
        highlighted = custom_note
        for s in spans:
            start, end, code = s["start"], s["end"], s["code"]
            highlighted = (
                highlighted[:start] + 
                f'<span class="highlight-span">{highlighted[start:end]} [Code: {code}]</span>' + 
                highlighted[end:]
            )
        st.markdown(f'<div style="background-color: #1e1e1e; padding: 20px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; line-height: 1.6; color: #fff;">{highlighted}</div>', unsafe_allow_html=True)
        
        # Run rules
        engine = RuleEngine()
        violations = engine.evaluate_rules(pred_codes, pred_mods, custom_note)
        
        # Check custom levothyroxine dynamic unit confusion logic
        if "levothyroxine" in custom_note.lower() and "mcg" in custom_note.lower() and "mg" in pred_codes.lower():
            violations.append({
                "error_type": "unit_confusion",
                "risk_score": 2.0,
                "details": "Lethal unit confusion: matched 100 mg instead of 100 mcg."
            })
            
        if violations:
            st.error(f"❌ Compliance Audit Failed: {len(violations)} rule violation(s) detected.")
            st.dataframe(pd.DataFrame(violations))
        else:
            st.success("✅ Compliance Audit Passed: No rule violations detected for this note.")

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
    
    if "is_rolled_back" not in st.session_state:
        st.session_state["is_rolled_back"] = False
        
    st.subheader("Release Candidate (v2) Metrics & Thresholds Check")
    
    if st.session_state["is_rolled_back"]:
        st.markdown(
            '<div style="background-color: rgba(76, 175, 80, 0.1); border-left: 5px solid #4caf50; padding: 20px; border-radius: 5px; margin-bottom: 20px;">'
            '<h3 style="color: #4caf50; margin: 0 0 10px 0;">✅ SYSTEM STATUS: ACTIVE (clinical-nlp-v1)</h3>'
            '<p style="color: #ccc; margin: 0;">The proposed candidate version (v2) has been successfully rolled back to baseline in production settings.</p>'
            '</div>', 
            unsafe_allow_html=True
        )
        if st.button("Re-evaluate Release Candidate (v2)", type="secondary"):
            st.session_state["is_rolled_back"] = False
            st.rerun()
    else:
        # Compute dynamic checks based on regression deltas and compliance audit
        comparison = regression.compare_versions()
        
        # 1. Specialty Regression Check
        specialty_regressions = []
        has_specialty_regression = False
        for spec, metrics in comparison.items():
            if metrics['delta'] < -0.05:
                specialty_regressions.append(f"{spec} ({metrics['delta']:.4f})")
                has_specialty_regression = True
        
        spec_val = f"Regressions in {', '.join(specialty_regressions)}" if has_specialty_regression else "All specialty F1 deltas within tolerance (-0.05)"
        spec_status = "❌ FAIL" if has_specialty_regression else "✅ PASS"
        
        # 2. Exact-match Accuracy check
        avg_delta = sum(m["delta"] for m in comparison.values()) / len(comparison) if comparison else 0
        accuracy_val = f"{avg_delta:+.4f} average F1 delta" if avg_delta < 0 else "No F1 degradation"
        accuracy_status = "❌ FAIL" if avg_delta < -0.05 else "✅ PASS"
        
        # 3. Modifier violation check
        modifier_val = f"{wrong_modifiers} wrong modifier violations"
        modifier_status = "❌ FAIL" if wrong_modifiers > 0 else "✅ PASS"
        
        # 4. Unit confusion check
        unit_val = f"{unit_confusions} unit mismatch violations"
        unit_status = "❌ FAIL" if unit_confusions > 0 else "✅ PASS"
        
        checks = [
            {"Rule": "Exact-match Accuracy Tolerance", "Value": accuracy_val, "Status": accuracy_status, "Desc": "Global F1 accuracy drift must not drop below baseline threshold."},
            {"Rule": "Modifier Accuracy (No degradation)", "Value": modifier_val, "Status": modifier_status, "Desc": "CPT modifiers (e.g. modifier 25) must be appended correctly without regressions."},
            {"Rule": "Unit Confusion (Strictly 0%)", "Value": unit_val, "Status": unit_status, "Desc": "Dosage unit confusion (mg vs mcg) must be completely absent."},
            {"Rule": "Specialty Regression Tolerance", "Value": spec_val, "Status": spec_status, "Desc": "Specialty F1-score delta must be within acceptable staging tolerances."}
        ]
        
        # Render cards
        col1, col2 = st.columns(2)
        for i, c in enumerate(checks):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                bg_color = "rgba(244, 67, 54, 0.1)" if "FAIL" in c["Status"] else "rgba(76, 175, 80, 0.1)"
                border_color = "#f44336" if "FAIL" in c["Status"] else "#4caf50"
                text_color = "#f44336" if "FAIL" in c["Status"] else "#4caf50"
                
                st.markdown(
                    f'<div style="background-color: {bg_color}; border: 1px solid {border_color}; padding: 20px; border-radius: 8px; margin-bottom: 15px;">'
                    f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                    f'<h4 style="margin: 0; color: #fff;">{c["Rule"]}</h4>'
                    f'<span style="color: {text_color}; font-weight: bold; padding: 2px 8px; border-radius: 4px; border: 1px solid {border_color};">{c["Status"]}</span>'
                    f'</div>'
                    f'<p style="margin: 10px 0 5px 0; font-size: 14px; color: #aaa;">{c["Desc"]}</p>'
                    f'<code style="color: #fff; background-color: rgba(255,255,255,0.05); padding: 4px 8px; border-radius: 4px;">{c["Value"]}</code>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        has_any_failure = any(c["Status"] == "❌ FAIL" for c in checks)
        st.markdown("---")
        
        if has_any_failure:
            st.markdown(
                '<div style="background-color: rgba(244, 67, 54, 0.1); border-left: 5px solid #f44336; padding: 15px; border-radius: 5px; margin-bottom: 20px;">'
                '<h4 style="color: #f44336; margin: 0 0 5px 0;">🚨 RELEASE STATUS: BLOCKED</h4>'
                '<p style="color: #ccc; margin: 0; font-size: 14px;">The proposed candidate version (v2) has failed one or more critical release gates. Deployment is blocked.</p>'
                '</div>',
                unsafe_allow_html=True
            )
            if st.button("Execute Rollback to Baseline (v1)", type="primary"):
                st.session_state["is_rolled_back"] = True
                st.rerun()
        else:
            st.markdown(
                '<div style="background-color: rgba(76, 175, 80, 0.1); border-left: 5px solid #4caf50; padding: 15px; border-radius: 5px; margin-bottom: 20px;">'
                '<h4 style="color: #4caf50; margin: 0 0 5px 0;">✅ RELEASE STATUS: PASSED</h4>'
                '<p style="color: #ccc; margin: 0; font-size: 14px;">All safety and compliance checks are satisfied. The proposed candidate version (v2) is safe to deploy.</p>'
                '</div>',
                unsafe_allow_html=True
            )
