from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReasoningStrategy(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REACT = "react"
    SELF_CORRECTION = "self_correction"


class Framework(Enum):
    ISO27001 = "ISO 27001"
    GDPR = "GDPR"


@dataclass
class PromptContext:
    document_text: str
    framework: Framework
    strategy: ReasoningStrategy
    previous_analysis: Optional[str] = None


class PromptOrchestrator:
    def build_system_prompt(self) -> str:
        return (
            "You are an expert compliance analyst. "
            "Base all conclusions strictly on the provided regulatory context. "
            "If the context is insufficient to decide, state 'Insufficient Evidence' explicitly."
        )

    def build_analysis_prompt(self, context: PromptContext) -> str:
        if context.strategy == ReasoningStrategy.SELF_CORRECTION:
            return self._self_correction_prompt(context)

        return f"""
            Analyze the policy excerpt for compliance with {context.framework.value}.

            {context.document_text}

            TASK:
            1. Explain the relevant regulatory requirement.
            2. Assess compliance of the policy excerpt.
            3. Clearly state whether it is compliant, partially compliant, or non-compliant.
            4. Justify your answer using only the regulatory context.
        """

    def build_complete_prompt(self, context: PromptContext) -> tuple[str, str]:
        return self.build_system_prompt(), self.build_analysis_prompt(context)

    def _self_correction_prompt(self, context: PromptContext) -> str:
        return f"""
            Review the following compliance analysis.

            PREVIOUS ANALYSIS:
            ---
            {context.previous_analysis}
            ---

            TASK:
            - Identify unsupported claims or logical errors.
            - Improve clarity and correctness.
            - Produce a safer, more grounded final answer.
        """
