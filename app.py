import streamlit as st

from src.policy_analysis import analyze_policy
from src.prompts import ReasoningStrategy
from src.retriever import load_vector_store
from src.ui.components import (
    render_findings_table,
    render_hero,
    render_metrics,
    render_sidebar,
)

# Internal Modules
from src.ui.styles import load_css

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Verity | Compliance AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- CACHED RESOURCES ---
@st.cache_resource
def get_vector_store():
    """Load vector store once to prevent reloading on every click."""
    try:
        return load_vector_store()
    except Exception as e:
        st.error(f"Failed to load vector store: {e}")
        return None


# --- MAIN APP LOGIC ---
def main():
    # 1. Load Styles
    load_css()

    # 2. Render Sidebar & Get Inputs
    framework, mode_label, uploaded_file = render_sidebar()

    # Map friendly mode label to ReasoningStrategy
    strategy = (
        ReasoningStrategy.SELF_CORRECTION
        if mode_label == "Deep Analysis"
        else ReasoningStrategy.CHAIN_OF_THOUGHT
    )

    # 3. Header
    st.title("Compliance Audit Center")
    st.markdown(f"Current Framework: **{framework.value}**")
    st.divider()

    # 4. Content Area
    if not uploaded_file:
        render_hero()
    else:
        # File Handling
        st.info(f"📂 Document Loaded: **{uploaded_file.name}**")

        if st.button("🚀 Run Compliance Audit", type="primary"):
            # A. Read File Content (Basic Text Support)
            try:
                # Assuming .txt for simplicity based on your snippets.
                # For PDF, you'd add pypdf logic here.
                policy_text = uploaded_file.getvalue().decode("utf-8")
            except Exception:
                st.error("Error reading file. Please upload a valid UTF-8 text file.")
                return

            # B. Analysis Spinner
            with st.status(
                "🤖 Verity is analyzing compliance...", expanded=True
            ) as status:
                st.write("Initializing Agent...")
                vs = get_vector_store()

                if vs:
                    st.write("Retrieving relevant regulations...")
                    # Perform the actual analysis using your backend
                    summary = analyze_policy(
                        vectorstore=vs,
                        policy_text=policy_text,
                        framework=framework,
                        strategy=strategy,
                    )
                    status.update(
                        label="Audit Complete!", state="complete", expanded=False
                    )

                    # Store result in session state to persist
                    st.session_state["last_audit"] = summary
                else:
                    status.update(label="System Error", state="error")

        # 5. Display Results (if available in session state)
        if "last_audit" in st.session_state:
            summary = st.session_state["last_audit"]

            st.markdown("### 📊 Executive Summary")
            render_metrics(summary)

            st.divider()

            render_findings_table(summary.findings)


if __name__ == "__main__":
    main()
