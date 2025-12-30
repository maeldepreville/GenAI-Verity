"""
Defining the Audit Engine: executes the full compliance audit process.
"""

import time
from dataclasses import dataclass

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.requirements import get_requirements
from src.agent import ComplianceAgent, ComplianceFinding
from src.prompts import Framework, ReasoningStrategy


def split_policy(policy_text: str, min_length: int = 80) -> list[str]:
    """
    Split policy text into meaningful sections using paragraph boundaries.
    """
    raw_sections = policy_text.split("\n\n")
    return [
        section.strip()
        for section in raw_sections
        if len(section.strip()) >= min_length
    ]


@dataclass
class ComplianceSummary:
    total_findings: int
    compliant: int
    partial: int
    non_compliant: int
    compliance_score: float
    findings: list[ComplianceFinding]


def compute_compliance_score(
    findings: list[ComplianceFinding],
) -> float:
    """
    Simple, explainable compliance scoring rule.
    """
    score = 100.0

    for finding in findings:
        if finding.status is finding.status.NON_COMPLIANT:
            score -= 20.0
        elif finding.status is finding.status.PARTIAL:
            score -= 10.0

    return max(0.0, score)


def analyze_policy(
    *,
    vectorstore: FAISS,
    policy_text: str,
    framework: Framework,
    strategy: ReasoningStrategy = ReasoningStrategy.CHAIN_OF_THOUGHT,
) -> ComplianceSummary:
    """
    Optimized analysis: for each requirement, retrieve the most relevant
    policy section via a local vector search before invoking the LLM.
    """
    agent = ComplianceAgent(strategy=strategy)
    requirements = get_requirements(framework)
    findings: list[ComplianceFinding] = []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    policy_chunks = splitter.split_text(policy_text)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
    )
    local_store = FAISS.from_texts(policy_chunks, embeddings)

    for requirement in requirements:
        relevant_sections = local_store.similarity_search(
            requirement,
            k=1,
        )
        best_section = relevant_sections[0].page_content if relevant_sections else ""

        finding = agent.analyze(
            vectorstore=vectorstore,
            requirement=requirement,
            policy_excerpt=best_section,
            framework=framework,
        )
        findings.append(finding)

        time.sleep(15)

    compliant = sum(
        1 for finding in findings if finding.status is finding.status.COMPLIANT
    )
    partial = sum(1 for finding in findings if finding.status is finding.status.PARTIAL)
    non_compliant = sum(
        1 for finding in findings if finding.status is finding.status.NON_COMPLIANT
    )

    score = compute_compliance_score(findings)

    return ComplianceSummary(
        total_findings=len(findings),
        compliant=compliant,
        partial=partial,
        non_compliant=non_compliant,
        compliance_score=score,
        findings=findings,
    )
