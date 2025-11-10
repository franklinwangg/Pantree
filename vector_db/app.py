import json
from fastapi import FastAPI, UploadFile, File, HTTPException

from pydantic import BaseModel
import chromadb
import numpy as np
import requests
from functools import lru_cache
import os

class VectorDBManager:
    def __init__(self, collection_name="user_embeddings", embedding_dim=1024):
        # --- Ensure persistence directory exists ---
        storage_path = "./data/chromadb_storage"
        os.makedirs(storage_path, exist_ok=True)

        # Initialize persistent client
        self.client = chromadb.PersistentClient(path=storage_path)
        # self.nim_url = "http://localhost:8002/v1/models/nv-embedqa-e5-v5/infer"  # Retrieval Embedding NIM endpoint
        self.nim_url = "http://localhost:8002/v1/embeddings"

        
        # Create or retrieve collection
        self.collection = self.client.get_or_create_collection(name=collection_name)

        # Embedding dimension (set according to your embedding model)
        self.embedding_dim = embedding_dim

    def generate_embedding(self, text: str):
        try:
            payload = {
                "model": "nvidia/nv-embedqa-e5-v5",
                "input": [text],
                "input_type": "passage"
            }
            res = requests.post("http://localhost:8002/v1/embeddings", json=payload)
            res.raise_for_status()
            return res.json()["data"][0]["embedding"]
        except Exception as e:
            print(f"⚠️ Retrieval NIM unavailable, using mock embedding: {e}")
            np.random.seed(abs(hash(text)) % (2**32))
            return np.random.rand(self.embedding_dim).tolist()



    # Add user's purchase embeddings
    
    def add_user_embeddings(self, user_id: str, purchases: list[str]):
        embeddings = [self.generate_embedding(item) for item in purchases]
        ids = [f"{user_id}_{i}" for i in range(len(purchases))]
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=purchases,
            metadatas=[{"user_id": user_id} for _ in purchases],
        )
        print(f"✅ Added {len(purchases)} items for {user_id}")
        # self.client.persist()

    # TODO: Change this to become given a list of item vectors, check which item vectors exist inside the database for the given user
    def check_existing_user_vectors(self, user_id: str, item_vectors: list[list[float]], similarity_threshold=0.9):
        """
        Given a list of embedding vectors, checks which ones are already similar
        to existing embeddings in the DB for the specified user.
        Returns a list of matches with similarity scores.
        """
        results = []
        for vec in item_vectors:
            res = self.collection.query(
                query_embeddings=[vec],
                where={"user_id": user_id},
                n_results=1  # find the closest stored item
            )

            if not res["documents"][0]:
                continue

            closest_item = res["documents"][0][0]
            score = 1 - res["distances"][0][0]  # convert distance → similarity (approx)

            if score >= similarity_threshold:
                results.append({"item": closest_item, "similarity": score})

        return results

    # Optional: seed with sample data
    def seed_data(self):
        seed_data = {
            "user_1": ["toothpaste", "toothbrush", "mouthwash"],
            "user_2": ["coffee", "sugar", "coffee filters"]
        }
        for uid, items in seed_data.items():
            self.add_user_embeddings(uid, items)
            
    def seed_from_json(self, data: dict):
        """
        Seeds the ChromaDB collection from parsed JSON data shaped like:
        {
        "user_1": ["toothpaste", "toothbrush"],
        "user_2": ["coffee", "filters"]
        }
        """
        for user_id, purchases in data.items():
            if not isinstance(purchases, list):
                raise ValueError(f"Purchases for user '{user_id}' must be a list.")

            for item in purchases:
                # Generate embedding for each item
                embedding = self.generate_embedding(item)

                # Store in vector DB
                self.collection.add(
                    ids=[f"{user_id}_{item}"],
                    documents=[item],
                    embeddings=[embedding],
                    metadatas=[{"user_id": user_id}]
                )


# ===============================
# 🔹 FastAPI App
# ===============================
app = FastAPI(title="VectorDB Recommendation API")
db = VectorDBManager()


# --- Request models (kept simple) ---
class AddUserRequest(BaseModel):
    user_id: str
    purchases: list[str]

class QueryRequest(BaseModel):
    user_id: str
    query_items: list[str]
    n_results: int = 3

class QueryEmbeddingRequest(BaseModel):
    embedding: list[float]   # ✅ correct type
    n_results: int = 3

# --- Endpoints ---
@app.post("/add_user")
def add_user(req: AddUserRequest):
    db.add_user_embeddings(req.user_id, req.purchases)
    return {"message": f"Added {len(req.purchases)} items for {req.user_id}"}


@app.post("/query_user")
def query_user(req: QueryRequest):
    results = db.get_similar_user_items(req.user_id, req.query_items, req.n_results)
    return {"results": results}

@app.post("/query_embedding")
def query_embedding(req: QueryEmbeddingRequest):
    results = db.collection.query(query_embeddings=[req.embedding], n_results=req.n_results)
    matches = results["documents"][0]
    return {"matches": matches}



# 🆕 NEW ENDPOINT: Upload JSON file to seed database
@app.post("/seed_from_file")
async def seed_from_file(file: UploadFile = File(...)):
    """
    Accepts a JSON file shaped like:
    {
      "user_1": ["toothpaste", "toothbrush"],
      "user_2": ["coffee", "filters"]
    }
    """
    try:
        contents = await file.read()
        data = json.loads(contents)
        if not isinstance(data, dict):
            raise ValueError("JSON must be a dictionary of user_id: [purchases]")
        db.seed_from_json(data)
        return {"message": "✅ Database seeded successfully", "users": list(data.keys())}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {e}")



# ===============================
# 🔹 Run directly (for local dev)
# ===============================
# if __name__ == "__main__":
#     import uvicorn
#     db.seed_data()
#     uvicorn.run("vector_db.app:app", host="127.0.0.1", port=8001, reload=False)

if __name__ == "__main__":
    import uvicorn
    db.seed_data()
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)
