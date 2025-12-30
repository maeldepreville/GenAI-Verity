import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, cast

import boto3
from google import genai
from langchain_aws import ChatBedrock

from config.settings import get_settings
from src.prompts import (
    Framework,
    PromptContext,
    PromptOrchestrator,
    ReasoningStrategy,
)
from src.retriever import retrieve_with_scores

logger = logging.getLogger(__name__)

class ComplianceStatus(Enum):
    """Define the different states of compliance."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SeverityLevel(Enum):
    """Ranks how dangerous a failure is."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(Enum):
    """Indicates how sure the agent is about its own answer."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceFinding:
    """
    Holds all the information about a specific check.
    """

    requirement: str
    status: ComplianceStatus
    analysis: str
    severity: SeverityLevel
    sources: list[str]
    confidence: ConfidenceLevel
    retrieval_notes: str


class BedrockClient:
    """Amazon Bedrock client wrapper."""

    def __init__(self) -> None:
        settings = get_settings()
        aws = settings._aws_credentials()

        bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=aws.region,
        )

        self.llm = ChatBedrock(
            model="anthropic.claude-3-7-sonnet-20250219-v1:0",
            client=bedrock_runtime,
            model_kwargs={
                "temperature": 0.0,
                "max_tokens": 2048,
            },
        )

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            response = self.llm.invoke(full_prompt)
            return str(response.content)
        except Exception as exc:  # noqa: BLE001
            logger.error("Bedrock API Error: %s", exc)
            return "Error: Could not retrieve analysis from Bedrock."


class GeminiClient:
    """Google Gemini client wrapper (mypy-safe)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.api_key: str = settings.gemini.api_key
        self.model_name: str = settings.gemini.model
        self.temperature: float = settings.gemini.temperature
        self.max_tokens: int = settings.gemini.max_tokens

        genai_any = cast(Any, genai)
        genai_any.configure(api_key=self.api_key)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        genai_any = cast(Any, genai)

        model = genai_any.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            generation_config=genai_any.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )

        try:
            response = model.generate_content(user_prompt)
            return str(response.text)
        except Exception as exc:  # noqa: BLE001
            logger.error("Gemini API Error: %s", exc)
            return "Error: Could not retrieve analysis from Gemini."


class ComplianceAgent:
    """Orchestrates the compliance analysis workflow."""

    def __init__(
        self,
        strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT,
    ) -> None:
        self.strategy = strategy
        self.prompt_orchestrator = PromptOrchestrator()
        self.llm = GeminiClient()

    def analyze(
        self,
        vectorstore: Any,
        requirement: str,
        policy_excerpt: str,
        framework: Framework,
        k: int = 4,
    ) -> ComplianceFinding:
        retrieved: list[tuple[Any, float]] = retrieve_with_scores(
            vectorstore,
            requirement,
            k=k,
        )

        docs = [doc for doc, _ in retrieved]
        scores = [score for _, score in retrieved]

        sources = sorted(
            {str(doc.metadata.get("source", "unknown")) for doc in docs},
        )
        context = "\n\n".join(str(getattr(doc, "page_content", "")) for doc in docs)

        confidence, notes, sufficient = self._assess_retrieval_quality(
            docs,
            scores,
        )

        if not sufficient:
            return ComplianceFinding(
                requirement=requirement,
                status=ComplianceStatus.INSUFFICIENT_EVIDENCE,
                analysis=(
                    "Insufficient regulatory evidence retrieved to make a "
                    "reliable compliance decision. Try rephrasing the "
                    "requirement, adding more regulation documents, or "
                    "increasing k."
                ),
                severity=SeverityLevel.LOW,
                sources=sources,
                confidence=confidence,
                retrieval_notes=notes,
            )

        prompt_context = PromptContext(
            document_text=(
                "REGULATORY CONTEXT (retrieved):\n"
                f"{context}\n\n"
                "POLICY EXCERPT:\n"
                f"{policy_excerpt}\n\n"
                "CITATION RULE:\n"
                "When you justify conclusions, reference sources."
            ),
            framework=framework,
            strategy=self.strategy,
        )

        system_prompt, analysis_prompt = self.prompt_orchestrator.build_complete_prompt(
            prompt_context
        )

        initial_analysis = self.llm.complete(
            system_prompt,
            analysis_prompt,
        )

        refined_analysis = initial_analysis
        if self.strategy is ReasoningStrategy.SELF_CORRECTION:
            refined_analysis = self._self_reflect(initial_analysis)

        status = self._infer_status(refined_analysis)

        return ComplianceFinding(
            requirement=requirement,
            status=status,
            analysis=refined_analysis,
            severity=self._infer_severity(status),
            sources=sources,
            confidence=confidence,
            retrieval_notes=notes,
        )

    def _self_reflect(self, initial_analysis: str) -> str:
        context = PromptContext(
            document_text="",
            framework=Framework.ISO27001,
            strategy=ReasoningStrategy.SELF_CORRECTION,
            previous_analysis=initial_analysis,
        )
        system_prompt = self.prompt_orchestrator.build_system_prompt()
        correction_prompt = self.prompt_orchestrator.build_analysis_prompt(
            context,
        )
        return self.llm.complete(system_prompt, correction_prompt)

    def _infer_status(self, text: str) -> ComplianceStatus:
        lowered = text.lower()
        if "insufficient" in lowered:
            return ComplianceStatus.INSUFFICIENT_EVIDENCE
        if "non-compliant" in lowered or "not compliant" in lowered:
            return ComplianceStatus.NON_COMPLIANT
        if "partial" in lowered:
            return ComplianceStatus.PARTIAL
        if "compliant" in lowered:
            return ComplianceStatus.COMPLIANT
        return ComplianceStatus.INSUFFICIENT_EVIDENCE

    def _infer_severity(self, status: ComplianceStatus) -> SeverityLevel:
        if status is ComplianceStatus.NON_COMPLIANT:
            return SeverityLevel.HIGH
        if status is ComplianceStatus.PARTIAL:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    def _assess_retrieval_quality(
        self,
        docs: list[Any],
        scores: list[float],
    ) -> tuple[ConfidenceLevel, str, bool]:
        if not docs:
            return ConfidenceLevel.LOW, "No chunks retrieved.", False

        non_empty = sum(
            1 for doc in docs if str(getattr(doc, "page_content", "")).strip()
        )
        if non_empty < 2:
            return (
                ConfidenceLevel.LOW,
                "Too few non-empty retrieved chunks.",
                False,
            )

        if not scores:
            return (
                ConfidenceLevel.MEDIUM,
                "Retrieval scores unavailable.",
                True,
            )

        score_min = min(scores)
        score_max = max(scores)
        spread = score_max - score_min

        if non_empty >= 3 and spread > 0.15:
            return (
                ConfidenceLevel.HIGH,
                f"Retrieved {non_empty} chunks; "
                f"score spread={spread:.3f} (good separation).",
                True,
            )

        if non_empty >= 2:
            return (
                ConfidenceLevel.MEDIUM,
                f"Retrieved {non_empty} chunks; "
                f"score spread={spread:.3f} (moderate evidence).",
                True,
            )

        return (
            ConfidenceLevel.LOW,
            f"Retrieved {non_empty} chunks; score spread={spread:.3f} (weak evidence).",
            False,
        )
