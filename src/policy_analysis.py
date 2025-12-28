"""
Defining the Audit Engine: it executes the full audit process
"""

from dataclasses import dataclass
from typing import List
import time

from src.agent import ComplianceAgent, ComplianceFinding
from src.prompts import Framework, ReasoningStrategy
from config.requirements import get_requirements


# -------------------------
# Simple Policy Splitter
# -------------------------

def split_policy(policy_text: str, min_length: int = 80) -> List[str]:
    """
    Split policy text into meaningful sections using paragraph boundaries.
    """
    raw_sections = policy_text.split("\n\n")
    sections = [
        section.strip()
        for section in raw_sections
        if len(section.strip()) >= min_length
    ]
    return sections


# -------------------------
# Aggregate Compliance Report
# -------------------------

@dataclass
class ComplianceSummary:
    total_findings: int
    compliant: int
    partial: int
    non_compliant: int
    compliance_score: float
    findings: List[ComplianceFinding]


def compute_compliance_score(findings: List[ComplianceFinding]) -> float:
    """
    Simple, explainable scoring rule.
    """
    score = 100.0

    for f in findings:
        if f.status.name == "NON_COMPLIANT":
            score -= 20
        elif f.status.name == "PARTIAL":
            score -= 10

    return max(0.0, score)


# -------------------------
# Main Orchestration Logic
# -------------------------

def analyze_policy(
    *,
    vectorstore,
    policy_text: str,
    framework: Framework,
    strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT,
) -> ComplianceSummary:
    """
    End-to-end policy analysis:
    - Split policy
    - Evaluate each section against each requirement
    - Aggregate findings
    """

    agent = ComplianceAgent(strategy=strategy)
    sections = split_policy(policy_text)

    findings: List[ComplianceFinding] = []
    
    requirements = get_requirements(framework)

    for requirement in requirements:
        for section in sections:
            finding = agent.analyze(
                vectorstore=vectorstore,
                requirement=requirement,
                policy_excerpt=section,
                framework=framework,
            )
            time.sleep(12) # Avoid exceeding of LLM
            findings.append(finding)

    compliant = sum(1 for f in findings if f.status.name == "COMPLIANT")
    partial = sum(1 for f in findings if f.status.name == "PARTIAL")
    non_compliant = sum(1 for f in findings if f.status.name == "NON_COMPLIANT")

    score = compute_compliance_score(findings)

    return ComplianceSummary(
        total_findings=len(findings),
        compliant=compliant,
        partial=partial,
        non_compliant=non_compliant,
        compliance_score=score,
        findings=findings,
    )
