import streamlit as st
from retrieval import search_documents, ingest_pdf_files
from graph import app as crag_graph

st.set_page_config(
    page_title="Enterprise CRAG Assistant",
    page_icon="📁",
    layout="wide"
)

st.title("🛡️ Enterprise PDF Knowledge Base (CRAG)")
st.caption("Upload company PDFs, auto-embed with Hybrid Search (Dense + BM25), and query with Critic Agent self-correction.")

# Sidebar: File Ingestion
with st.sidebar:
    st.header("📂 Document Ingestion")
    uploaded_files = st.file_uploader(
        "Upload Enterprise PDFs",
        type=["pdf"],
        accept_multiple_files=True
    )
    
    if st.button("Index Documents", type="primary"):
        if uploaded_files:
            with st.spinner("Parsing PDFs and generating hybrid embeddings..."):
                num_chunks = ingest_pdf_files(uploaded_files)
                st.success(f"Indexed {len(uploaded_files)} PDF(s) into {num_chunks} vector chunks!")
        else:
            st.warning("Please upload at least one PDF file.")

    st.divider()
    st.markdown("""
    **Pipeline Architecture:**
    - **Chunking:** Recursive (500 chars / 50 overlap)
    - **Storage:** Local Qdrant Docker (Hybrid RRF)
    - **Critic:** LangGraph + Llama 3.2
    """)

# Main Query Interface
query = st.text_input("Enter your question based on uploaded PDFs:", placeholder="e.g., What are the terms of the termination clause?")

if st.button("Run Search & Agent", type="secondary"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        st.divider()
        col1, col2 = st.columns([1, 1])

        # 1. Retrieval Column
        with col1:
            st.subheader("1. Hybrid Retrieval (Qdrant)")
            with st.spinner("Retrieving relevant chunks..."):
                raw_docs = search_documents(query, limit=3)
                formatted_docs = [
                    {
                        "text": doc.payload["text"],
                        "category": doc.payload.get("category", "general"),
                        "source": doc.payload.get("source", "N/A"),
                        "chunk_id": doc.payload.get("chunk_id", "N/A")
                    }
                    for doc in raw_docs
                ]

            for idx, doc in enumerate(formatted_docs, 1):
                with st.expander(f"Chunk #{idx} | Source: {doc['source']} (Chunk {doc['chunk_id']})", expanded=True):
                    st.write(doc["text"])

        # 2. Agent Workflow Column
        with col2:
            st.subheader("2. Agentic Validation (LangGraph)")
            initial_state = {
                "question": query,
                "documents": formatted_docs,
                "generation": ""
            }

            with st.spinner("Critic grading context relevance..."):
                final_state = crag_graph.invoke(initial_state)

            if "generation" in final_state and final_state["generation"]:
                st.success("✅ **Status:** Critic passed documents. Answer grounded.")
                st.markdown("### Final Answer")
                st.info(final_state["generation"])
            else:
                st.error("❌ **Status:** Critic rejected all chunks as irrelevant.")
                st.markdown("### Rewriter Agent Action")
                st.warning(f"**Transformed Query:** {final_state['question']}")
                st.caption("The Critic prevented hallucination and suggested an optimized query.")