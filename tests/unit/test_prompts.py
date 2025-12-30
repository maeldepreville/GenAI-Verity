from src.prompts import (
    Framework,
    PromptContext,
    PromptOrchestrator,
    ReasoningStrategy,
)

# ---------------------------------------------------------------------
# Enum sanity checks
# ---------------------------------------------------------------------


def test_framework_enum_values() -> None:
    assert Framework.ISO27001.value == "ISO 27001"
    assert Framework.GDPR.value == "GDPR"


def test_reasoning_strategy_enum_values() -> None:
    assert ReasoningStrategy.CHAIN_OF_THOUGHT.value == "chain_of_thought"
    assert ReasoningStrategy.REACT.value == "react"
    assert ReasoningStrategy.SELF_CORRECTION.value == "self_correction"


# ---------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------


def test_build_system_prompt() -> None:
    orchestrator = PromptOrchestrator()
    prompt = orchestrator.build_system_prompt()

    assert isinstance(prompt, str)
    assert "expert compliance analyst" in prompt.lower()
    assert "insufficient evidence" in prompt.lower()


# ---------------------------------------------------------------------
# Analysis prompt (standard strategies)
# ---------------------------------------------------------------------


def test_build_analysis_prompt_standard_strategy() -> None:
    context = PromptContext(
        document_text="REGULATORY CONTEXT",
        framework=Framework.ISO27001,
        strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
    )

    orchestrator = PromptOrchestrator()
    prompt = orchestrator.build_analysis_prompt(context)

    assert "ISO 27001" in prompt
    assert "REGULATORY CONTEXT" in prompt
    assert "Assess compliance" in prompt
    assert "Justify your answer" in prompt


def test_build_analysis_prompt_react_strategy() -> None:
    context = PromptContext(
        document_text="GDPR CONTEXT",
        framework=Framework.GDPR,
        strategy=ReasoningStrategy.REACT,
    )

    orchestrator = PromptOrchestrator()
    prompt = orchestrator.build_analysis_prompt(context)

    assert "GDPR" in prompt
    assert "GDPR CONTEXT" in prompt
    assert "Assess compliance" in prompt


# ---------------------------------------------------------------------
# Self-correction prompt
# ---------------------------------------------------------------------


def test_build_self_correction_prompt() -> None:
    previous_analysis = "The policy is compliant."

    context = PromptContext(
        document_text="",
        framework=Framework.ISO27001,
        strategy=ReasoningStrategy.SELF_CORRECTION,
        previous_analysis=previous_analysis,
    )

    orchestrator = PromptOrchestrator()
    prompt = orchestrator.build_analysis_prompt(context)

    assert "PREVIOUS ANALYSIS" in prompt
    assert previous_analysis in prompt
    assert "Improve clarity" in prompt
    assert "final answer" in prompt.lower()


# ---------------------------------------------------------------------
# Complete prompt assembly
# ---------------------------------------------------------------------


def test_build_complete_prompt_returns_tuple() -> None:
    context = PromptContext(
        document_text="Some context",
        framework=Framework.GDPR,
        strategy=ReasoningStrategy.CHAIN_OF_THOUGHT,
    )

    orchestrator = PromptOrchestrator()
    system_prompt, analysis_prompt = orchestrator.build_complete_prompt(context)

    assert isinstance(system_prompt, str)
    assert isinstance(analysis_prompt, str)

    assert system_prompt
    assert analysis_prompt
