"""
Defining the Audit Engine: it executes the full audit process
"""

from dataclasses import dataclass
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
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
    Analyse optimisée : Pour chaque exigence, on récupère la section de la 
    politique la plus pertinente via une recherche vectorielle locale 
    avant de solliciter l'IA.
    """
    
    agent = ComplianceAgent(strategy=strategy)
    requirements = get_requirements(framework)
    findings: List[ComplianceFinding] = []

    # Création d'un index vectoriel temporaire pour ta politique locale
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    policy_chunks = splitter.split_text(policy_text)
    
    # On utilise le même modèle d'embeddings que pour OpenSearch
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    
    local_store = FAISS.from_texts(policy_chunks, embeddings)

    for requirement in requirements:
        # On cherche la section de TA politique qui semble traiter ce requirement
        relevant_policy_sections = local_store.similarity_search(requirement, k=1)
        best_section = relevant_policy_sections[0].page_content if relevant_policy_sections else ""

        # L'agent analyse uniquement cette section par rapport à l'exigence
        finding = agent.analyze(
            vectorstore=vectorstore, # Base OpenSearch (Règles)
            requirement=requirement,
            policy_excerpt=best_section,
            framework=framework,
        )
        findings.append(finding)
        
        # Sleep for the quota
        time.sleep(15)

    # Calcul du score final
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