# CRAG (Corrective Retrieval-Augmented Generation)
## Complete Architecture & Interview Preparation Guide

This document is your master revision guide for explaining the CRAG project in an interview. It covers the problem statement, the architectural evolution (moving from Streamlit to React/FastAPI), the tech stack, and the agentic workflow.

---

## 1. What Problem Does CRAG Solve?
Traditional RAG (Retrieval-Augmented Generation) blindly trusts the documents returned by the search engine. If the search returns irrelevant documents, the LLM will hallucinate an answer based on bad data. 

**CRAG solves this by introducing a "Critic Agent"** that grades the retrieved documents. 
- If documents are relevant -> The Generator creates the final answer.
- If documents are irrelevant -> The Rewriter Agent rewrites the user's query for a better search, preventing hallucinations.

---

## 2. Tech Stack & "Why We Chose It"

### Frontend: React + Vite + Vanilla CSS
- **Why React over Streamlit?** 
  Streamlit is great for quick prototyping, but it lacks the fine-grained control needed for enterprise-grade UI/UX. React allows for seamless state management, custom micro-animations, and a highly responsive single-page application (SPA) feel.
- **Why Vite?**
  Vite provides lightning-fast Hot Module Replacement (HMR) and optimized build times compared to Create React App (Webpack).
- **Why Vanilla CSS?**
  To demonstrate deep frontend fundamentals and create a highly custom, performant "Glassmorphism" UI with CSS variables, without the overhead of heavy component libraries.

### Backend: FastAPI
- **Why FastAPI?**
  FastAPI is asynchronous by default, natively supports Pydantic for strict data validation (like our `QueryRequest`), and automatically generates Swagger UI documentation. It is much faster and more modern than Flask.

### Vector Database: Qdrant (Local Disk Mode)
- **Why Qdrant?**
  Qdrant natively supports **Hybrid Search** (combining Dense semantic vectors and Sparse keyword vectors).
- **Why Local Disk Mode?**
  By running Qdrant in `path="qdrant_storage"` mode, the database runs entirely embedded inside the Python process. This removes the need for Docker containers, making the project incredibly easy to deploy and test anywhere.

### AI & Embeddings: Llama 3.2 + FastEmbed + LangGraph
- **Llama 3.2 (via Ollama):** Runs completely locally for data privacy and zero API costs.
- **FastEmbed:** Generates embeddings locally using ONNX without needing massive PyTorch dependencies.
- **LangGraph:** Provides a stateful graph to orchestrate the Agents (Critic -> Generator / Rewriter). It allows for complex cycles and conditional routing that standard LangChain struggles with.

---

## 3. The Architecture Flow

### A. Data Ingestion Phase
1. User drags and drops PDF files onto the React UI.
2. React sends a `multipart/form-data` POST request to FastAPI (`/api/upload`).
3. FastAPI reads the PDFs, splits them into 500-character chunks with 50-character overlap.
4. `FastEmbed` generates Dense (meaning) and Sparse (keyword) embeddings.
5. Chunks are saved to **Qdrant** on the local disk.

### B. Query & Agent Workflow Phase
1. User types a query in the React UI (e.g., "What is the failover policy?").
2. React sends a JSON POST request to FastAPI (`/api/query`).
3. **Retrieval**: Qdrant executes a Hybrid Search using Reciprocal Rank Fusion (RRF) to find the top 3 best chunks.
4. **Critic Agent (LangGraph)**: 
   - Inspects the retrieved chunks. 
   - Prompts the LLM to output strict JSON (`{"score": "yes"}` or `"no"`).
5. **Conditional Routing**:
   - *If Yes:* Routes to the **Generator**, which builds the final answer from the context.
   - *If No:* Routes to the **Rewriter**, which optimizes the user's query and returns it as a suggestion.
6. The final state is returned to React, which elegantly displays the retrieved chunks and the Agent's decision using dynamic CSS cards.

---

## 4. Common Interview Questions & Answers

**Q: How do you handle LLMs returning unstructured text when you need a programmatic decision (like the Critic)?**
> "I use structured output formatting. In the Critic prompt, I explicitly instruct the model to act as a strict grader and return a JSON object with a single key 'score'. This allows the Python backend to deterministically parse `json.loads()` and route the workflow safely."

**Q: What is Hybrid Search and why didn't you just use standard Semantic Search?**
> "Semantic search (dense vectors) is great for understanding context and paraphrases. However, it often fails on exact keyword matches, like specific part numbers, employee IDs, or acronyms. Hybrid search solves this by combining Dense vectors with Sparse (BM25) vectors, merging the results using Reciprocal Rank Fusion (RRF) for the best of both worlds."

**Q: Why did you migrate the frontend from Streamlit to React/FastAPI?**
> "Streamlit couples the frontend and backend tightly, which doesn't scale well for production microservices. By decoupling them, I created a strict REST API boundary with FastAPI. This allows the frontend (React) to manage complex asynchronous loading states, animations, and custom CSS, while the backend can scale independently or be consumed by other clients."

---

## 5. Folder Structure Summary
```text
CRAG/
├── frontend/             # React SPA (Vite)
│   ├── src/App.jsx       # Main UI component (Search, Upload, Display)
│   └── src/index.css     # Custom Glassmorphism design system
├── server.py             # FastAPI REST endpoints (/upload, /query)
├── retrieval.py          # Qdrant Hybrid Search & PDF processing
├── graph.py              # LangGraph Agent Orchestration (Critic, Gen, Rewrite)
├── qdrant_storage/       # Local database files (auto-generated)
└── start.sh              # Bash script to boot both servers parallelly
```
