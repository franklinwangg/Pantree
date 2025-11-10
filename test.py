# insert seed data into vector db
# get some fake user purchase history data
# 6.1) query the retrieval NIM for similar related products to each product the user has bought.
# 6.2) The retrieval NIM returns all the related products to whatever the user has bought.
# 7.1) query the vector DB if any of the similar related products returned by the retrieval NIM are present in the vector DB. 
# 7.2) Vector DB returns all related products in the user’s purchase history.
# display everything the vector db returns

import json
import requests
import random
import time

# URLs of your running services
VECTOR_DB_URL = "http://localhost:8001"
RETRIEVAL_NIM_URL = "http://localhost:8002/v1/embeddings"


# ✅ Upload JSON file to seed the Vector DB
print("Seeding vector DB from file...")
with open("data/test_seed.json", "rb") as f:
    res = requests.post(f"{VECTOR_DB_URL}/seed_from_file", files={"file": f})
    if res.status_code == 200:
        print("Seeded vector DB.\n")
    else:
        print(f"Failed to seed: {res.text}\n")

# # ✅ Load the same data locally for use in code
with open("data/test_seed.json", "r") as f:
    seed_data = json.load(f)

# ✅ If JSON is shaped like { "user_1": [...], "user_2": [...] }
first_user = list(seed_data.keys())[0]          # pick the first user
user_purchase_history = random.sample(seed_data[first_user], 2)
print(f"User purchase history for {first_user}: {user_purchase_history}\n")

# (If it's a dict like {"products": [...]}, do this instead)
# user_purchase_history = random.sample(seed_data["products"], 2)

print("User purchase history:", user_purchase_history, "\n")

# 3️⃣ Step 6.1 & 6.2: Query Retrieval NIM for similar related products
related_products = []

for product in user_purchase_history:
    # 1️⃣ Get embedding for the current product (query vector)
    emb_resp = requests.post(
        RETRIEVAL_NIM_URL,
        json={
            "model": "nvidia/nv-embedqa-e5-v5",
            "input_type": "query",
            "input": product
        },
    )

    if emb_resp.status_code != 200:
        print(f"Retrieval NIM error for {product}: {emb_resp.text}")
        continue

    # print(f"Response for {product}:\n", emb_resp.text)
    # embedding = emb_resp.json()["embedding"][0]
    embedding = emb_resp.json()["data"][0]["embedding"]

    # 2️⃣ Query the Vector DB for similar items
    db_resp = requests.post(
        f"{VECTOR_DB_URL}/query_embedding",
        json={"embedding": embedding, "n_results": 3}
    )

    if db_resp.status_code == 200:
        matches = db_resp.json().get("matches", [])
        related_products.extend(matches)
        print(f"Related products for '{product}': {matches}")
        # print("Vector DB at least worked")
    else:
        print(f"Vector DB query error for {product}: {db_resp.text}")

print("\n Retrieval NIM returned all related products:", related_products, "\n")

# 4️⃣ Step 7.1 & 7.2: Query Vector DB for any of those related products
results = []
for product in related_products:
    resp = requests.post(f"{VECTOR_DB_URL}/query", json={"query": product, "n_results": 3})
    if resp.status_code == 200:
        matches = resp.json().get("matches", [])
        if matches:
            results.extend(matches)
            print(f" Vector DB found matches for '{product}': {matches}")

print("\n Final results (everything Vector DB returned):")
for item in set(results):
    print("-", item)
