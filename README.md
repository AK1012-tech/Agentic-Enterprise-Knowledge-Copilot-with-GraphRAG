# Agentic Enterprise Knowledge Copilot with GraphRAG

An interview-ready MVP for an enterprise knowledge copilot. It combines file ingestion,
hybrid retrieval, practical GraphRAG expansion, agentic orchestration, citations, feedback,
and Dockerized infrastructure.

## Architecture

```text
Streamlit UI -> FastAPI -> Agentic Workflow
                       -> Hybrid Search -> In-memory/Qdrant-ready chunk index
                       -> GraphRAG -> Neo4j-ready entity relationship graph
                       -> OpenAI-compatible LLM layer
```

The MVP includes deterministic local fallbacks for embeddings and completion, so the core
demo can run without an OpenAI key. Add `OPENAI_API_KEY` in `.env` to use OpenAI.

## Quick Start

```bash
copy .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
streamlit run frontend/streamlit_app.py
```

Open:

- API: `http://localhost:8000/docs`
- UI: `http://localhost:8501`

## Docker

```bash
copy .env.example .env
docker compose -f deployment/docker-compose.yml up --build
```

## Demo Script

1. Upload a PDF, DOCX, TXT, or CSV in the Streamlit sidebar.
2. Ask a factual question about the document.
3. Show citations and confidence verification.
4. Ask a relationship-style question to trigger graph expansion.
5. Record feedback and explain how it supports evaluation.

## Interview Talking Points

- The system is split into API, ingestion, retrieval, graph, agents, workflow, evaluation, and UI modules.
- GraphRAG v1 extracts entities and co-mention relationships, then uses the graph to enrich retrieval.
- Hybrid retrieval combines deterministic vector-style embeddings with keyword scoring and reranking.
- The OpenAI layer has local fallbacks to keep demos reliable.
- Docker Compose includes Postgres, Qdrant, Neo4j, and Redis to show enterprise deployment direction.

