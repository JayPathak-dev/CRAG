from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
import io

from retrieval import ingest_pdf_files, search_documents
from graph import app as crag_graph

app = FastAPI(title="CRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FileWrapper:
    def __init__(self, upload_file: UploadFile, content: bytes):
        self.name = upload_file.filename
        self.content = content
        
    def read(self):
        return self.content

class QueryRequest(BaseModel):
    query: str

@app.post("/api/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    try:
        wrapped_files = []
        for file in files:
            content = await file.read()
            wrapped_files.append(FileWrapper(file, content))
            
        num_chunks = ingest_pdf_files(wrapped_files)
        return {"success": True, "message": f"Indexed {len(files)} PDF(s) into {num_chunks} vector chunks!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query")
async def query_crag(request: QueryRequest):
    query = request.query
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        # 1. Retrieval
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
        
        # 2. Agent Validation
        initial_state = {
            "question": query,
            "documents": formatted_docs,
            "generation": ""
        }
        
        final_state = crag_graph.invoke(initial_state)
        
        response_data = {
            "documents": formatted_docs,
            "generation": final_state.get("generation"),
            "transformed_query": final_state.get("question") if "generation" not in final_state or not final_state["generation"] else None
        }
        
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
