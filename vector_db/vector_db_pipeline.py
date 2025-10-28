import chromadb
import numpy as np
from chromadb.utils import embedding_functions
import json
import os

class VectorDBManager:
    def __init__(self, collection_name="user_embeddings", embedding_dim=384):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(name=collection_name)
        self.embedding_dim = embedding_dim # Dimension of the mock embeddings

    # TODO(Franklin): Replace this mock embedding generator with a call to the Retrieval Embedding NIM.
    # The NIM should take item text → return a real embedding vector (same dimension: 384).
    def generate_embedding(self, text: str):
        np.random.seed(abs(hash(text)) % (2**32))
        return np.random.rand(self.embedding_dim).tolist()

    # --- Add a user's purchased items ---
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

    # --- Retrieve similar items for a user ---
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

    # --- Optional: seed with mock data ---
    def seed_data(self):
        seed_data = {
            "user_1": ["toothpaste", "toothbrush", "mouthwash"],
            "user_2": ["coffee", "sugar", "coffee filters"]
        }
        for uid, items in seed_data.items():
            self.add_user_embeddings(uid, items) #TODO replace with real retrieval embedding NIM later

    # def seed_data(self):
    #     # Get path to JSON file (relative to current script)
    #     file_path = os.path.join(os.path.dirname(__file__), "../data/seed_data.json")

    #     # Load seed data from JSON
    #     with open(file_path, "r") as f:
    #         seed_data = json.load(f)

    #     # Iterate through users and items
    #     for uid, items in seed_data.items():
    #         self.add_user_embeddings(uid, items)  # TODO: replace with Retrieval Embedding NIM later

# --- Example usage (only runs when this file is executed directly) ---
if __name__ == "__main__":
    db = VectorDBManager()
    db.seed_data()
    results = db.get_similar_user_items("user_1", ["dental floss"])
    for r in results:
        print(f"\nQuery: {r['query']}")
        for match, score in zip(r["matches"], r["scores"]):
            print(f"  → {match} (score={score:.4f})")
