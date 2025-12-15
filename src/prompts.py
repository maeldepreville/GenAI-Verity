from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReasoningStrategy(Enum):
    CHAIN_OF_THOUGHT = "chain_of_thought"
    REACT = "react"
    SELF_CORRECTION = "self_correction"
    TREE_OF_THOUGHTS = "tree_of_thoughts"


class Framework(Enum):
    ISO27001 = "ISO 27001"
    GDPR = "GDPR"
    SOC2 = "SOC2"
    HIPAA = "HIPAA"


@dataclass
class PromptContext:
    document_text: str
    framework: Framework
    strategy: ReasoningStrategy
    previous_analysis: Optional[str] = None


@dataclass
class SystemPrompt:
    role: str
    expertise: str
    guidelines: list[str]


@dataclass
class AnalysisPrompt:
    instruction: str
    context: str
    output_format: str


class SystemPromptBuilder:
    def build_compliance_analyst(self) -> str:
        role = self._get_role()
        expertise = self._get_expertise()
        guidelines = self._get_guidelines()

        return self._format_system_prompt(role, expertise, guidelines)

    def _get_role(self) -> str:
        return "You are an expert compliance analyst specializing in information security and data protection regulations."

    def _get_expertise(self) -> str:
        areas = [
            "ISO 27001 information security controls",
            "GDPR data protection requirements",
            "SOC2 trust service criteria",
            "HIPAA privacy and security rules"
        ]
        return "Your expertise includes:\n" + "\n".join(f"- {area}" for area in areas)

    def _get_guidelines(self) -> list[str]:
        return [
            "Analyze documents thoroughly and methodically",
            "Identify specific compliance gaps with evidence",
            "Provide actionable recommendations",
            "Use precise regulatory terminology",
            "Rate severity objectively based on risk impact",
            "Support all findings with direct document quotes"
        ]

    def _format_system_prompt(self, role: str, expertise: str, guidelines: list[str]) -> str:
        guidelines_text = "\n".join(f"- {g}" for g in guidelines)

        return f"""{role}

{expertise}

Guidelines:
{guidelines_text}"""


class ChainOfThoughtPromptBuilder:
    def build(self, context: PromptContext) -> str:
        instruction = self._build_instruction(context.framework)
        thinking_steps = self._build_thinking_steps()
        output_format = self._build_output_format()

        return self._format_prompt(instruction, context.document_text, thinking_steps, output_format)

    def _build_instruction(self, framework: Framework) -> str:
        return f"""Analyze the following policy document for compliance with {framework.value}.

Use step-by-step reasoning to evaluate each relevant control."""

    def _build_thinking_steps(self) -> list[str]:
        return [
            "Identify the policy sections in the document",
            "List applicable regulatory controls for each section",
            "Compare document statements against control requirements",
            "Determine compliance status for each control",
            "Identify gaps and their severity",
            "Formulate specific recommendations"
        ]

    def _build_output_format(self) -> str:
        return """For each finding, provide:
- Control ID and title
- Requirement summary
- Document evidence (quote)
- Compliance status (compliant/partial/non-compliant)
- Gap description
- Severity (critical/high/medium/low)
- Recommendation

Finally, calculate an overall compliance score (0-100)."""

    def _format_prompt(self, instruction: str, document: str, steps: list[str], output_format: str) -> str:
        steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

        return f"""{instruction}

Document:
---
{document}
---

Reasoning Process:
{steps_text}

{output_format}"""


class ReActPromptBuilder:
    def build(self, context: PromptContext) -> str:
        instruction = self._build_instruction(context.framework)
        react_loop = self._build_react_loop()
        available_actions = self._build_available_actions()
        output_format = self._build_output_format()

        return self._format_prompt(instruction, context.document_text, react_loop, available_actions, output_format)

    def _build_instruction(self, framework: Framework) -> str:
        return f"""Analyze this policy document for {framework.value} compliance using the ReAct reasoning pattern.

Alternate between Thought, Action, and Observation steps."""

    def _build_react_loop(self) -> str:
        return """For each control:

Thought: What aspect should I analyze next?
Action: Select an action to gather information
Observation: Record what you found
Analysis: Evaluate compliance based on observation

Repeat until all controls are evaluated."""

    def _build_available_actions(self) -> list[str]:
        return [
            "SEARCH_DOCUMENT: Find mentions of specific security controls",
            "EXTRACT_POLICY: Extract policy statements for a topic",
            "CHECK_REQUIREMENT: Verify if a requirement is met",
            "ASSESS_GAP: Identify what is missing",
            "RATE_SEVERITY: Determine impact of a gap"
        ]

    def _build_output_format(self) -> str:
        return """After completing all iterations, provide:
- Complete findings list with evidence
- Compliance score
- Priority recommendations"""

    def _format_prompt(self, instruction: str, document: str, react_loop: str, actions: list[str], output_format: str) -> str:
        actions_text = "\n".join(f"- {action}" for action in actions)

        return f"""{instruction}

Document:
---
{document}
---

{react_loop}

Available Actions:
{actions_text}

{output_format}"""


