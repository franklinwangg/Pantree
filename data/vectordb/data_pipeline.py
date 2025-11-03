"""
Data Pipeline - Transforms simulation data into Vector DB format.

This module handles the ETL process:
1. Extract: Read simulated receipt data
2. Transform: Calculate statistics and generate embeddings
3. Load: Insert into Vector DB
"""

from typing import List, Dict, Any
from pathlib import Path
import json

from vectordb.db_client import VectorDBClient
from vectordb.embedding_service import EmbeddingService, create_embeddings_from_receipts


class DataPipeline:
    """
    Pipeline for processing receipt data and loading into Vector DB.
    """

    def __init__(
        self,
        db_client: VectorDBClient,
        embedding_service: EmbeddingService,
    ):
        """
        Initialize data pipeline.

        Args:
            db_client: Vector database client
            embedding_service: Embedding service instance
        """
        self.db_client = db_client
        self.embedding_service = embedding_service

    def process_receipts(
        self,
        receipts: List[Dict[str, Any]],
        batch_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Process receipts and load into Vector DB.

        Args:
            receipts: List of receipt dictionaries
            batch_size: Batch size for insertions

        Returns:
            Processing statistics
        """
        print(f"Processing {len(receipts)} receipts...")

        # Create embeddings from receipts
        embeddings_data = create_embeddings_from_receipts(receipts, self.embedding_service)

        print(f"Generated {len(embeddings_data)} item embeddings")

        # Insert in batches
        total_inserted = 0
        failed = 0

        for i in range(0, len(embeddings_data), batch_size):
            batch = embeddings_data[i:i + batch_size]

            try:
                success = self.db_client.insert(batch)
                if success:
                    total_inserted += len(batch)
                    print(f"  Inserted batch {i // batch_size + 1} ({len(batch)} items)")
                else:
                    failed += len(batch)
                    print(f"  Failed to insert batch {i // batch_size + 1}")
            except Exception as e:
                failed += len(batch)
                print(f"  Error inserting batch: {e}")

        return {
            "total_receipts": len(receipts),
            "total_items_processed": len(embeddings_data),
            "successfully_inserted": total_inserted,
            "failed": failed,
        }

    def process_customer_directory(
        self,
        customer_dir: str,
    ) -> Dict[str, Any]:
        """
        Process all receipts in a customer directory.

        Args:
            customer_dir: Path to customer directory containing receipt JSONs

        Returns:
            Processing statistics
        """
        customer_path = Path(customer_dir)

        if not customer_path.exists():
            raise ValueError(f"Customer directory not found: {customer_dir}")

        # Load all receipts
        receipts = []
        for receipt_file in customer_path.glob("receipt_*.json"):
            try:
                with open(receipt_file, 'r') as f:
                    receipt = json.load(f)
                    receipts.append(receipt)
            except Exception as e:
                print(f"Warning: Could not load {receipt_file}: {e}")

        print(f"Loaded {len(receipts)} receipts from {customer_dir}")

        return self.process_receipts(receipts)

    def initialize_from_simulation(
        self,
        simulated_receipts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Initialize Vector DB from simulated purchase data.

        This is the main entry point for Step 3: Data Initialization.

        Args:
            simulated_receipts: Receipts from simulation component

        Returns:
            Initialization statistics
        """
        print("\n" + "="*60)
        print("Initializing Vector DB from Simulation Data")
        print("="*60)

        stats = self.process_receipts(simulated_receipts)

        print("\n" + "="*60)
        print("Vector DB Initialization Complete")
        print(f"  Total Receipts: {stats['total_receipts']}")
        print(f"  Items Processed: {stats['total_items_processed']}")
        print(f"  Successfully Inserted: {stats['successfully_inserted']}")
        print(f"  Failed: {stats['failed']}")
        print("="*60 + "\n")

        return stats


def demo_pipeline():
    """Demo the data pipeline."""
    from simulation.purchase_simulator import PurchaseSimulator

    print("Demo: Data Pipeline\n")

    # Step 1: Generate simulated data
    simulator = PurchaseSimulator()
    seed_items = [
        {"name": "Bananas", "price": 1.99},
        {"name": "Chicken Breast", "price": 12.99},
        {"name": "Whole Milk (Gallon)", "price": 5.49},
        {"name": "Whole Wheat Bread", "price": 3.99},
    ]

    print("Generating simulated purchase history...")
    history = simulator.generate_purchase_history(
        seed_items=seed_items,
        archetype="health_conscious",
        months=6,
        customer_id="demo_001",
    )
    print(f"Generated {len(history)} receipts\n")

    # Step 2: Create DB client and embedding service
    print("Initializing Vector DB client (mock mode)...")
    db_client = VectorDBClient(backend="mock", dimension=128)

    print("Initializing embedding service (TF-IDF mode)...")
    embedding_service = EmbeddingService(backend="tfidf", dimension=128)

    # Step 3: Create pipeline and process data
    pipeline = DataPipeline(db_client, embedding_service)

    stats = pipeline.initialize_from_simulation(history)

    # Step 4: Test retrieval
    print("\nTesting data retrieval...")
    customer_items = db_client.get_customer_items("demo_001")
    print(f"Found {len(customer_items)} items for customer demo_001")

    for item in customer_items[:5]:
        print(f"  - {item['item_name']}: {item['purchase_count']} purchases, "
              f"confidence={item['confidence_score']:.1f}")

    db_client.close()


if __name__ == "__main__":
    demo_pipeline()
