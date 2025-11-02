"""
Vector Database Client - Manages connections to Vector DB for customer/product embeddings.

This module provides a client for interacting with a vector database (Milvus/Qdrant/etc.)
to store and query customer purchase embeddings.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime


class VectorDBClient:
    """
    Client for Vector Database operations.

    Supports multiple vector DB backends (Milvus, Qdrant, etc.)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "customer_purchases",
        dimension: int = 768,
        backend: str = "milvus",
    ):
        """
        Initialize Vector DB client.

        Args:
            host: Vector DB host
            port: Vector DB port
            collection_name: Name of the collection to use
            dimension: Embedding dimension size
            backend: Backend type ('milvus', 'qdrant', 'mock')
        """
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.backend = backend
        self.client = None
        self.collection = None

        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the appropriate vector DB backend."""
        if self.backend == "milvus":
            self._initialize_milvus()
        elif self.backend == "qdrant":
            self._initialize_qdrant()
        elif self.backend == "mock":
            self._initialize_mock()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _initialize_milvus(self):
        """Initialize Milvus connection."""
        try:
            from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

            # Connect to Milvus
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
            )

            # Check if collection exists
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                print(f"Connected to existing collection: {self.collection_name}")
            else:
                # Create collection
                fields = [
                    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                    FieldSchema(name="customer_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="item_name", dtype=DataType.VARCHAR, max_length=200),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                    FieldSchema(name="purchase_count", dtype=DataType.INT64),
                    FieldSchema(name="last_purchase_date", dtype=DataType.VARCHAR, max_length=50),
                    FieldSchema(name="avg_interval_days", dtype=DataType.FLOAT),
                    FieldSchema(name="confidence_score", dtype=DataType.FLOAT),
                ]

                schema = CollectionSchema(fields=fields, description="Customer purchase embeddings")
                self.collection = Collection(name=self.collection_name, schema=schema)

                # Create index
                index_params = {
                    "metric_type": "L2",
                    "index_type": "IVF_FLAT",
                    "params": {"nlist": 1024},
                }
                self.collection.create_index(field_name="embedding", index_params=index_params)
                print(f"Created new collection: {self.collection_name}")

            self.collection.load()

        except ImportError:
            print("Warning: pymilvus not installed. Install with: pip install pymilvus")
            print("Falling back to mock mode")
            self._initialize_mock()
        except Exception as e:
            print(f"Error connecting to Milvus: {e}")
            print("Falling back to mock mode")
            self._initialize_mock()

    def _initialize_qdrant(self):
        """Initialize Qdrant connection."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams, PointStruct

            self.client = QdrantClient(host=self.host, port=self.port)

            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.dimension, distance=Distance.COSINE),
                )
                print(f"Created new collection: {self.collection_name}")
            else:
                print(f"Connected to existing collection: {self.collection_name}")

        except ImportError:
            print("Warning: qdrant-client not installed. Install with: pip install qdrant-client")
            print("Falling back to mock mode")
            self._initialize_mock()
        except Exception as e:
            print(f"Error connecting to Qdrant: {e}")
            print("Falling back to mock mode")
            self._initialize_mock()

    def _initialize_mock(self):
        """Initialize mock in-memory vector store for testing."""
        print("Using mock in-memory vector store")
        self.backend = "mock"
        self.mock_data = []

    def insert(self, data: List[Dict[str, Any]]) -> bool:
        """
        Insert embeddings into the vector database.

        Args:
            data: List of dictionaries containing:
                - customer_id: str
                - item_name: str
                - embedding: List[float] or np.ndarray
                - purchase_count: int
                - last_purchase_date: str
                - avg_interval_days: float
                - confidence_score: float

        Returns:
            Success boolean
        """
        try:
            if self.backend == "milvus":
                return self._insert_milvus(data)
            elif self.backend == "qdrant":
                return self._insert_qdrant(data)
            elif self.backend == "mock":
                return self._insert_mock(data)
            return False
        except Exception as e:
            print(f"Error inserting data: {e}")
            return False

    def _insert_milvus(self, data: List[Dict[str, Any]]) -> bool:
        """Insert data into Milvus."""
        entities = [
            [d["customer_id"] for d in data],
            [d["item_name"] for d in data],
            [d["embedding"] for d in data],
            [d["purchase_count"] for d in data],
            [d["last_purchase_date"] for d in data],
            [d["avg_interval_days"] for d in data],
            [d["confidence_score"] for d in data],
        ]

        self.collection.insert(entities)
        self.collection.flush()
        return True

    def _insert_qdrant(self, data: List[Dict[str, Any]]) -> bool:
        """Insert data into Qdrant."""
        from qdrant_client.models import PointStruct

        points = []
        for idx, d in enumerate(data):
            point = PointStruct(
                id=idx,
                vector=d["embedding"],
                payload={
                    "customer_id": d["customer_id"],
                    "item_name": d["item_name"],
                    "purchase_count": d["purchase_count"],
                    "last_purchase_date": d["last_purchase_date"],
                    "avg_interval_days": d["avg_interval_days"],
                    "confidence_score": d["confidence_score"],
                },
            )
            points.append(point)

        self.client.upsert(collection_name=self.collection_name, points=points)
        return True

    def _insert_mock(self, data: List[Dict[str, Any]]) -> bool:
        """Insert data into mock store."""
        self.mock_data.extend(data)
        return True

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar items in the vector database.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_dict: Optional filters (e.g., {"customer_id": "cust_123"})

        Returns:
            List of similar items with metadata
        """
        try:
            if self.backend == "milvus":
                return self._search_milvus(query_vector, top_k, filter_dict)
            elif self.backend == "qdrant":
                return self._search_qdrant(query_vector, top_k, filter_dict)
            elif self.backend == "mock":
                return self._search_mock(query_vector, top_k, filter_dict)
            return []
        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def _search_milvus(self, query_vector, top_k, filter_dict) -> List[Dict[str, Any]]:
        """Search in Milvus."""
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        expr = None
        if filter_dict:
            conditions = [f'{k} == "{v}"' for k, v in filter_dict.items()]
            expr = " && ".join(conditions)

        results = self.collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["customer_id", "item_name", "purchase_count", "confidence_score"],
        )

        return [
            {
                "item_name": hit.entity.get("item_name"),
                "customer_id": hit.entity.get("customer_id"),
                "purchase_count": hit.entity.get("purchase_count"),
                "confidence_score": hit.entity.get("confidence_score"),
                "distance": hit.distance,
            }
            for hit in results[0]
        ]

    def _search_qdrant(self, query_vector, top_k, filter_dict) -> List[Dict[str, Any]]:
        """Search in Qdrant."""
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        query_filter = None
        if filter_dict:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filter_dict.items()
            ]
            query_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )

        return [
            {
                "item_name": hit.payload.get("item_name"),
                "customer_id": hit.payload.get("customer_id"),
                "purchase_count": hit.payload.get("purchase_count"),
                "confidence_score": hit.payload.get("confidence_score"),
                "score": hit.score,
            }
            for hit in results
        ]

    def _search_mock(self, query_vector, top_k, filter_dict) -> List[Dict[str, Any]]:
        """Search in mock store using cosine similarity."""
        if not self.mock_data:
            return []

        query_np = np.array(query_vector)

        # Filter data
        filtered_data = self.mock_data
        if filter_dict:
            filtered_data = [
                d for d in self.mock_data
                if all(d.get(k) == v for k, v in filter_dict.items())
            ]

        # Calculate similarities
        results = []
        for item in filtered_data:
            item_vector = np.array(item["embedding"])
            similarity = np.dot(query_np, item_vector) / (
                np.linalg.norm(query_np) * np.linalg.norm(item_vector)
            )
            results.append({
                "item_name": item["item_name"],
                "customer_id": item["customer_id"],
                "purchase_count": item["purchase_count"],
                "confidence_score": item["confidence_score"],
                "score": float(similarity),
            })

        # Sort by similarity and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_customer_items(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get all items for a specific customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of items with metadata
        """
        if self.backend == "mock":
            return [d for d in self.mock_data if d.get("customer_id") == customer_id]

        # For other backends, use search with filter
        # This is a simplified approach; in production you'd use a proper query
        return []

    def close(self):
        """Close database connection."""
        if self.backend == "milvus":
            from pymilvus import connections
            connections.disconnect("default")
        elif self.backend == "qdrant" and self.client:
            self.client.close()


if __name__ == "__main__":
    # Demo usage
    print("Testing Vector DB Client...")

    # Create client (will use mock mode if no DB available)
    client = VectorDBClient(backend="mock", dimension=128)

    # Create some test data
    test_data = [
        {
            "customer_id": "cust_001",
            "item_name": "Bananas",
            "embedding": np.random.randn(128).tolist(),
            "purchase_count": 5,
            "last_purchase_date": "2025-01-15",
            "avg_interval_days": 7.5,
            "confidence_score": 85.3,
        },
        {
            "customer_id": "cust_001",
            "item_name": "Milk",
            "embedding": np.random.randn(128).tolist(),
            "purchase_count": 8,
            "last_purchase_date": "2025-01-20",
            "avg_interval_days": 5.2,
            "confidence_score": 92.1,
        },
    ]

    # Insert data
    success = client.insert(test_data)
    print(f"Insert successful: {success}")

    # Search for similar items
    query = np.random.randn(128).tolist()
    results = client.search(query, top_k=5)
    print(f"\nFound {len(results)} similar items")

    for result in results:
        print(f"  - {result['item_name']}: confidence={result['confidence_score']}, score={result.get('score', 0):.3f}")

    client.close()
