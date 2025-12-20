# Compliance Agent – Explainable AI for Regulatory Audits

This project implements an **AI-powered Compliance Agent** designed to analyze internal policy documents and assess their compliance with regulatory frameworks such as **ISO 27001** and **GDPR**.

The system leverages **Retrieval-Augmented Generation (RAG)** and advanced LLM reasoning strategies to produce **explainable, traceable, and actionable compliance reports**.

---

## Architecture Overview

The pipeline follows four main stages:

1. **Regulation Ingestion & Vectorization**
2. **Contextual Retrieval (RAG)**
3. **LLM-based Compliance Analysis**
4. **Scoring & Reporting**

---

## Core Modules

### `ingestion.py`
Builds a local **FAISS vector store** from regulatory text files.

- Loads regulations from `data/regulations/`
- Splits text into overlapping chunks
- Generates embeddings using **Google Generative AI**
- Persists the vector store locally

Used once or when regulations change. :contentReference[oaicite:0]{index=0}

---

### `retriever.py`
Handles vector store loading and similarity-based retrieval.

- Loads the persisted FAISS index
- Retrieves relevant regulatory chunks
- Supports retrieval **with similarity scores** for confidence estimation :contentReference[oaicite:1]{index=1}

---

### `prompts.py`
Centralizes **prompt engineering and reasoning strategies**.

- Supported strategies: Chain-of-Thought, ReAct, Self-Correction
- Framework abstraction (ISO 27001, GDPR)
- Ensures grounded, explainable outputs :contentReference[oaicite:2]{index=2}

---

### `agent.py`
Implements the **Compliance Agent**.

- Retrieves regulatory context via RAG
- Assesses retrieval quality and confidence
- Performs LLM-based compliance reasoning
- Supports self-correction
- Outputs structured `ComplianceFinding` objects (status, severity, confidence, sources) :contentReference[oaicite:3]{index=3}

---

### `policy_analysis.py`
End-to-end orchestration logic.

- Splits policy documents into sections
- Evaluates each section against regulatory requirements
- Aggregates findings
- Computes a transparent compliance score :contentReference[oaicite:4]{index=4}

---

## Compliance Status Levels

- **Compliant**
- **Partially Compliant**
- **Non-Compliant**
- **Insufficient Evidence**

Each decision is justified with citations and confidence indicators.

---

## Key Design Principles

- **Explainability-first** (no black-box decisions)
- **Grounded reasoning** (RAG + strict context usage)
- **Hallucination minimization**
- **Modular and extensible architecture**

---

## Disclaimer

This tool is a **technical decision-support system**.  
It does **not** replace legal or regulatory expertise.

---

## Typical Use Cases

- Internal compliance pre-audits
- Risk and gap analysis
- Policy review and improvement
- AI-assisted audit workflows