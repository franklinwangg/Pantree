import chromadb

# Path must match your VectorDBManager storage path
storage_path = "./data/chromadb_storage"

client = chromadb.PersistentClient(path=storage_path)
collection = client.get_or_create_collection(name="user_embeddings")

# Fetch all stored items
results = collection.get(include=["documents", "metadatas", "embeddings"])

print("\n📦 Current contents of vector DB:")
for i, (doc, meta, id_) in enumerate(zip(results["documents"], results["metadatas"], results["ids"])):
    print(f"{i+1}. ID: {id_}")
    print(f"   📝 Document: {doc}")
    print(f"   🧠 Metadata: {meta}")
    print()
