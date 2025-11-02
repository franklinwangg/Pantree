# TODO

## Backend / SageMaker

---

## Data & Frequency Analysis

---

## 🔍 Vector DB & Embedding (Franklin)

- [ ] deploy the vector db on cloud
- [ ] create a real token to vector converter on a docker container
- [ ] currently use nv-embedqa-e3-v0, but upon deployment use nv-embedqa-e5-v5
- [ ] test vector retrieval and similarity reasoning
  - ## Progress:
    so rn, i have a local vector db set up on my computer. it returns mocked retrieval embeddings cuz i havent been able to set up the retrieval embedding nim on a docker container yet(i need to first update my gpu so my gpu can support some stuff, and then i need to pull an appropriate retrieval embedding nim like nvidia/llama-3.2-nv-embedqa-1b-v2 from nvidia's docker registry and then run it, and then i can send requests to it).

That’s a great checkpoint — you’ve already done the **most essential local setup** (vector DB running + mocked retrieval). Right now, since you’re temporarily blocked by the GPU driver and NIM container, here’s how to use this downtime efficiently.

---

## ✅ What You _Can_ Still Work On (Before the NIM Runs)

### 2. **Structure how embeddings will be stored**

Settle schema early so you don’t refactor later:

```json
{
  "user_id": "123",
  "item_id": "B00X4WHP5E",
  "vector": [0.123, -0.055, ...],
  "metadata": {
    "category": "coffee",
    "frequency_score": 0.92
  }
}
```

You can mock this schema now using fake embeddings.

---

### 3. **Implement similarity logic**

Use cosine similarity / FAISS search locally:

```python
from sklearn.metrics.pairwise import cosine_similarity
```

Then later just replace the embedding generator with the NIM call — the retrieval logic stays identical.

---

### 4. **Prepare your NIM integration wrapper**

Write a helper module now that will _later_ call the NIM:

```python
def get_embedding(text: str):
    # Temporary mock
    return np.random.rand(1536)

# Later, swap with:
# response = requests.post(NIM_URL, json={"model": "nv-embedqa-e5-v5", "input": text})
# return response.json()["data"][0]["embedding"]
```

This makes switching seamless once the container runs.

---

### 5. **Document endpoints + data flow**

Draft a short README or comment block that shows:

```
Frontend → SageMaker → Frequency Analysis → Llama NIM → Vector DB → Embedding Retrieval
```

It’ll help your teammates integrate your service easily.

---

## 🚧 What’s Best to Wait On

- Running the actual **Retrieval Embedding NIM**
- Measuring **real query latency / embedding quality**
- GPU-specific optimizations

---

So TL;DR —

> ✅ Keep developing everything _around_ the embedding generator (DB logic, schema, API, similarity tests).
> 🕐 Wait to plug in the real NIM endpoint until after the GPU driver update.

You’ll still make visible progress on your subsystem and be integration-ready by the time the embedding service is online.

Would you like me to outline how your vector DB service fits into the full data flow (with arrows showing SageMaker → Frequency → Llama → Vector → Frontend)? It could help you design your API interfaces now.

## 🤖 Llama NIM & Frontend
