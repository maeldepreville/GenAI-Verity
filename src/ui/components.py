from collections.abc import Callable, Iterable
from typing import Any

import pandas as pd
import streamlit as st

from src.agent import ComplianceFinding
from src.policy_analysis import ComplianceSummary
from src.prompts import Framework


def render_sidebar() -> tuple[Framework, str, Any]:
    """Render the configuration sidebar and file uploader."""
    with st.sidebar:
        st.title("🛡️ Verity")
        st.caption("AI Compliance Audit Center")
        st.markdown("---")

        framework_options = {
            "ISO 27001:2022": Framework.ISO27001,
            "GDPR": Framework.GDPR,
        }

        selected_key = st.selectbox(
            "Regulation Framework",
            list(framework_options.keys()),
        )
        framework = framework_options[selected_key]

        mode = st.radio(
            "Audit Intensity",
            ["Standard", "Deep Analysis"],
            captions=[
                "Faster, standard checks",
                "Includes self-correction loop",
            ],
        )

        st.markdown("---")

        uploaded_file = st.file_uploader(
            "Upload Policy",
            type=["txt", "pdf"],
        )

        return framework, mode, uploaded_file


def render_hero() -> None:
    """Render the empty-state welcome screen."""
    st.markdown(
        """
        <div style='text-align: center; padding: 60px 20px;'>
            <h1>👋 Welcome to Verity</h1>
            <p style='font-size: 1.1rem; color: #888; 
            max-width: 600px; margin: 0 auto;'>
                Your autonomous compliance agent. Upload a policy document on the left
                to begin a secure RAG-powered audit against ISO 27001 or GDPR.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(summary: ComplianceSummary) -> None:
    """Render top-level KPI metric cards."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{summary.compliance_score:.0f}%</div>
                <div class="metric-label">Compliance Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #e74c3c;">
                    {summary.non_compliant}
                </div>
                <div class="metric-label">Critical Issues</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #f1c40f;">
                    {summary.partial}
                </div>
                <div class="metric-label">Partial Matches</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #2ecc71;">
                    {summary.compliant}
                </div>
                <div class="metric-label">Compliant Areas</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_findings_table(findings: Iterable[ComplianceFinding]) -> None:
    """Render detailed audit findings in a dataframe."""
    st.markdown("### 🔍 Detailed Audit Findings")

    data = [
        {
            "Requirement": finding.requirement,
            "Status": finding.status.value.upper(),
            "Severity": finding.severity.value.upper(),
            "Analysis": finding.analysis,
        }
        for finding in findings
    ]

    df = pd.DataFrame(data)

    def color_status(value: Any) -> str | None:
        color_map = {
            "NON_COMPLIANT": (
                "background-color: rgba(231, 76, 60, 0.2); color: #e74c3c;"
            ),
            "PARTIAL": ("background-color: rgba(241, 196, 15, 0.2); color: #f1c40f;"),
            "COMPLIANT": ("background-color: rgba(46, 204, 113, 0.2); color: #2ecc71;"),
            "INSUFFICIENT_EVIDENCE": (
                "background-color: rgba(149, 165, 166, 0.2); color: #95a5a6;"
            ),
        }
        return color_map.get(str(value), None)

    styler_fn: Callable[[Any], str | None] = color_status

    st.dataframe(
        df.style.map(styler_fn, subset=["Status"]),
        use_container_width=True,
        column_config={
            "Requirement": st.column_config.TextColumn(
                "Control / Requirement",
                width="medium",
            ),
            "Analysis": st.column_config.TextColumn(
                "AI Reasoning",
                width="large",
            ),
        },
        height=400,
    )
