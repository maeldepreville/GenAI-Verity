import streamlit as st
import pandas as pd
from src.prompts import Framework

def render_sidebar():
    """Renders the configuration sidebar and file uploader."""
    with st.sidebar:
        st.title("🛡️ Verity")
        st.caption("AI Compliance Audit Center")
        st.markdown("---")

        # 1. Framework Selection
        framework_options = {
            "ISO 27001:2022": Framework.ISO27001,
            "GDPR": Framework.GDPR
        }
        selected_key = st.selectbox("Regulation Framework", list(framework_options.keys()))
        framework = framework_options[selected_key]

        # 2. Mode Selection
        mode = st.radio(
            "Audit Intensity",
            ["Standard", "Deep Analysis"],
            captions=["Faster, standard checks", "Includes self-correction loop"]
        )

        st.markdown("---")

        # 3. File Upload
        uploaded_file = st.file_uploader("Upload Policy", type=["txt", "pdf"])
        
        return framework, mode, uploaded_file

def render_hero():
    """Renders the empty state 'Welcome' screen."""
    st.markdown("""
    <div style='text-align: center; padding: 60px 20px;'>
        <h1>👋 Welcome to Verity</h1>
        <p style='font-size: 1.1rem; color: #888; max-width: 600px; margin: 0 auto;'>
            Your autonomous compliance agent. Upload a policy document on the left 
            to begin a secure RAG-powered audit against ISO 27001 or GDPR.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_metrics(summary):
    """Renders the top-level KPI cards."""
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{summary.compliance_score:.0f}%</div>
            <div class="metric-label">Compliance Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #e74c3c;">{summary.non_compliant}</div>
            <div class="metric-label">Critical Issues</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #f1c40f;">{summary.partial}</div>
            <div class="metric-label">Partial Matches</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="color: #2ecc71;">{summary.compliant}</div>
            <div class="metric-label">Compliant Areas</div>
        </div>
        """, unsafe_allow_html=True)

def render_findings_table(findings):
    """Renders the detailed findings in an interactive dataframe."""
    st.markdown("### 🔍 Detailed Audit Findings")
    
    # Convert dataclass list to list of dicts for DataFrame
    data = []
    for f in findings:
        data.append({
            "Requirement": f.requirement,
            "Status": f.status.value.upper(),
            "Severity": f.severity.value.upper(),
            "Analysis": f.analysis
        })
    
    df = pd.DataFrame(data)

    # Style function for the Status column
    def color_status(val):
        color_map = {
            'NON_COMPLIANT': 'background-color: rgba(231, 76, 60, 0.2); color: #e74c3c;',
            'PARTIAL': 'background-color: rgba(241, 196, 15, 0.2); color: #f1c40f;',
            'COMPLIANT': 'background-color: rgba(46, 204, 113, 0.2); color: #2ecc71;',
            'INSUFFICIENT_EVIDENCE': 'background-color: rgba(149, 165, 166, 0.2); color: #95a5a6;'
        }
        return color_map.get(val, '')

    st.dataframe(
        df.style.map(color_status, subset=['Status']),
        use_container_width=True,
        column_config={
            "Requirement": st.column_config.TextColumn("Control / Requirement", width="medium"),
            "Analysis": st.column_config.TextColumn("AI Reasoning", width="large"),
        },
        height=400
    )