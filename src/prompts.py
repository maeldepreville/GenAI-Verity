"""
Defines how the compliance agent should reason and how prompts are constructed.
"""

from dataclasses import dataclass
from enum import Enum


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
    previous_analysis: str | None = None


class PromptOrchestrator:
    def build_system_prompt(self) -> str:
        return (
            "You are an expert compliance analyst. "
            "Base all conclusions strictly on the provided regulatory context. "
            "If the context is insufficient to decide, state "
            "'Insufficient Evidence' explicitly."
        )

    def build_analysis_prompt(self, context: PromptContext) -> str:
        if context.strategy is ReasoningStrategy.SELF_CORRECTION:
            return self._self_correction_prompt(context)

        return (
            f"Analyze the policy excerpt for compliance with "
            f"{context.framework.value}.\n\n"
            f"{context.document_text}\n\n"
            "TASK:\n"
            "1. Explain the relevant regulatory requirement.\n"
            "2. Assess compliance of the policy excerpt.\n"
            "3. Clearly state whether it is compliant, partially compliant, "
            "or non-compliant.\n"
            "4. Justify your answer using only the regulatory context."
        )

    def build_complete_prompt(
        self,
        context: PromptContext,
    ) -> tuple[str, str]:
        return self.build_system_prompt(), self.build_analysis_prompt(
            context,
        )

    def _self_correction_prompt(self, context: PromptContext) -> str:
        return (
            "Review the following compliance analysis.\n\n"
            "PREVIOUS ANALYSIS:\n"
            "---\n"
            f"{context.previous_analysis}\n"
            "---\n\n"
            "TASK:\n"
            "- Identify unsupported claims or logical errors.\n"
            "- Improve clarity and correctness.\n"
            "- Produce a safer, more grounded final answer."
        )
