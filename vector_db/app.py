from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import numpy as np
# from chromadb.config import Settings

# import chromadb

# Persistent client (saves to disk)
# self.client = chromadb.PersistentClient(path="./data/chromadb_storage")


# ===============================
# 🔹 VectorDBManager class
# ===============================
class VectorDBManager:
    def __init__(self, collection_name="user_embeddings", embedding_dim=384):
        # Use persistent local ChromaDB storage
        # self.client = chromadb.Client(Settings(
        #     chroma_db_impl="duckdb+parquet",
        #     persist_directory="./data/chromadb_storage"
        # ))
        self.client = chromadb.PersistentClient(path="./data/chromadb_storage")

        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embedding_dim = embedding_dim

    # Mock embedding (to replace later with Retrieval Embedding NIM)
    def generate_embedding(self, text: str):
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

    # Query similar items for a given user
    def get_similar_user_items(self, user_id: str, query_items: list[str], n_results=3):
        results = []
        for query in query_items:
            emb = self.generate_embedding(query)
            res = self.collection.query(
                query_embeddings=[emb],
                n_results=n_results,
                where={"user_id": user_id},
            )
            results.append({
                "query": query,
                "matches": res["documents"][0],
                "scores": res["distances"][0]
            })
        return results

    # Optional: seed with sample data
    def seed_data(self):
        seed_data = {
            "user_1": ["toothpaste", "toothbrush", "mouthwash"],
            "user_2": ["coffee", "sugar", "coffee filters"]
        }
        for uid, items in seed_data.items():
            self.add_user_embeddings(uid, items)


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


# --- Endpoints ---
@app.post("/add_user")
def add_user(req: AddUserRequest):
    db.add_user_embeddings(req.user_id, req.purchases)
    return {"message": f"Added {len(req.purchases)} items for {req.user_id}"}


@app.post("/query_user")
def query_user(req: QueryRequest):
    results = db.get_similar_user_items(req.user_id, req.query_items, req.n_results)
    return {"results": results}


# ===============================
# 🔹 Run directly (for local dev)
# ===============================
if __name__ == "__main__":
    import uvicorn
    db.seed_data()
    uvicorn.run("vector_db.app:app", host="127.0.0.1", port=8000, reload=True)
