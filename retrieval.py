import uuid
import os
import io
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from qdrant_client import models
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVectorParams
from fastembed import TextEmbedding, SparseTextEmbedding

# 1. Connect to local Qdrant container (Updated to use local disk without Docker)
client = QdrantClient(path="qdrant_storage")
COLLECTION_NAME = "enterprise_docs"

# 2. Initialize local embedding models (running via ONNX on Apple Silicon)
dense_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")

# 3. Define sample enterprise documents
DOCUMENTS = [
    {
        "id": 1,
        "text": "Project TITAN-9000 architecture uses a decentralized distributed ledger with a 500ms block time.",
        "category": "architecture"
    },
    {
        "id": 2,
        "text": "Employee remote work policy mandates 3 days in office for engineering teams starting Q3.",
        "category": "hr"
    },
    {
        "id": 3,
        "text": "The failover mechanism for our primary PostgreSQL cluster triggers automatically after 3 missed heartbeats.",
        "category": "infrastructure"
    }
]

def init_and_index():
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={"text-dense": VectorParams(size=384, distance=Distance.COSINE)},
        sparse_vectors_config={"text-sparse": SparseVectorParams()}
    )

    docs_dir = "docs"
    texts = []
    metadata = []

    # Read all files from the docs directory
    for filename in os.listdir(docs_dir):
        if filename.endswith(".txt"):
            category = filename.split("_")[0] # e.g., 'hr', 'it', 'eng'
            with open(os.path.join(docs_dir, filename), "r") as f:
                text = f.read()
                texts.append(text)
                metadata.append({"category": category, "text": text, "source": filename})

    if not texts:
        print("No documents found in 'docs/' directory.")
        return

    # Generate embeddings
    dense_embeddings = list(dense_model.embed(texts))
    sparse_embeddings = list(sparse_model.embed(texts))

    points = []
    for idx in range(len(texts)):
        sparse_vec = sparse_embeddings[idx]
        points.append(
            PointStruct(
                id=idx + 1,
                vector={
                    "text-dense": dense_embeddings[idx].tolist(),
                    "text-sparse": {
                        "indices": sparse_vec.indices.tolist(),
                        "values": sparse_vec.values.tolist(),
                    }
                },
                payload=metadata[idx]
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Successfully indexed {len(points)} documents from disk.")

def search_documents(query_text: str, limit: int = 2):
    # 1. Embed the search query (query_embed optimizes for search context)
    dense_vec = list(dense_model.query_embed(query_text))[0].tolist()
    sparse_vec = list(sparse_model.query_embed(query_text))[0]

    # 2. Execute Hybrid Search using RRF
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        prefetch=[
            models.Prefetch(
                query=dense_vec,
                using="text-dense",
                limit=limit
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vec.indices.tolist(),
                    values=sparse_vec.values.tolist()
                ),
                using="text-sparse",
                limit=limit
            )
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=limit
    )

    print(f"\n--- Results for: '{query_text}' ---")
    for hit in results.points:
        print(f"Score: {hit.score:.4f} | Category: {hit.payload['category']} | Text: {hit.payload['text']}")
    
    return results.points

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # Standard chunk size for high-granularity retrieval
    chunk_overlap=50,      # Preserves semantic context across chunk boundaries
    separators=["\n\n", "\n", " ", ""]
)

def ingest_pdf_files(uploaded_files):
    """Processes uploaded PDF file streams, chunks them, and upserts them to Qdrant."""
    # Ensure fresh collection for new batch
    if client.collection_exists(collection_name=COLLECTION_NAME):
        client.delete_collection(collection_name=COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={"text-dense": VectorParams(size=384, distance=Distance.COSINE)},
        sparse_vectors_config={"text-sparse": SparseVectorParams()}
    )

    all_chunks = []
    chunk_metadata = []

    for file in uploaded_files:
        pdf_reader = PdfReader(io.BytesIO(file.read()))
        file_text = ""
        for page_num, page in enumerate(pdf_reader.pages, 1):
            extracted = page.extract_text()
            if extracted:
                file_text += f"\n[Page {page_num}] " + extracted

        # Split full document text into chunks
        chunks = text_splitter.split_text(file_text)
        for idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_metadata.append({
                "source": file.name,
                "chunk_id": idx + 1,
                "text": chunk,
                "category": file.name.split(".")[0]
            })

    if not all_chunks:
        return 0

    # Generate hybrid embeddings
    dense_embeddings = list(dense_model.embed(all_chunks))
    sparse_embeddings = list(sparse_model.embed(all_chunks))

    # Construct and upsert points
    points = []
    for idx in range(len(all_chunks)):
        sparse_vec = sparse_embeddings[idx]
        points.append(
            PointStruct(
                id=idx + 1,
                vector={
                    "text-dense": dense_embeddings[idx].tolist(),
                    "text-sparse": {
                        "indices": sparse_vec.indices.tolist(),
                        "values": sparse_vec.values.tolist(),
                    }
                },
                payload=chunk_metadata[idx]
            )
        )

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)

if __name__ == "__main__":
    # init_and_index()  # Comment out the indexing function so we don't duplicate data
    
    # Test a highly specific technical query
    search_documents("How many missed heartbeats trigger the PostgreSQL failover?")   

# if __name__ == "__main__":
#     init_and_index()