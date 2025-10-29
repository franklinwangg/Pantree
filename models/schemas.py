from pydantic import BaseModel
from typing import List, Dict

class AddUserRequest(BaseModel):
    user_id: str
    purchases: List[str]

class QueryRequest(BaseModel):
    user_id: str
    query_items: List[str]
    n_results: int = 3

class EmbeddingRecord(BaseModel):
    user_id: str
    item_id: str
    vector: List[float]
    metadata: Dict
