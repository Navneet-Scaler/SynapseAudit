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
st.set_page_config(page_title="SynapseAudit Clinical QA Workspace", layout="wide", initial_sidebar_state="expanded")

# Dark theme custom stylesheet for premium clinical aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #0d1117;
    }
    .main {
        background: #0d1117;
        color: #c9d1d9;
    }
    h1, h2, h3, h4 {
        color: #58a6ff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    .card-border {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 15px;
    }
    .highlight-span {
        background-color: rgba(56, 139, 253, 0.2);
        border: 1px solid #388bfd;
        border-radius: 4px;
        padding: 2px 6px;
        font-weight: 600;
        cursor: pointer;
        display: inline-block;
        margin: 2px 0;
    }
    .highlight-span:hover {
        background-color: rgba(56, 139, 253, 0.45);
    }
    .kanban-col {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        min-height: 480px;
    }
    .kanban-item {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
        margin-bottom: 12px;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .kanban-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
        border-color: #58a6ff;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header Banner
st.title("SynapseAudit Clinical Workspace")
st.markdown("Offline Quality Assurance Staging Gate & Adjudication Console for Clinical NLP Coding")

# Database initializer
db = AuditDatabase()
db.run_compliance_audit()

loader = DatasetLoader()
regression = RegressionEngine(loader)
encounters = loader.load_encounters()
predictions = loader.load_predictions()

# Initialize dynamic state variables
if "kanban_board" not in st.session_state:
    board = {}
    for idx, row in encounters.iterrows():
        status = "Auditing" if row["record_id"] in ["REC001", "REC002"] else "Pending"
        board[row["record_id"]] = status
    st.session_state["kanban_board"] = board

if "selected_record" not in st.session_state:
    st.session_state["selected_record"] = "REC001"

# Sidebar Navigation Panel
st.sidebar.markdown("### Workspace Console")
page = st.sidebar.radio("Console Navigation", [
    "Staging Regression Overview", 
    "Interactive Review Board",
    "Explainable Audit Ledger", 
    "Prompt Logic Compare",
    "Rule Sandbox Testing Lab",
    "Release Gate Safety Charts"
])

# Utility to trigger record inspection
def inspect_record(rec_id):
    st.session_state["selected_record"] = rec_id

# 1. Staging Regression Overview
if page == "Staging Regression Overview":
    st.header("Staging Regression Overview")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Current Staging Candidate", "clinical-nlp-v2", "Staging")
    col_m2.metric("Active Production Reference", "clinical-nlp-v1", "Stable")
    col_m3.metric("Evaluated Slices", f"{len(encounters)} cases")
    
    st.markdown("---")
    st.subheader("F1 Score Specialty Regression Analysis")
    comparison = regression.compare_versions()
    
    # Plotly Specialty Performance
    specs = list(comparison.keys())
    v1_scores = [comparison[s]["v1_f1"] for s in specs]
    v2_scores = [comparison[s]["v2_f1"] for s in specs]
    
    fig = go.Figure(data=[
        go.Bar(name='Active Reference (v1)', x=specs, y=v1_scores, marker_color='#1f6feb'),
        go.Bar(name='Staging Candidate (v2)', x=specs, y=v2_scores, marker_color='#ff7b72')
    ])
    fig.update_layout(
        barmode='group',
        template="plotly_dark",
        yaxis_title="F1 Score",
        xaxis_title="Clinical Specialty",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Detailed data grid
    st.subheader("Performance Drift Details")
    comparison_df = pd.DataFrame.from_dict(comparison, orient='index')
    st.dataframe(comparison_df.style.highlight_min(subset=["delta"], color="#8b1a1a"))

# 2. Interactive Review Board (Kanban style)
elif page == "Interactive Review Board":
    st.header("Interactive Review Board")
    st.markdown("Auditors manage pipeline queues here. Move cases between columns or click Inspect to view detail.")
    
    board = st.session_state["kanban_board"]
    col_p, col_a, col_ap, col_r = st.columns(4)
    
    stages = {
        "Pending": {"col": col_p, "header_color": "#8b949e", "bg": "rgba(139,148,158,0.15)"},
        "Auditing": {"col": col_a, "header_color": "#58a6ff", "bg": "rgba(88,166,255,0.15)"},
        "Approved": {"col": col_ap, "header_color": "#3fb950", "bg": "rgba(63,185,80,0.15)"},
        "Rejected": {"col": col_r, "header_color": "#f85149", "bg": "rgba(248,81,73,0.15)"}
    }
    
    for s_name, s_info in stages.items():
        with s_info["col"]:
            st.markdown(
                f'<div style="background-color: {s_info["bg"]}; border-bottom: 2px solid {s_info["header_color"]}; padding: 6px; border-radius: 6px 6px 0 0; text-align: center; font-size: 13px; font-weight: bold; color: white;">'
                f'{s_name}'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # Column container
            with st.container():
                recs_in_stage = [r for r, s in board.items() if s == s_name]
                if not recs_in_stage:
                    st.markdown('<div style="text-align: center; padding: 30px; color: #8b949e; font-size: 12px;">No cases</div>', unsafe_allow_html=True)
                
                for r_id in recs_in_stage:
                    row = encounters[encounters["record_id"] == r_id].iloc[0]
                    
                    st.markdown(
                        f'<div class="kanban-item">'
                        f'<div style="display: flex; justify-content: space-between; align-items: center;">'
                        f'<span style="font-weight: bold; color: #58a6ff; font-size: 13px;">{row["record_id"]}</span>'
                        f'<span style="font-size: 10px; background-color: #21262d; padding: 2px 4px; border-radius: 4px; border: 1px solid #30363d; color: #8b949e;">{row["specialty"]}</span>'
                        f'</div>'
                        f'<div style="font-size: 11px; color: #c9d1d9; margin-top: 8px; line-height: 1.4;">'
                        f'{row["note_text"][:85]}...'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Interactivity column button options
                    btn_inspect, btn_move = st.columns([1, 1])
                    with btn_inspect:
                        if st.button("Inspect", key=f"ins_{r_id}", use_container_width=True):
                            inspect_record(r_id)
                            st.toast(f"Selected {r_id} for audit inspection")
                    with btn_move:
                        # Dropdown selector to change column instantly
                        current_idx = list(stages.keys()).index(s_name)
                        options = list(stages.keys())
                        new_stage = st.selectbox(
                            "Stage", 
                            options, 
                            index=current_idx, 
                            key=f"sel_{r_id}",
                            label_visibility="collapsed"
                        )
                        if new_stage != s_name:
                            board[r_id] = new_stage
                            st.session_state["kanban_board"] = board
                            st.rerun()

# 3. Explainable Audit Ledger
elif page == "Explainable Audit Ledger":
    st.header("Explainable Audit Ledger")
    st.write("Select a clinical record to inspect matched billing codes and highlighted source text evidence spans.")
    
    selected_id = st.selectbox("Active Inspection Case", encounters["record_id"].tolist(), index=encounters["record_id"].tolist().index(st.session_state["selected_record"]))
    
    # Save selection back
    st.session_state["selected_record"] = selected_id
    
    record = encounters[encounters["record_id"] == selected_id].iloc[0]
    note_text = record["note_text"]
    
    col_note, col_audit_actions = st.columns([2, 1])
    
    with col_note:
        st.subheader("Highlighted Evidence Spans")
        parser = ClinicalParser()
        spans = parser.parse_note(note_text)
        spans = sorted(spans, key=lambda x: x["start"], reverse=True)
        highlighted = note_text
        for s in spans:
            start, end, code = s["start"], s["end"], s["code"]
            highlighted = (
                highlighted[:start] + 
                f'<span class="highlight-span" title="Clinical Entity matching code: {code}">{highlighted[start:end]} [Code: {code}]</span>' + 
                highlighted[end:]
            )
        st.markdown(f'<div style="background-color: #161b22; border: 1px solid #30363d; padding: 20px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; line-height: 1.6; color: #c9d1d9;">{highlighted}</div>', unsafe_allow_html=True)
        
    with col_audit_actions:
        st.subheader("Adjudication Dashboard")
        
        # State display
        current_status = st.session_state["kanban_board"][selected_id]
        st.markdown(f"**Current Case Workflow State**: `{current_status}`")
        
        # Adjudication controls
        col_app, col_rej = st.columns(2)
        with col_app:
            if st.button("Approve Code Set", key=f"app_{selected_id}", type="primary", use_container_width=True):
                st.session_state["kanban_board"][selected_id] = "Approved"
                st.success("Case Approved!")
                st.rerun()
        with col_rej:
            if st.button("Flag / Reject Set", key=f"rej_{selected_id}", use_container_width=True):
                st.session_state["kanban_board"][selected_id] = "Rejected"
                st.error("Case Flagged for Regression!")
                st.rerun()
                
        st.markdown("---")
        st.markdown("#### Code comparison detail")
        
        c_v1 = predictions[(predictions["record_id"] == selected_id) & (predictions["model_version"] == "clinical-nlp-v1")].iloc[0]
        c_v2 = predictions[(predictions["record_id"] == selected_id) & (predictions["model_version"] == "clinical-nlp-v2")].iloc[0]
        
        st.markdown(f"**Stable Baseline (v1)**: `{c_v1['predicted_codes']}` (Modifiers: `{c_v1['predicted_modifiers'] or 'None'}`)")
        st.markdown(f"**Candidate Release (v2)**: `{c_v2['predicted_codes']}` (Modifiers: `{c_v2['predicted_modifiers'] or 'None'}`)")
        
        conn = sqlite3.connect("data/synapse_audit.db")
        audit_results = pd.read_sql_query(f"SELECT * FROM compliance_audit_results WHERE record_id = '{selected_id}'", conn)
        conn.close()
        
        if not audit_results.empty:
            st.error("Staging Gate Compliance Violations:")
            st.dataframe(audit_results[["error_type", "risk_score", "details"]], hide_index=True)
        else:
            st.success("Case passes all deterministic compliance rules.")

# 4. Prompt Logic Compare
elif page == "Prompt Logic Compare":
    st.header("Prompt Logic Compare")
    st.markdown("Interactive diff display showing changes between baseline (v1) and staging candidate (v2) prompt templates.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("Baseline Prompt Configuration (v1)")
        st.markdown(
            '<div style="background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; font-size: 13px;">'
            'System Prompt: clinical-nlp-v1\n'
            '==============================\n'
            'You are an expert clinical coder. Extract CPT and ICD-10 codes from notes.\n'
            '<span style="background-color: rgba(63,185,80,0.25); border: 1px solid #2ea043; padding: 2px 4px; border-radius: 3px;">CRITICAL: If a procedure (e.g. cardiac cath 93451) and E/M visit (e.g. 99213) occur on same day, ensure modifier 25 is attached to the E/M code (format: 99213:25).</span>'
            '</div>',
            unsafe_allow_html=True
        )
    with col_p2:
        st.subheader("Candidate Prompt Configuration (v2)")
        st.markdown(
            '<div style="background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 6px; font-family: monospace; white-space: pre-wrap; font-size: 13px;">'
            'System Prompt: clinical-nlp-v2\n'
            '==============================\n'
            'You are a clinical assistant. Extract diagnostic codes and CPT codes from notes.\n'
            '<span style="background-color: rgba(248,81,73,0.25); border: 1px solid #f85149; padding: 2px 4px; border-radius: 3px;">Ensure E/M levels are selected correctly. Ensure all details are matched. Do not hallucinate.</span>'
            '</div>',
            unsafe_allow_html=True
        )
        
    st.warning("Staging Review Assessment: Removing the explicit Modifier 25 rule block from System Prompt v2 caused the candidate model to omit necessary modifier markers on joint evaluation claims.")

# 5. Rule Sandbox Testing Lab
elif page == "Rule Sandbox Testing Lab":
    st.header("Rule Sandbox Testing Lab")
    st.markdown("Simulate customized notes dynamically in real-time to audit parser outputs and check rule behaviors.")
    
    note_type = st.selectbox("Quick Note Presets", [
        "Empty Scratchpad",
        "Cardiology (Missing Modifier 25 Evaluation)",
        "Endocrinology (Critical Unit Mismatch Case)"
    ])
    
    text_val = ""
    if note_type == "Cardiology (Missing Modifier 25 Evaluation)":
        text_val = "Patient evaluated for systolic chronic heart failure. Performed cardiac catheterization (93451) and routine cardiovascular evaluation (99213)."
    elif note_type == "Endocrinology (Critical Unit Mismatch Case)":
        text_val = "Patient started on levothyroxine 100 mcg daily for thyroid deficiency."
        
    note_input = st.text_area("Interactive Clinical Note Entry", value=text_val, height=180)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        pred_codes = st.text_input("Simulated Extraction Codes", value="93451,99213")
    with col_c2:
        pred_mods = st.text_input("Simulated Modifiers", value="99213") # missing modifier
        
    if st.button("Execute Verification Rules", type="primary"):
        st.subheader("Highlighted Entities matched")
        parser = ClinicalParser()
        spans = parser.parse_note(note_input)
        spans = sorted(spans, key=lambda x: x["start"], reverse=True)
        highlighted = note_input
        for s in spans:
            start, end, code = s["start"], s["end"], s["code"]
            highlighted = (
                highlighted[:start] + 
                f'<span class="highlight-span">{highlighted[start:end]} [Code: {code}]</span>' + 
                highlighted[end:]
            )
        st.markdown(f'<div style="background-color: #161b22; border: 1px solid #30363d; padding: 18px; border-radius: 6px; font-family: monospace; white-space: pre-wrap;">{highlighted}</div>', unsafe_allow_html=True)
        
        # Test engine rules
        engine = RuleEngine()
        violations = engine.evaluate_rules(pred_codes, pred_mods, note_input)
        
        # levothyroxine custom logic trigger
        if "levothyroxine" in note_input.lower() and "mcg" in note_input.lower() and "mg" in pred_codes.lower():
            violations.append({
                "error_type": "unit_confusion",
                "risk_score": 2.0,
                "details": "Lethal unit confusion: matched 100 mg instead of 100 mcg."
            })
            
        if violations:
            st.error(f"Audit Rules Verification Failure: {len(violations)} rule violations found.")
            st.dataframe(pd.DataFrame(violations), hide_index=True)
        else:
            st.success("Audit Rules Verification Success: Case passes all rules.")

# 6. Release Gate Safety Charts
elif page == "Release Gate Safety Charts":
    st.header("Release Gate Safety Charts")
    st.markdown("Gauge visual charts tracking Candidate release compliance metrics relative to strict staging thresholds.")
    
    conn = sqlite3.connect("data/synapse_audit.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM compliance_audit_results WHERE model_version = 'clinical-nlp-v2' AND error_type = 'unit_confusion'")
    unit_confusions = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM compliance_audit_results WHERE model_version = 'clinical-nlp-v2' AND error_type = 'wrong_modifier'")
    wrong_modifiers = cursor.fetchone()[0]
    conn.close()
    
    # Calculate values
    comparison = regression.compare_versions()
    avg_delta = sum(m["delta"] for m in comparison.values()) / len(comparison) if comparison else 0
    
    col_g1, col_g2, col_g3 = st.columns(3)
    
    # Gauge 1: Global F1 Delta
    with col_g1:
        st.markdown("#### Global F1 Drift Delta")
        fig_g1 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = avg_delta,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Staging Tolerance Limit: -0.05"},
            gauge = {
                'axis': {'range': [-0.2, 0.1]},
                'bar': {'color': "#1f6feb"},
                'steps': [
                    {'range': [-0.2, -0.05], 'color': "rgba(244,67,54,0.25)"},
                    {'range': [-0.05, 0.1], 'color': "rgba(76,175,80,0.25)"}
                ]
            }
        ))
        fig_g1.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#fff"}, height=250)
        st.plotly_chart(fig_g1, use_container_width=True)
        
    # Gauge 2: Modifier Violation Count
    with col_g2:
        st.markdown("#### Modifier Violations")
        fig_g2 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = wrong_modifiers,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Staging Tolerance Limit: 0"},
            gauge = {
                'axis': {'range': [0, 5]},
                'bar': {'color': "#ff7b72"},
                'steps': [
                    {'range': [0, 0.9], 'color': "rgba(76,175,80,0.25)"},
                    {'range': [0.9, 5], 'color': "rgba(244,67,54,0.25)"}
                ]
            }
        ))
        fig_g2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#fff"}, height=250)
        st.plotly_chart(fig_g2, use_container_width=True)
        
    # Gauge 3: Unit Confusion Count
    with col_g3:
        st.markdown("#### Dosage Unit Confusions")
        fig_g3 = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = unit_confusions,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Staging Tolerance Limit: 0"},
            gauge = {
                'axis': {'range': [0, 5]},
                'bar': {'color': "#ff7b72"},
                'steps': [
                    {'range': [0, 0.9], 'color': "rgba(76,175,80,0.25)"},
                    {'range': [0.9, 5], 'color': "rgba(244,67,54,0.25)"}
                ]
            }
        ))
        fig_g3.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "#fff"}, height=250)
        st.plotly_chart(fig_g3, use_container_width=True)

    # Rollback console
    st.markdown("---")
    st.subheader("Staging gate deployment rollbacks")
    
    if st.session_state.get("is_rolled_back", False):
        st.success("System reference is active: clinical-nlp-v1 stable baseline.")
        if st.button("Reset Release Evaluation"):
            st.session_state["is_rolled_back"] = False
            st.rerun()
    else:
        has_failure = (avg_delta < -0.05) or (wrong_modifiers > 0) or (unit_confusions > 0)
        if has_failure:
            st.error("Release Candidate (v2) contains regressions. Deployment is blocked.")
            if st.button("Execute Rollback to stable v1 reference", type="primary"):
                st.session_state["is_rolled_back"] = True
                st.rerun()
        else:
            st.success("Candidate passes all release staging criteria. Approved for deployment.")
