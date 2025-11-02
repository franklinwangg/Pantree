# inference.py
import json
import os
import requests

# Mock example — replace with actual NVIDIA NIM URLs
LLAMA_NIM_URL = os.getenv("LLAMA_NIM_URL", "https://api.nvidia.com/v1/chat/completions")
EMBED_NIM_URL = os.getenv("EMBED_NIM_URL", "https://api.nvidia.com/v1/embeddings")
NIM_API_KEY = os.getenv("NIM_API_KEY")

def handler(event, context):
    """SageMaker entrypoint — receives JSON payload."""
    body = json.loads(event["body"]) if "body" in event else event
    user_id = body.get("user_id")
    purchases = body.get("purchases", [])

    # Step 1: Frequency logic
    from collections import Counter
    freq = Counter(purchases)
    frequent_items = [k for k, v in freq.items() if v >= 3]

    # Step 2: Call Embedding NIM
    embed_resp = requests.post(
        EMBED_NIM_URL,
        headers={"Authorization": f"Bearer {NIM_API_KEY}"},
        json={"input": frequent_items}
    )
    embeddings = embed_resp.json().get("data", [])

    # Step 3: Call Llama NIM for reasoning
    llama_prompt = f"Given frequent purchases: {frequent_items}, recommend items for Subscribe & Save."
    llama_resp = requests.post(
        LLAMA_NIM_URL,
        headers={"Authorization": f"Bearer {NIM_API_KEY}"},
        json={
            "model": "llama-3.1-nemotron-nano-8B-v1",
            "messages": [{"role": "user", "content": llama_prompt}]
        }
    )
    reasoning = llama_resp.json().get("choices", [{}])[0].get("message", {}).get("content", "")

    result = {
        "subscribe_candidates": frequent_items,
        "reasoning": reasoning,
        "embeddings_count": len(embeddings),
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result)
    }
