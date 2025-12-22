import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import google.generativeai as genai 

from config.settings import get_settings
from src.prompts import Framework, PromptContext, PromptOrchestrator, ReasoningStrategy
from src.retriever import retrieve_with_scores


logger = logging.getLogger(__name__)

class ComplianceStatus(Enum):
    """
    Define the different states of compliance
    """
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class SeverityLevel(Enum):
    """
    Ranks how dangerous a failure is
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(Enum):
    """
    Indicates how sure the agent is about its own answer
    """
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceFinding:
    """
    Holds all the information about a specific check: 
    - what the rule was, 
    - the status, the long-form analysis, 
    - the sources used, 
    - and the confidence score
    """
    requirement: str
    status: ComplianceStatus
    analysis: str
    severity: SeverityLevel
    sources: List[str]
    confidence: ConfidenceLevel
    retrieval_notes: str
    

class GeminiClient:  # CHANGED CLASS
    """
    Ensure the Gemini-connection
    """
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.gemini.api_key
        self.model_name = settings.gemini.model
        self.temperature = settings.gemini.temperature
        self.max_tokens = settings.gemini.max_tokens
        
        # Initialize the global client configuration
        genai.configure(api_key=self.api_key)

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        # Gemini 1.5 supports 'system_instruction' at model creation
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
        )
        
        try:
            response = model.generate_content(user_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            return "Error: Could not retrieve analysis from Gemini."


class ComplianceAgent:
    """
    Orchestrates the entire workflow of checking a document and grade it 
    """
    
    def __init__(self, strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT):
        self.strategy = strategy
        self.prompt_orchestrator = PromptOrchestrator()
        self.llm = GeminiClient()  # CHANGED

    def analyze(
        self,
        vectorstore,
        requirement: str,
        policy_excerpt: str,
        framework: Framework,
        k: int = 4,
    ) -> ComplianceFinding:
        # 1) Retrieve regulatory context WITH scores
        retrieved: List[Tuple[object, float]] = retrieve_with_scores(vectorstore, requirement, k=k)

        docs = [d for (d, _score) in retrieved]
        scores = [_score for (_d, _score) in retrieved]

        sources = sorted({d.metadata.get("source", "unknown") for d in docs})
        context = "\n\n".join(d.page_content for d in docs)

        # 2) Compute confidence + decide if evidence is sufficient
        confidence, notes, sufficient = self._assess_retrieval_quality(docs, scores)

        if not sufficient:
            return ComplianceFinding(
                requirement=requirement,
                status=ComplianceStatus.INSUFFICIENT_EVIDENCE,
                analysis=(
                    "Insufficient regulatory evidence retrieved to make a reliable compliance decision. "
                    "Try rephrasing the requirement, adding more regulation documents, or increasing k."
                ),
                severity=SeverityLevel.LOW,
                sources=sources,
                confidence=confidence,
                retrieval_notes=notes,
            )

        # 3) Build prompt context for grounded analysis
        prompt_context = PromptContext(
            document_text=(
                "REGULATORY CONTEXT (retrieved):\n"
                f"{context}\n\n"
                "POLICY EXCERPT:\n"
                f"{policy_excerpt}\n\n"
                "CITATION RULE:\n"
                "When you justify conclusions, reference sources as ."
            ),
            framework=framework,
            strategy=self.strategy,
        )

        system_prompt, analysis_prompt = self.prompt_orchestrator.build_complete_prompt(prompt_context)

        # 4) First-pass analysis
        initial_analysis = self.llm.complete(system_prompt, analysis_prompt)

        # 5) Optional self-reflection
        refined_analysis = initial_analysis
        if self.strategy == ReasoningStrategy.SELF_CORRECTION:
            refined_analysis = self._self_reflect(initial_analysis)

        # 6) Infer status from answer
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
        correction_prompt = self.prompt_orchestrator.build_analysis_prompt(context)
        return self.llm.complete(system_prompt, correction_prompt)

    def _infer_status(self, text: str) -> ComplianceStatus:
        t = text.lower()
        if "insufficient evidence" in t or "not enough evidence" in t:
            return ComplianceStatus.INSUFFICIENT_EVIDENCE
        if "non-compliant" in t or "not compliant" in t:
            return ComplianceStatus.NON_COMPLIANT
        if "partial" in t:
            return ComplianceStatus.PARTIAL
        if "compliant" in t:
            return ComplianceStatus.COMPLIANT
        return ComplianceStatus.INSUFFICIENT_EVIDENCE

    def _infer_severity(self, status: ComplianceStatus) -> SeverityLevel:
        if status == ComplianceStatus.NON_COMPLIANT:
            return SeverityLevel.HIGH
        if status == ComplianceStatus.PARTIAL:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    def _assess_retrieval_quality(
        self,
        docs: List[object],
        scores: List[float],
    ) -> tuple[ConfidenceLevel, str, bool]:
        if not docs:
            return ConfidenceLevel.LOW, "No chunks retrieved.", False

        non_empty = sum(1 for d in docs if getattr(d, "page_content", "").strip())
        if non_empty < 2:
            return ConfidenceLevel.LOW, "Too few non-empty retrieved chunks.", False

        s_min = min(scores) if scores else None
        s_max = max(scores) if scores else None

        if s_min is None or s_max is None:
            return ConfidenceLevel.MEDIUM, "Retrieval scores unavailable.", True

        spread = s_max - s_min

        if non_empty >= 3 and spread > 0.15:
            return ConfidenceLevel.HIGH, f"Retrieved {non_empty} chunks; score spread={spread:.3f} (good separation).", True

        if non_empty >= 2:
            return ConfidenceLevel.MEDIUM, f"Retrieved {non_empty} chunks; score spread={spread:.3f} (moderate evidence).", True

        return ConfidenceLevel.LOW, f"Retrieved {non_empty} chunks; score spread={spread:.3f} (weak evidence).", False