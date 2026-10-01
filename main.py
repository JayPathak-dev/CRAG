from retrieval import search_documents
from graph import app

def run_agentic_rag(query: str):
    print(f"\n========== NEW INFERENCE RUN ==========")
    print(f"User Query: {query}\n")

    # 1. Execute Hybrid Retrieval
    print("---RETRIEVAL STAGE---")
    raw_docs = search_documents(query, limit=2)
    
    # Extract the payload for the graph state
    formatted_docs = [{"text": doc.payload["text"], "category": doc.payload["category"]} for doc in raw_docs]

    # 2. Initialize the Graph State
    initial_state = {
        "question": query,
        "documents": formatted_docs,
        "generation": ""
    }

    # 3. Execute the LangGraph Workflow
    final_state = app.invoke(initial_state)

    # 4. Print final output
    if "generation" in final_state and final_state["generation"]:
        print(f"\n---FINAL GENERATED ANSWER---\n{final_state['generation']}\n")
    else:
        print(f"\n---SYSTEM FALLBACK---\nAgent determined context was irrelevant. Rewrote query to: '{final_state['question']}'\n")

if __name__ == "__main__":
    # Test 1: A valid query that should successfully generate an answer
    run_agentic_rag("How many missed heartbeats trigger the PostgreSQL failover?")
    
    # Test 2: An off-topic query that should trigger the Critic and route to Rewriter
    run_agentic_rag("What is the company policy on bringing pets to the office?")