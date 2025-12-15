import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from openai import OpenAI

from config.settings import get_settings
from src.prompts import Framework, PromptContext, PromptOrchestrator, ReasoningStrategy


logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class SeverityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceFinding:
    control_id: str
    control_title: str
    requirement: str
    evidence: str
    status: ComplianceStatus
    gap_description: str
    severity: SeverityLevel
    recommendation: str


@dataclass
class ComplianceReport:
    framework: Framework
    document_name: str
    analysis_date: datetime
    findings: list[ComplianceFinding]
    compliance_score: float
    reasoning_trace: str
    strategy_used: ReasoningStrategy
    total_controls_evaluated: int
    compliant_count: int
    partial_count: int
    non_compliant_count: int
    critical_gaps: list[str] = field(default_factory=list)
    high_priority_recommendations: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    success: bool
    report: Optional[ComplianceReport]
    error_message: Optional[str]
    raw_response: Optional[str]


class ResponseParser:
    def parse_compliance_report(
        self,
        response_text: str,
        framework: Framework,
        document_name: str,
        strategy: ReasoningStrategy
    ) -> ComplianceReport:
        findings = self._extract_findings(response_text)
        score = self._extract_score(response_text)
        stats = self._calculate_statistics(findings)

        return ComplianceReport(
            framework=framework,
            document_name=document_name,
            analysis_date=datetime.now(),
            findings=findings,
            compliance_score=score,
            reasoning_trace=response_text,
            strategy_used=strategy,
            total_controls_evaluated=stats['total'],
            compliant_count=stats['compliant'],
            partial_count=stats['partial'],
            non_compliant_count=stats['non_compliant'],
            critical_gaps=self._extract_critical_gaps(findings),
            high_priority_recommendations=self._extract_priority_recommendations(findings)
        )

    def _extract_findings(self, text: str) -> list[ComplianceFinding]:
        findings = []

        sections = self._split_into_finding_sections(text)

        for section in sections:
            finding = self._parse_finding_section(section)
            if finding:
                findings.append(finding)

        return findings

    def _split_into_finding_sections(self, text: str) -> list[str]:
        lines = text.split('\n')
        sections = []
        current_section = []

        for line in lines:
            if self._is_finding_header(line):
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                if current_section:
                    current_section.append(line)

        if current_section:
            sections.append('\n'.join(current_section))

        return sections

    def _is_finding_header(self, line: str) -> bool:
        line_lower = line.lower()
        return any([
            'control id' in line_lower,
            line.strip().startswith('###'),
            line.strip().startswith('##')
        ])

    def _parse_finding_section(self, section: str) -> Optional[ComplianceFinding]:
        try:
            control_id = self._extract_field(section, ['control id', 'control:'])
            control_title = self._extract_field(section, ['title', 'control title'])
            requirement = self._extract_field(section, ['requirement', 'requirements'])
            evidence = self._extract_field(section, ['evidence', 'document evidence'])
            status = self._extract_status(section)
            gap = self._extract_field(section, ['gap', 'gap description'])
            severity = self._extract_severity(section)
            recommendation = self._extract_field(section, ['recommendation', 'action'])

            if not control_id:
                return None

            return ComplianceFinding(
                control_id=control_id,
                control_title=control_title or "Unknown",
                requirement=requirement or "",
                evidence=evidence or "",
                status=status,
                gap_description=gap or "",
                severity=severity,
                recommendation=recommendation or ""
            )
        except Exception as e:
            logger.warning(f"Failed to parse finding section: {e}")
            return None

    def _extract_field(self, text: str, field_names: list[str]) -> str:
        for field_name in field_names:
            pattern = f"{field_name}:"
            for line in text.split('\n'):
                if pattern in line.lower():
                    value = line.split(':', 1)[-1].strip()
                    if value:
                        return value

        return ""

    def _extract_status(self, text: str) -> ComplianceStatus:
        text_lower = text.lower()

        if 'non-compliant' in text_lower or 'non compliant' in text_lower:
            return ComplianceStatus.NON_COMPLIANT
        elif 'partial' in text_lower:
            return ComplianceStatus.PARTIAL
        elif 'compliant' in text_lower:
            return ComplianceStatus.COMPLIANT
        elif 'not applicable' in text_lower or 'n/a' in text_lower:
            return ComplianceStatus.NOT_APPLICABLE

        return ComplianceStatus.NON_COMPLIANT

    def _extract_severity(self, text: str) -> SeverityLevel:
        text_lower = text.lower()

        if 'critical' in text_lower:
            return SeverityLevel.CRITICAL
        elif 'high' in text_lower:
            return SeverityLevel.HIGH
        elif 'medium' in text_lower:
            return SeverityLevel.MEDIUM
        elif 'low' in text_lower:
            return SeverityLevel.LOW

        return SeverityLevel.MEDIUM

    def _extract_score(self, text: str) -> float:
        for line in text.split('\n'):
            line_lower = line.lower()
            if 'compliance score' in line_lower or 'overall score' in line_lower or 'final score' in line_lower:
                import re
                numbers = re.findall(r'\d+\.?\d*', line)
                if numbers:
                    score = float(numbers[0])
                    if score > 100:
                        score = score / 100
                    return min(100.0, max(0.0, score))

        return 0.0

    def _calculate_statistics(self, findings: list[ComplianceFinding]) -> dict[str, int]:
        return {
            'total': len(findings),
            'compliant': sum(1 for f in findings if f.status == ComplianceStatus.COMPLIANT),
            'partial': sum(1 for f in findings if f.status == ComplianceStatus.PARTIAL),
            'non_compliant': sum(1 for f in findings if f.status == ComplianceStatus.NON_COMPLIANT)
        }

    def _extract_critical_gaps(self, findings: list[ComplianceFinding]) -> list[str]:
        return [
            f"{f.control_id}: {f.gap_description}"
            for f in findings
            if f.severity == SeverityLevel.CRITICAL and f.status == ComplianceStatus.NON_COMPLIANT
        ]

    def _extract_priority_recommendations(self, findings: list[ComplianceFinding]) -> list[str]:
        priority_findings = [
            f for f in findings
            if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
            and f.status in [ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL]
        ]

        return [f.recommendation for f in priority_findings if f.recommendation]


