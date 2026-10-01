import os
import json
from typing import List, TypedDict
from dotenv import load_dotenv
from litellm import completion
from langgraph.graph import END, StateGraph, START

load_dotenv()

# 1. Define the Graph State
class GraphState(TypedDict):
    question: str
    documents: List[dict]
    generation: str

# 2. The Critic Agent (Grader)
def grade_documents(state: GraphState):
    print("\n---CRITIC AGENT: GRADING DOCUMENTS---")
    question = state["question"]
    documents = state["documents"]
    filtered_docs = []

    # System prompt instructing the LLM to output strict JSON
    system_prompt = """You are a strict grader assessing the relevance of a retrieved document to a user question.
    If the document contains information that can help answer the question, grade it as relevant.
    Respond ONLY with a valid JSON object containing a single key 'score' with the value 'yes' or 'no'."""

    for doc in documents:
        text = doc["text"]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Retrieved document: \n\n {text} \n\n User question: {question}"}
        ]

        # 3. Call LLM via LiteLLM to evaluate
        try:
            response = completion(
                model="ollama/llama3.2",
                messages=messages,
                response_format={"type": "json_object"}
            )
            score = json.loads(response.choices[0].message.content).get("score", "no")
        except Exception as e:
            print(f"Error during LLM call: {e}")
            score = "no"
        
        if score.lower() == "yes":
            print("  - Document relevant.")
            filtered_docs.append(doc)
        else:
            print("  - Document IRRELEVANT. Filtering out.")

    # Return the updated state
    return {"documents": filtered_docs, "question": question}

# 4. The Generator Agent
def generate(state: GraphState):
    print("\n---GENERATOR AGENT: ANSWERING---")
    question = state["question"]
    documents = state["documents"]
    
    # Concatenate document texts
    context = "\n\n".join(doc["text"] for doc in documents)
    
    messages = [
        {"role": "system", "content": "You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Keep the answer concise."},
        {"role": "user", "content": f"Context: {context} \n\n Question: {question}"}
    ]
    
    response = completion(model="ollama/llama3.2", messages=messages)
    answer = response.choices[0].message.content
    
    return {"generation": answer}

# 5. The Query Transformation Agent (Rewriter)
def transform_query(state: GraphState):
    print("\n---REWRITE AGENT: TRANSFORMING QUERY---")
    question = state["question"]
    
    messages = [
        {"role": "system", "content": "You are a specialized query optimization agent for a vector database. Your only job is to rewrite the user's query to be more specific. Output ONLY the optimized search query. Do not include introductory text, explanations, or quotes."},
        {"role": "user", "content": f"Initial question: {question}"}
    ]
    
    response = completion(model="ollama/llama3.2", messages=messages)
    better_question = response.choices[0].message.content
    print(f"  - New Query: {better_question}")
    
    return {"question": better_question}

# 6. The Routing Logic (Conditional Edge)
def decide_to_generate(state: GraphState):
    print("\n---ROUTER: ASSESSING GRADED DOCUMENTS---")
    filtered_docs = state["documents"]
    
    if not filtered_docs:
        print("  - Decision: All documents irrelevant. Routing to Rewrite Query.")
        return "transform_query"
    else:
        print("  - Decision: Relevant documents found. Routing to Generate.")
        return "generate"

# 7. Compile the LangGraph
workflow = StateGraph(GraphState)

# Add nodes (the agents)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("transform_query", transform_query)
workflow.add_node("generate", generate)

# Add edges (the flow)
workflow.add_edge(START, "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    }
)
workflow.add_edge("transform_query", END) # In a full system, this would loop back to search
workflow.add_edge("generate", END)

app = workflow.compile()