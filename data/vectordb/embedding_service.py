"""
Embedding Service - Generates embeddings for products and customer purchase patterns.

This service creates vector embeddings from product names and purchase data
for storage in the vector database.
"""

from typing import List, Dict, Any, Optional
import numpy as np


class EmbeddingService:
    """
    Service for generating embeddings from text and purchase data.

    Supports multiple embedding backends:
    - sentence-transformers (local)
    - OpenAI embeddings (API)
    - Simple TF-IDF (fallback)
    """

    def __init__(
        self,
        backend: str = "sentence-transformers",
        model_name: str = "all-MiniLM-L6-v2",
        dimension: int = 384,
    ):
        """
        Initialize embedding service.

        Args:
            backend: Embedding backend ('sentence-transformers', 'openai', 'tfidf')
            model_name: Model name to use
            dimension: Embedding dimension
        """
        self.backend = backend
        self.model_name = model_name
        self.dimension = dimension
        self.model = None

        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the embedding model."""
        if self.backend == "sentence-transformers":
            self._initialize_sentence_transformers()
        elif self.backend == "openai":
            self._initialize_openai()
        elif self.backend == "tfidf":
            self._initialize_tfidf()
        else:
            raise ValueError(f"Unsupported backend: {self.backend}")

    def _initialize_sentence_transformers(self):
        """Initialize sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"Loaded sentence-transformers model: {self.model_name} (dim={self.dimension})")

        except ImportError:
            print("Warning: sentence-transformers not installed. Install with: pip install sentence-transformers")
            print("Falling back to TF-IDF mode")
            self._initialize_tfidf()
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to TF-IDF mode")
            self._initialize_tfidf()

    def _initialize_openai(self):
        """Initialize OpenAI embeddings."""
        try:
            import openai
            import os

            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY not set")

            self.model = "text-embedding-ada-002"
            self.dimension = 1536
            print(f"Using OpenAI embeddings: {self.model}")

        except ImportError:
            print("Warning: openai not installed. Install with: pip install openai")
            print("Falling back to TF-IDF mode")
            self._initialize_tfidf()
        except Exception as e:
            print(f"Error setting up OpenAI: {e}")
            print("Falling back to TF-IDF mode")
            self._initialize_tfidf()

    def _initialize_tfidf(self):
        """Initialize TF-IDF vectorizer as fallback."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.backend = "tfidf"
        self.model = TfidfVectorizer(max_features=self.dimension)
        self.vocabulary = []
        print(f"Using TF-IDF embeddings (dim={self.dimension})")

    def embed_text(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for text.

        Args:
            texts: List of text strings

        Returns:
            Numpy array of embeddings
        """
        if self.backend == "sentence-transformers":
            return self.model.encode(texts, convert_to_numpy=True)

        elif self.backend == "openai":
            import openai
            embeddings = []
            for text in texts:
                response = openai.Embedding.create(input=text, model=self.model)
                embeddings.append(response['data'][0]['embedding'])
            return np.array(embeddings)

        elif self.backend == "tfidf":
            # For TF-IDF, we need to fit first if vocabulary is empty
            if not self.vocabulary:
                self.model.fit(texts)
                self.vocabulary = self.model.get_feature_names_out()

            vectors = self.model.transform(texts).toarray()

            # Pad or truncate to match dimension
            if vectors.shape[1] < self.dimension:
                padding = np.zeros((vectors.shape[0], self.dimension - vectors.shape[1]))
                vectors = np.hstack([vectors, padding])
            else:
                vectors = vectors[:, :self.dimension]

            return vectors

        return np.zeros((len(texts), self.dimension))

    def embed_product(self, product_name: str, metadata: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Generate embedding for a product.

        Args:
            product_name: Name of the product
            metadata: Optional metadata (category, price, etc.)

        Returns:
            Embedding vector
        """
        # Create rich text representation
        text = product_name

        if metadata:
            if "category" in metadata:
                text += f" {metadata['category']}"
            if "price" in metadata:
                # Add price tier information
                price = metadata["price"]
                if price < 5:
                    text += " budget affordable"
                elif price > 15:
                    text += " premium expensive"

        return self.embed_text([text])[0]

    def embed_purchase_pattern(
        self,
        item_name: str,
        purchase_count: int,
        avg_interval: float,
        category: Optional[str] = None,
    ) -> np.ndarray:
        """
        Generate embedding that captures purchase pattern.

        Args:
            item_name: Product name
            purchase_count: Number of purchases
            avg_interval: Average days between purchases
            category: Product category

        Returns:
            Embedding vector
        """
        # Create text description of purchase pattern
        frequency_desc = "rarely"
        if avg_interval <= 7:
            frequency_desc = "weekly"
        elif avg_interval <= 14:
            frequency_desc = "biweekly"
        elif avg_interval <= 30:
            frequency_desc = "monthly"

        text = f"{item_name} purchased {frequency_desc}"
        if category:
            text += f" {category}"
        if purchase_count >= 5:
            text += " frequently regular customer"

        return self.embed_text([text])[0]

    def create_customer_profile_embedding(
        self,
        items: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Create a customer profile embedding from their purchase history.

        Args:
            items: List of item dictionaries with purchase data

        Returns:
            Aggregated embedding representing customer preferences
        """
        if not items:
            return np.zeros(self.dimension)

        # Create embeddings for each item
        item_texts = []
        weights = []

        for item in items:
            text = item.get("name", "unknown")
            if "category" in item:
                text += f" {item['category']}"

            item_texts.append(text)

            # Weight by purchase frequency/confidence
            weight = item.get("purchase_count", 1) * item.get("confidence_score", 50) / 100
            weights.append(weight)

        # Generate embeddings
        embeddings = self.embed_text(item_texts)

        # Weighted average
        weights_array = np.array(weights).reshape(-1, 1)
        weighted_embeddings = embeddings * weights_array
        profile_embedding = weighted_embeddings.sum(axis=0) / weights_array.sum()

        return profile_embedding


def create_embeddings_from_receipts(
    receipts: List[Dict[str, Any]],
    embedding_service: EmbeddingService,
) -> List[Dict[str, Any]]:
    """
    Create embeddings from receipt data for vector DB insertion.

    Args:
        receipts: List of receipt dictionaries
        embedding_service: EmbeddingService instance

    Returns:
        List of embedding dictionaries ready for Vector DB
    """
    from collections import defaultdict
    from datetime import datetime

    # Aggregate items across receipts
    item_data = defaultdict(lambda: {
        "dates": [],
        "customer_id": None,
        "category": None,
        "price": 0,
    })

    for receipt in receipts:
        customer_id = receipt.get("customer_id", "unknown")

        for item in receipt.get("items", []):
            item_name = item.get("name", "")
            if not item_name:
                continue

            try:
                date = datetime.strptime(receipt["pickup_date"], "%A, %B %d, %Y")
                item_data[item_name]["dates"].append(date)
                item_data[item_name]["customer_id"] = customer_id
                item_data[item_name]["price"] = item.get("price", 0)
            except (ValueError, KeyError):
                continue

    # Create embeddings
    embeddings_data = []

    for item_name, data in item_data.items():
        if len(data["dates"]) < 2:
            continue

        # Calculate statistics
        sorted_dates = sorted(data["dates"])
        intervals = [(sorted_dates[i] - sorted_dates[i-1]).days for i in range(1, len(sorted_dates))]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0

        # Generate embedding
        embedding = embedding_service.embed_purchase_pattern(
            item_name=item_name,
            purchase_count=len(data["dates"]),
            avg_interval=avg_interval,
        )

        embeddings_data.append({
            "customer_id": data["customer_id"],
            "item_name": item_name,
            "embedding": embedding.tolist(),
            "purchase_count": len(data["dates"]),
            "last_purchase_date": sorted_dates[-1].strftime("%Y-%m-%d"),
            "avg_interval_days": round(avg_interval, 1),
            "confidence_score": 75.0,  # Placeholder - would calculate properly
        })

    return embeddings_data


if __name__ == "__main__":
    # Demo usage
    print("Testing Embedding Service...")

    # Create service (will use TF-IDF if sentence-transformers not available)
    service = EmbeddingService(backend="tfidf", dimension=128)

    # Test product embedding
    products = ["Bananas", "Organic Milk", "Whole Wheat Bread"]
    embeddings = service.embed_text(products)
    print(f"\nGenerated embeddings for {len(products)} products")
    print(f"Embedding shape: {embeddings.shape}")

    # Test purchase pattern embedding
    pattern_emb = service.embed_purchase_pattern(
        item_name="Bananas",
        purchase_count=8,
        avg_interval=7.2,
        category="produce"
    )
    print(f"\nPurchase pattern embedding shape: {pattern_emb.shape}")

    # Test customer profile
    items = [
        {"name": "Bananas", "category": "produce", "purchase_count": 8, "confidence_score": 85},
        {"name": "Milk", "category": "dairy", "purchase_count": 10, "confidence_score": 92},
    ]
    profile_emb = service.create_customer_profile_embedding(items)
    print(f"\nCustomer profile embedding shape: {profile_emb.shape}")
