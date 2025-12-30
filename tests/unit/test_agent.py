from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.agent import (
    ComplianceAgent,
    ComplianceFinding,
    ComplianceStatus,
    ConfidenceLevel,
    SeverityLevel,
)
from src.prompts import Framework, ReasoningStrategy


class DummyDocument:
    """Minimal stand-in for LangChain Document."""

    def __init__(self, text: str, source: str = "test-source") -> None:
        self.page_content = text
        self.metadata = {"source": source}


@pytest.fixture()
def agent() -> ComplianceAgent:  # type: ignore
    with patch("src.agent.GeminiClient") as mock_gemini:
        mock_instance = mock_gemini.return_value
        mock_instance.complete.return_value = "Default compliant response"
        yield ComplianceAgent(strategy=ReasoningStrategy.CHAIN_OF_THOUGHT)


# ---------------------------------------------------------------------
# Pure logic tests
# ---------------------------------------------------------------------


def test_infer_status_compliant(agent: ComplianceAgent) -> None:
    status = agent._infer_status("The policy is compliant.")
    assert status is ComplianceStatus.COMPLIANT


def test_infer_status_non_compliant(agent: ComplianceAgent) -> None:
    status = agent._infer_status("This control is non-compliant.")
    assert status is ComplianceStatus.NON_COMPLIANT


def test_infer_status_insufficient(agent: ComplianceAgent) -> None:
    status = agent._infer_status("Insufficient evidence available.")
    assert status is ComplianceStatus.INSUFFICIENT_EVIDENCE


def test_infer_severity_mapping(agent: ComplianceAgent) -> None:
    assert agent._infer_severity(ComplianceStatus.NON_COMPLIANT) is SeverityLevel.HIGH
    assert agent._infer_severity(ComplianceStatus.PARTIAL) is SeverityLevel.MEDIUM
    assert agent._infer_severity(ComplianceStatus.COMPLIANT) is SeverityLevel.LOW


# ---------------------------------------------------------------------
# Retrieval quality tests
# ---------------------------------------------------------------------


def test_assess_retrieval_quality_empty(agent: ComplianceAgent) -> None:
    confidence, notes, sufficient = agent._assess_retrieval_quality([], [])
    assert confidence is ConfidenceLevel.LOW
    assert not sufficient
    assert "No chunks" in notes


def test_assess_retrieval_quality_good(agent: ComplianceAgent) -> None:
    docs = [
        DummyDocument("Relevant text."),
        DummyDocument("More text."),
        DummyDocument("Even more."),
    ]
    scores = [0.9, 0.7, 0.4]

    confidence, _, sufficient = agent._assess_retrieval_quality(docs, scores)

    assert sufficient
    assert confidence is ConfidenceLevel.HIGH


# ---------------------------------------------------------------------
# analyze() tests with mocks
# ---------------------------------------------------------------------


@patch("src.agent.retrieve_with_scores")
def test_analyze_insufficient_evidence(
    mock_retrieve: MagicMock,
    agent: ComplianceAgent,
) -> None:
    mock_retrieve.return_value = []

    result = agent.analyze(
        vectorstore=MagicMock(),
        requirement="Access control",
        policy_excerpt="",
        framework=Framework.ISO27001,
    )

    assert isinstance(result, ComplianceFinding)
    assert result.status is ComplianceStatus.INSUFFICIENT_EVIDENCE
    assert result.severity is SeverityLevel.LOW


@patch("src.agent.retrieve_with_scores")
def test_analyze_compliant_path(
    mock_retrieve: MagicMock,
    agent: ComplianceAgent,
) -> None:
    docs: list[tuple[Any, float]] = [
        (DummyDocument("ISO requires access control."), 0.9),
        (DummyDocument("Policy describes access control."), 0.8),
        (DummyDocument("Roles defined."), 0.6),
    ]
    mock_retrieve.return_value = docs

    agent.llm.complete.return_value = "The policy is compliant."

    result = agent.analyze(
        vectorstore=MagicMock(),
        requirement="Access control",
        policy_excerpt="RBAC is enforced.",
        framework=Framework.ISO27001,
    )

    assert result.status is ComplianceStatus.COMPLIANT
    assert result.severity is SeverityLevel.LOW
