from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import shutil
from typing import List
from pdfminer.high_level import extract_text
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq
from googleapiclient.discovery import build
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for Chainlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding model and knowledge base
model = SentenceTransformer('all-MiniLM-L6-v2')
index = None
chunks = []

# Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Google Custom Search API (used as Brave API requires a paid subscription; Google offers a free tier)
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

# Endpoint to upload PDFs and build the knowledge base
@app.post("/upload_pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    global index, chunks
    chunks = []
    for file in files:
        if not file.filename.endswith('.pdf'):
            continue
        # Save PDF temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Extract text
        text = extract_text(temp_path)
        # Split into chunks (paragraphs)
        paragraphs = text.split('\n\n')
        chunks.extend([p.strip() for p in paragraphs if p.strip()])
        os.remove(temp_path)
    
    if not chunks:
        raise HTTPException(status_code=400, detail="No text extracted from PDFs")
    
    # Generate embeddings
    embeddings = model.encode(chunks)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)  # Normalize for cosine similarity
    # Initialize FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    index.add(embeddings)
    return {"message": "PDFs uploaded and knowledge base built successfully"}

# Function to retrieve passages from the knowledge base
def retrieve_passages(query, k=5):
    query_emb = model.encode([query])
    query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
    distances, indices = index.search(query_emb, k)
    passages = [chunks[idx] for idx in indices[0]]
    return passages, distances[0]

# Function to perform web search using Google Custom Search API
def web_search(query, num_results=3):
    service = build("customsearch", "v1", developerKey=google_api_key)
    res = service.cse().list(q=query, cx=google_cse_id, num=num_results).execute()
    snippets = [item['snippet'] for item in res.get('items', [])]
    return snippets

# Pydantic model for chat request
class ChatRequest(BaseModel):
    query: str

# Chat endpoint with RAG and decomposition
@app.post("/chat")
async def chat(request: ChatRequest):
    if index is None or not chunks:
        raise HTTPException(status_code=400, detail="Knowledge base not built. Please upload PDFs first.")
    
    query = request.query
    
    # Decompose query into related sub-queries
    prompt = f"Generate 3 related questions or rephrased queries that can help answer the following: {query}"
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="mixtral-8x7b-32768",  # Replace with available Groq model
        max_tokens=100
    )
    related_queries = response.choices[0].message.content.strip().split('\n')
    related_queries = [q.strip() for q in related_queries if q.strip()]
    
    # Retrieve passages from KB for each sub-query
    all_passages = []
    for rel_query in related_queries:
        passages, distances = retrieve_passages(rel_query, k=3)
        # Filter passages with high similarity (distance < 0.5 as heuristic)
        filtered_passages = [p for p, d in zip(passages, distances) if d < 0.5]
        all_passages.extend(filtered_passages)
    
    # Remove duplicates
    all_passages = list(set(all_passages))
    
    # If insufficient passages, perform web search
    if len(all_passages) < 2:
        web_snippets = web_search(query, num_results=3)
        all_passages.extend(web_snippets)
    
    # Generate response using retrieved passages
    passages_text = "\n".join(all_passages)
    prompt = f"Based on the following information, answer the question: {query}\n\nInformation:\n{passages_text}"
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="mixtral-8x7b-32768",
        max_tokens=500
    )
    answer = response.choices[0].message.content.strip()
    return {"answer": answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)