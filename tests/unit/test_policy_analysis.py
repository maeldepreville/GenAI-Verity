from unittest.mock import MagicMock, patch

from src.agent import (
    ComplianceFinding,
    ComplianceStatus,
    ConfidenceLevel,
    SeverityLevel,
)
from src.policy_analysis import (
    ComplianceSummary,
    analyze_policy,
    compute_compliance_score,
    split_policy,
)
from src.prompts import Framework, ReasoningStrategy

# ---------------------------------------------------------------------
# split_policy
# ---------------------------------------------------------------------


def test_split_policy_filters_short_sections() -> None:
    text = (
        "Too short.\n\n"
        "This is a sufficiently long policy section that should be kept.\n\n"
        "Another short."
    )

    sections = split_policy(text, min_length=30)

    assert len(sections) == 1
    assert "sufficiently long" in sections[0]


# ---------------------------------------------------------------------
# compute_compliance_score
# ---------------------------------------------------------------------


def _finding(status: ComplianceStatus) -> ComplianceFinding:
    return ComplianceFinding(
        requirement="Test requirement",
        status=status,
        analysis="analysis",
        severity=SeverityLevel.LOW,
        sources=[],
        confidence=ConfidenceLevel.HIGH,
        retrieval_notes="notes",
    )


def test_compute_compliance_score_all_compliant() -> None:
    findings = [
        _finding(ComplianceStatus.COMPLIANT),
        _finding(ComplianceStatus.COMPLIANT),
    ]

    score = compute_compliance_score(findings)

    assert score == 100.0


def test_compute_compliance_score_mixed() -> None:
    findings = [
        _finding(ComplianceStatus.COMPLIANT),
        _finding(ComplianceStatus.PARTIAL),
        _finding(ComplianceStatus.NON_COMPLIANT),
    ]

    score = compute_compliance_score(findings)

    # 100 - 10 (partial) - 20 (non-compliant)
    assert score == 70.0


def test_compute_compliance_score_never_negative() -> None:
    findings = [
        _finding(ComplianceStatus.NON_COMPLIANT),
        _finding(ComplianceStatus.NON_COMPLIANT),
        _finding(ComplianceStatus.NON_COMPLIANT),
        _finding(ComplianceStatus.NON_COMPLIANT),
        _finding(ComplianceStatus.NON_COMPLIANT),
    ]

    score = compute_compliance_score(findings)

    assert score == 0.0


# ---------------------------------------------------------------------
# analyze_policy (integration-style unit test)
# ---------------------------------------------------------------------


@patch("src.policy_analysis.time.sleep")
@patch("src.policy_analysis.FAISS")
@patch("src.policy_analysis.GoogleGenerativeAIEmbeddings")
@patch("src.policy_analysis.ComplianceAgent")
@patch("src.policy_analysis.get_requirements")
def test_analyze_policy_happy_path(
    mock_get_requirements: MagicMock,
    mock_agent_cls: MagicMock,
    mock_embeddings: MagicMock,
    mock_faiss: MagicMock,
    mock_sleep: MagicMock,
) -> None:
    # Arrange requirements
    mock_get_requirements.return_value = [
        "Requirement A",
        "Requirement B",
        "Requirement C",
    ]

    # Fake findings returned by agent
    findings: list[ComplianceFinding] = [
        _finding(ComplianceStatus.COMPLIANT),
        _finding(ComplianceStatus.PARTIAL),
        _finding(ComplianceStatus.NON_COMPLIANT),
    ]

    agent_instance = mock_agent_cls.return_value
    agent_instance.analyze.side_effect = findings

    # Fake FAISS local store
    mock_local_store = MagicMock()
    mock_local_store.similarity_search.return_value = [
        MagicMock(page_content="policy section")
    ]
    mock_faiss.from_texts.return_value = mock_local_store

    # Act
    summary = analyze_policy(
        vectorstore=MagicMock(),
        policy_text="Some long policy text.",
        framework=Framework.ISO27001,
        strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
    )

    # Assert summary counts
    assert isinstance(summary, ComplianceSummary)
    assert summary.total_findings == 3
    assert summary.compliant == 1
    assert summary.partial == 1
    assert summary.non_compliant == 1
    assert summary.compliance_score == 70.0

    # Ensure agent called once per requirement
    assert agent_instance.analyze.call_count == 3

    # Ensure sleep was called (but mocked)
    assert mock_sleep.called