class SelfCorrectionPromptBuilder:
    def build(self, context: PromptContext) -> str:
        if not context.previous_analysis:
            raise ValueError("Self-correction requires previous_analysis in context")

        instruction = self._build_instruction()
        review_criteria = self._build_review_criteria()
        output_format = self._build_output_format()

        return self._format_prompt(instruction, context.previous_analysis, review_criteria, output_format)

    def _build_instruction(self) -> str:
        return """Review and improve the following compliance analysis.

Identify errors, omissions, or areas needing refinement."""

    def _build_review_criteria(self) -> list[str]:
        return [
            "Are all critical controls addressed?",
            "Is the evidence specific and quoted accurately?",
            "Are severity ratings justified?",
            "Are recommendations actionable and specific?",
            "Is the compliance score calculation correct?",
            "Are there any logical inconsistencies?"
        ]

    def _build_output_format(self) -> str:
        return """Provide:
1. Identified issues in the original analysis
2. Corrected findings
3. Updated compliance score if needed
4. Explanation of changes made"""

    def _format_prompt(self, instruction: str, previous: str, criteria: list[str], output_format: str) -> str:
        criteria_text = "\n".join(f"- {c}" for c in criteria)

        return f"""{instruction}

Previous Analysis:
---
{previous}
---

Review Criteria:
{criteria_text}

{output_format}"""


class TreeOfThoughtsPromptBuilder:
    def build(self, context: PromptContext) -> str:
        instruction = self._build_instruction(context.framework)
        branching_strategy = self._build_branching_strategy()
        evaluation_method = self._build_evaluation_method()
        output_format = self._build_output_format()

        return self._format_prompt(instruction, context.document_text, branching_strategy, evaluation_method, output_format)

    def _build_instruction(self, framework: Framework) -> str:
        return f"""Analyze this document for {framework.value} compliance by exploring multiple interpretation paths.

For ambiguous sections, consider alternative interpretations."""

    def _build_branching_strategy(self) -> str:
        return """When encountering ambiguous policy statements:

1. Generate 2-3 possible interpretations
2. Evaluate compliance under each interpretation
3. Assess likelihood of each interpretation
4. Select the most reasonable interpretation
5. Note assumptions made"""

    def _build_evaluation_method(self) -> str:
        return """Rate each interpretation path on:
- Consistency with document context
- Alignment with regulatory intent
- Practical feasibility
- Risk level"""

    def _build_output_format(self) -> str:
        return """Provide:
- Main compliance findings
- Ambiguous areas with interpretation analysis
- Recommended interpretation for each ambiguity
- Overall compliance score with confidence level
- Risk assessment based on interpretation uncertainty"""

    def _format_prompt(self, instruction: str, document: str, strategy: str, evaluation: str, output_format: str) -> str:
        return f"""{instruction}

Document:
---
{document}
---

{strategy}

{evaluation}

{output_format}"""


class PromptOrchestrator:
    def __init__(self):
        self.system_builder = SystemPromptBuilder()
        self.cot_builder = ChainOfThoughtPromptBuilder()
        self.react_builder = ReActPromptBuilder()
        self.self_correction_builder = SelfCorrectionPromptBuilder()
        self.tot_builder = TreeOfThoughtsPromptBuilder()

    def build_system_prompt(self) -> str:
        return self.system_builder.build_compliance_analyst()

    def build_analysis_prompt(self, context: PromptContext) -> str:
        if context.strategy == ReasoningStrategy.CHAIN_OF_THOUGHT:
            return self.cot_builder.build(context)
        elif context.strategy == ReasoningStrategy.REACT:
            return self.react_builder.build(context)
        elif context.strategy == ReasoningStrategy.SELF_CORRECTION:
            return self.self_correction_builder.build(context)
        elif context.strategy == ReasoningStrategy.TREE_OF_THOUGHTS:
            return self.tot_builder.build(context)
        else:
            raise ValueError(f"Unknown strategy: {context.strategy}")

    def build_complete_prompt(self, context: PromptContext) -> tuple[str, str]:
        system_prompt = self.build_system_prompt()
        analysis_prompt = self.build_analysis_prompt(context)

        return system_prompt, analysis_prompt


class PromptTemplateRegistry:
    @staticmethod
    def get_extraction_prompt(document_text: str) -> str:
        return f"""Extract key policy statements from this document.

Document:
---
{document_text}
---

Identify:
- Security policies
- Access control rules
- Data protection measures
- Incident response procedures
- Compliance statements

Format as structured list with section references."""

    @staticmethod
    def get_scoring_prompt(findings: str) -> str:
        return f"""Calculate compliance score based on these findings.

Findings:
---
{findings}
---

Scoring criteria:
- Critical non-compliance: -25 points per finding
- High severity gap: -15 points per finding
- Medium severity gap: -10 points per finding
- Low severity gap: -5 points per finding
- Partial compliance: -3 points per finding
- Start from 100 points

Provide:
1. Detailed score calculation
2. Final score (0-100)
3. Score interpretation"""

    @staticmethod
    def get_recommendation_prompt(gap_description: str, severity: str) -> str:
        return f"""Generate actionable recommendation for this compliance gap.

Gap: {gap_description}
Severity: {severity}

Provide:
1. Specific actions to address the gap
2. Implementation priority
3. Expected timeline
4. Resources needed
5. Success criteria"""
