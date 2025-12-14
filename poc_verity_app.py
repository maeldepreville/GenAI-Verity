import streamlit as st
import time
import pandas as pd
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Verity | AI Compliance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BACKEND MOCK (Place your Agent logic here) ---
# This class mimics your future RAG/Agent backend.
# Replace the 'process' method with your actual LLM call.
class ComplianceAgent:
    def process(self, file_content, regulation_framework):
        """
        Mocks the CoT and Compliance Check.
        Input: Text content, Regulation Name
        Output: Dictionary with analysis
        """
        # SIMULATE PROCESSING TIME (Remove in production)
        time.sleep(1.5) 
        
        # MOCK RETURN DATA
        return {
            "score": 85,
            "summary": "The policy is largely compliant with ISO 27001 but lacks specific mention of incident reporting timelines.",
            "reasoning_steps": [
                "Analyzing document structure...",
                "Retrieving 'Access Control' regulations...",
                "Comparing Section 4.2 against Control A.9.2...",
                "Identifying gap in reporting latency."
            ],
            "issues": [
                {"severity": "High", "control": "A.16.1", "observation": "Missing 72h reporting deadline."},
                {"severity": "Low", "control": "A.9.4", "observation": "Password complexity not explicitly defined (defaults assumed)."}
            ]
        }

# Initialize Backend
agent = ComplianceAgent()

# --- CUSTOM CSS (The "High-End" Polish) ---
# This hides default elements and styles the app to look like a SaaS product
# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* REMOVED: header visibility: hidden - this was hiding your sidebar toggle */
    /* REMOVED: sidebar background color - this was breaking dark mode */

    /* Card Styling for Results */
    .metric-card {
        background-color: rgba(255, 255, 255, 0.1); /* Transparent for Dark Mode compatibility */
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #64B5F6; /* Lighter blue for dark mode */
    }
    .metric-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.title("🛡️ Verity")
    st.caption("AI Compliance Auditor")
    
    st.markdown("---")
    
    # 1. Configuration
    framework = st.selectbox(
        "Regulation Framework",
        ["ISO 27001:2022", "GDPR", "SOC2 Type II", "HIPAA"]
    )
    
    mode = st.radio(
        "Analysis Mode",
        ["Quick Scan", "Deep Audit (CoT)"],
        captions=["Faster, checks keywords", "Full reasoning & reasoning traces"]
    )
    
    st.markdown("---")
    
    # 2. File Upload
    uploaded_file = st.file_uploader("Upload Policy", type=["pdf", "txt", "docx"])
    
    # Reset Button
    if st.button("Clear Session", type="secondary"):
        st.session_state.messages = []
        st.session_state.analysis_result = None
        st.rerun()

    st.markdown("### About")
    st.info("Verity uses RAG + Chain of Thought to analyze policies against real regulatory controls.")

# --- MAIN INTERFACE ---

# Title Section
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Compliance Audit Center")
    st.markdown(f"Current Framework: **{framework}**")
with col2:
    # Just a visual placeholder for 'User Status'
    st.markdown("<div style='text-align: right; color: gray;'>Logged in as <b>Admin</b></div>", unsafe_allow_html=True)

st.divider()

# 1. HERO SECTION (Only show if no file is uploaded)
if not uploaded_file:
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>🛡️ Welcome to Verity</h1>
        <p style='font-size: 1.2rem; opacity: 0.8;'>AI-Powered Compliance & Regulation Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Move the uploader here to the main column for better visibility
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded_file = st.file_uploader("Upload your policy document (PDF, TXT)", type=["pdf", "txt", "docx"])
        
        st.info("👆 Upload a document to unlock the analysis dashboard.")

# 2. CHAT & ANALYSIS INTERFACE
else:
    # A. Chat History (The "Consultant" Feel)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # B. Trigger Analysis (If file exists but no result yet)
    if st.session_state.analysis_result is None:
        
        # This is where we hook into the backend
        with st.chat_message("assistant"):
            st.markdown(f"I have received **{uploaded_file.name}**. I am now initiating the {mode} protocol.")
            
            # The "Thinking" UI - Highly effective for AI apps
            with st.status("Analyzing document structure...", expanded=True) as status:
                st.write("Extracting text layers...")
                time.sleep(1) # Visual filler
                st.write(f"Retrieving {framework} vector embeddings...")
                time.sleep(0.5) # Visual filler
                
                # CALL YOUR BACKEND HERE
                # ---------------------
                result = agent.process(uploaded_file, framework)
                # ---------------------
                
                # Show the Chain of Thought steps if Deep Audit is on
                if mode == "Deep Audit (CoT)":
                    for step in result["reasoning_steps"]:
                        st.write(f"🧠 {step}")
                        time.sleep(0.2)
                
                status.update(label="Audit Complete", state="complete", expanded=False)
            
            # Save to session state
            st.session_state.analysis_result = result
            st.session_state.messages.append({"role": "assistant", "content": "Analysis complete. See the dashboard below."})
            st.rerun()

    # C. THE RESULTS DASHBOARD (Rendered after analysis)
    if st.session_state.analysis_result:
        res = st.session_state.analysis_result
        
        # High-level Metrics Row
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{res['score']}%</div>
                <div class="metric-label">Compliance Score</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #e67e22;">{len(res['issues'])}</div>
                <div class="metric-label">Risks Detected</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #27ae60;">PASS</div>
                <div class="metric-label">Audit Status</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📋 Executive Summary")
        st.write(res["summary"])

        st.markdown("### 🔍 Detailed Findings")
        
        # Interactive Dataframe for findings
        df = pd.DataFrame(res["issues"])
        
        # Custom coloring for the dataframe
        def highlight_severity(val):
            color = '#ffcccc' if val == 'High' else '#ccffcc'
            return f'background-color: {color}'

        st.dataframe(
            df.style.applymap(highlight_severity, subset=['severity']),
            use_container_width=True,
            column_config={
                "severity": st.column_config.TextColumn("Severity", width="small"),
                "control": "ISO Control",
                "observation": "Observation",
            }
        )

        # "Ask Verity" Section
        st.divider()
        st.markdown("#### 💬 Ask about this report")
        
        if prompt := st.chat_input("Ex: How can we fix the password complexity issue?"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Simulated AI Response
            with st.chat_message("assistant"):
                response = f"Based on **Control {res['issues'][1]['control']}**, you should update the policy to explicitly require a minimum of 12 characters and special symbols."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})