class OpenAIClient:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai.api_key)
        self.model = settings.openai.model
        self.temperature = settings.openai.temperature
        self.max_tokens = settings.openai.max_tokens

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

    def complete_with_history(self, messages: list[dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise


class ComplianceAgent:
    def __init__(self, strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT):
        self.strategy = strategy
        self.prompt_orchestrator = PromptOrchestrator()
        self.openai_client = OpenAIClient()
        self.response_parser = ResponseParser()

    def analyze(self, document_text: str, framework: Framework, document_name: str) -> AnalysisResult:
        try:
            response_text = self._execute_analysis(document_text, framework)

            report = self.response_parser.parse_compliance_report(
                response_text=response_text,
                framework=framework,
                document_name=document_name,
                strategy=self.strategy
            )

            return AnalysisResult(
                success=True,
                report=report,
                error_message=None,
                raw_response=response_text
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                success=False,
                report=None,
                error_message=str(e),
                raw_response=None
            )

    def _execute_analysis(self, document_text: str, framework: Framework) -> str:
        context = PromptContext(
            document_text=document_text,
            framework=framework,
            strategy=self.strategy
        )

        system_prompt, analysis_prompt = self.prompt_orchestrator.build_complete_prompt(context)

        response = self.openai_client.complete(system_prompt, analysis_prompt)

        return response

    def analyze_with_self_correction(
        self,
        document_text: str,
        framework: Framework,
        document_name: str
    ) -> AnalysisResult:
        try:
            initial_analysis = self._execute_analysis(document_text, framework)

            corrected_analysis = self._apply_self_correction(initial_analysis)

            report = self.response_parser.parse_compliance_report(
                response_text=corrected_analysis,
                framework=framework,
                document_name=document_name,
                strategy=ReasoningStrategy.SELF_CORRECTION
            )

            return AnalysisResult(
                success=True,
                report=report,
                error_message=None,
                raw_response=corrected_analysis
            )

        except Exception as e:
            logger.error(f"Self-correction analysis failed: {e}")
            return AnalysisResult(
                success=False,
                report=None,
                error_message=str(e),
                raw_response=None
            )

    def _apply_self_correction(self, initial_analysis: str) -> str:
        context = PromptContext(
            document_text="",
            framework=Framework.ISO27001,
            strategy=ReasoningStrategy.SELF_CORRECTION,
            previous_analysis=initial_analysis
        )

        system_prompt = self.prompt_orchestrator.build_system_prompt()
        correction_prompt = self.prompt_orchestrator.build_analysis_prompt(context)

        corrected = self.openai_client.complete(system_prompt, correction_prompt)

        return corrected

    def set_strategy(self, strategy: ReasoningStrategy) -> None:
        self.strategy = strategy


class MultiStrategyComplianceAgent:
    def __init__(self):
        self.agents = {
            strategy: ComplianceAgent(strategy)
            for strategy in ReasoningStrategy
        }

    def analyze_with_strategy(
        self,
        document_text: str,
        framework: Framework,
        document_name: str,
        strategy: ReasoningStrategy
    ) -> AnalysisResult:
        agent = self.agents[strategy]
        return agent.analyze(document_text, framework, document_name)

    def analyze_with_all_strategies(
        self,
        document_text: str,
        framework: Framework,
        document_name: str
    ) -> dict[ReasoningStrategy, AnalysisResult]:
        results = {}

        for strategy in ReasoningStrategy:
            if strategy != ReasoningStrategy.SELF_CORRECTION:
                result = self.analyze_with_strategy(
                    document_text,
                    framework,
                    document_name,
                    strategy
                )
                results[strategy] = result

        return results

    def get_best_result(
        self,
        results: dict[ReasoningStrategy, AnalysisResult]
    ) -> tuple[ReasoningStrategy, AnalysisResult]:
        successful_results = {
            strategy: result
            for strategy, result in results.items()
            if result.success and result.report
        }

        if not successful_results:
            return list(results.items())[0]

        best_strategy, best_result = max(
            successful_results.items(),
            key=lambda item: item[1].report.compliance_score
        )

        return best_strategy, best_result
