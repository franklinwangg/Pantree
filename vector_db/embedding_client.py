import requests

def generate_embedding(text: str, input_type="passage"):
    payload = {
        "input": [text],
        "model": "nvidia/llama-3.2-nv-embedqa-1b-v2",
        "input_type": input_type
    }
    r = requests.post("http://localhost:8000/v1/embeddings", json=payload)
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]
