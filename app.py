from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from pinecone import Pinecone
import requests

# Initialize Pinecone
pc = Pinecone(api_key="pcsk_2vkjf_MWMZSQJDdCnFAFhuKpAq9NA8aKfZneDocPfYncuVhmTX8Gww7Nn4VnemDMEVzVu")
index = pc.Index("pcdata")

# Initialize FastAPI app
app = FastAPI()

# Request body schema
class QueryInput(BaseModel):
    query: str
    top_k: int = 3

# Function to embed query using local Ollama model
def embed_question(query_text):
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": query_text}
    )
    if response.status_code != 200:
        raise Exception("Failed to get embedding from Ollama")
    return response.json()["embedding"]

# Function to query Pinecone
def query_pinecone(query_text, top_k):
    vector = embed_question(query_text)
    result = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return [match['metadata']['text'] for match in result['matches']]

# Root endpoint
@app.post("/")
def query_handler(data: QueryInput):
    try:
        results = query_pinecone(data.query, data.top_k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
