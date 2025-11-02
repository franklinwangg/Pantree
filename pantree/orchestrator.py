"""
Main Orchestrator - Coordinates all components of the Subscribe & Save system.

This service orchestrates the complete flow:
1. Receives seed purchase from frontend
2. Generates simulated purchase history
3. Streams data month-by-month to frontend
4. Initializes Vector DB with purchase data
5. Runs frequency analysis
6. Integrates with Llama NIM for enhanced recommendations
7. Sends to Sagemaker for final recommendations
8. Returns results to frontend
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from simulation.purchase_simulator import PurchaseSimulator
from simulation.streaming_service import StreamingService
from vectordb.db_client import VectorDBClient
from vectordb.embedding_service import EmbeddingService
from vectordb.data_pipeline import DataPipeline
from frequency_analysis.llama_integration import LlamaNIMClient, EnhancedFrequencyAnalyzer
from recommendations.sagemaker_client import SagemakerClient, RecommendationService
from config.settings import config

# Import the existing frequency analyzer
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from analyze_customer_frequency import calculate_item_statistics


class SubscribeSaveOrchestrator:
    """
    Main orchestrator for the Subscribe & Save recommendation system.
    """

    def __init__(
        self,
        simulation_months: int = 6,
        stream_delay: float = 0.5,
        enable_llama: bool = True,
        enable_sagemaker: bool = True,
    ):
        """
        Initialize orchestrator.

        Args:
            simulation_months: Months of history to simulate
            stream_delay: Delay between streaming months
            enable_llama: Enable Llama NIM integration
            enable_sagemaker: Enable Sagemaker integration
        """
        self.simulation_months = simulation_months
        self.stream_delay = stream_delay
        self.enable_llama = enable_llama
        self.enable_sagemaker = enable_sagemaker

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize all service components."""
        print("Initializing Subscribe & Save system components...")

        # Step 2: Simulation
        self.simulator = PurchaseSimulator()
        self.streamer = StreamingService(stream_delay=self.stream_delay)

        # Step 3: Vector DB
        self.db_client = VectorDBClient(
            host=config.VECTORDB_HOST,
            port=config.VECTORDB_PORT,
            collection_name=config.VECTORDB_COLLECTION,
            dimension=config.VECTORDB_DIMENSION,
            backend="mock",  # Use mock for demo; change to "milvus" or "qdrant" for production
        )

        self.embedding_service = EmbeddingService(
            backend="tfidf",  # Use "sentence-transformers" for production
            dimension=config.VECTORDB_DIMENSION,
        )

        self.data_pipeline = DataPipeline(self.db_client, self.embedding_service)

        # Step 4: Frequency Analysis with Llama
        if self.enable_llama:
            try:
                self.llama_client = LlamaNIMClient(
                    endpoint=config.LLAMA_NIM_ENDPOINT,
                    api_key=config.LLAMA_NIM_API_KEY,
                    model=config.LLAMA_NIM_MODEL,
                )
                self.enhanced_analyzer = EnhancedFrequencyAnalyzer(
                    self.llama_client,
                    min_purchases=config.FREQ_MIN_PURCHASES,
                    min_confidence=config.FREQ_MIN_CONFIDENCE,
                )
                print("✓ Llama NIM integration enabled")
            except Exception as e:
                print(f"✗ Llama NIM integration failed: {e}")
                self.enable_llama = False
        else:
            print("- Llama NIM integration disabled")

        # Step 5: Sagemaker
        if self.enable_sagemaker:
            try:
                self.sagemaker_client = SagemakerClient(
                    endpoint_name=config.SAGEMAKER_ENDPOINT,
                    region=config.SAGEMAKER_REGION,
                    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                )
                self.recommendation_service = RecommendationService(
                    self.sagemaker_client,
                    min_confidence=config.FREQ_MIN_CONFIDENCE,
                )
                print("✓ Sagemaker integration enabled")
            except Exception as e:
                print(f"✗ Sagemaker integration failed: {e}")
                self.enable_sagemaker = False
        else:
            print("- Sagemaker integration disabled")

        print("Initialization complete.\n")

    async def process_seed_purchase(
        self,
        seed_items: List[Dict[str, Any]],
        customer_id: str,
        customer_name: str = "Customer",
        archetype: str = "health_conscious",
        streaming_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Complete end-to-end processing pipeline.

        Args:
            seed_items: Initial purchase items
            customer_id: Customer identifier
            customer_name: Customer name
            archetype: Customer archetype
            streaming_callback: Optional callback for streaming updates

        Returns:
            Complete results including recommendations
        """
        print("="*80)
        print(f"Processing seed purchase for customer: {customer_id}")
        print("="*80 + "\n")

        results = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "archetype": archetype,
            "timestamp": datetime.now().isoformat(),
            "steps": {},
        }

        # STEP 2: Generate Simulation
        print("STEP 2: Generating purchase history simulation...")
        simulated_receipts = self.simulator.generate_purchase_history(
            seed_items=seed_items,
            archetype=archetype,
            months=self.simulation_months,
            customer_id=customer_id,
            customer_name=customer_name,
        )

        results["steps"]["simulation"] = {
            "receipts_generated": len(simulated_receipts),
            "months": self.simulation_months,
        }
        print(f"✓ Generated {len(simulated_receipts)} receipts over {self.simulation_months} months\n")

        # STEP 2b: Stream data month-by-month
        print("STEP 2b: Streaming monthly data...")
        streamed_data = []

        async for month_data in self.streamer.stream_monthly_data(
            simulated_receipts,
            callback=streaming_callback,
        ):
            streamed_data.append(month_data)

        results["steps"]["streaming"] = {
            "months_streamed": len(streamed_data),
            "total_receipts": sum(m["receipt_count"] for m in streamed_data),
        }
        print(f"✓ Streamed {len(streamed_data)} months of data\n")

        # STEP 3: Initialize Vector DB
        print("STEP 3: Initializing Vector DB...")
        vectordb_stats = self.data_pipeline.initialize_from_simulation(simulated_receipts)

        results["steps"]["vectordb"] = vectordb_stats
        print(f"✓ Vector DB initialized with {vectordb_stats['successfully_inserted']} items\n")

        # STEP 4: Frequency Analysis
        print("STEP 4: Running frequency analysis...")
        frequency_results = self._run_frequency_analysis(simulated_receipts, customer_id)

        results["steps"]["frequency_analysis"] = {
            "items_analyzed": len(frequency_results),
            "high_confidence_items": len([r for r in frequency_results if r.get("confidence", 0) >= config.FREQ_MIN_CONFIDENCE]),
        }
        print(f"✓ Analyzed {len(frequency_results)} items\n")

        # STEP 4b: Enhance with Llama NIM (if enabled)
        if self.enable_llama and frequency_results:
            print("STEP 4b: Enhancing analysis with Llama NIM...")
            enhanced_results = []

            for item in frequency_results[:5]:  # Enhance top 5 to save API calls
                try:
                    enhanced = self.enhanced_analyzer.analyze_with_ai_enhancement(item)
                    enhanced_results.append(enhanced)
                except Exception as e:
                    print(f"  Warning: Could not enhance {item.get('name')}: {e}")
                    enhanced_results.append(item)

            # Add remaining items without enhancement
            enhanced_results.extend(frequency_results[5:])
            frequency_results = enhanced_results

            results["steps"]["llama_enhancement"] = {
                "items_enhanced": min(5, len(frequency_results)),
            }
            print(f"✓ Enhanced top items with AI insights\n")

        # STEP 5: Get Sagemaker Recommendations
        if self.enable_sagemaker:
            print("STEP 5: Getting Sagemaker recommendations...")
            recommendations = self.recommendation_service.generate_recommendations(
                customer_id=customer_id,
                frequency_analysis=frequency_results,
                top_k=5,
            )

            results["recommendations"] = recommendations
            print(f"✓ Generated {len(recommendations.get('recommendations', []))} recommendations\n")
        else:
            # Fallback recommendations
            print("STEP 5: Using fallback recommendations (Sagemaker disabled)...")
            sorted_items = sorted(
                frequency_results,
                key=lambda x: x.get("confidence", 0),
                reverse=True,
            )[:5]

            results["recommendations"] = {
                "customer_id": customer_id,
                "recommendations": sorted_items,
                "metadata": {
                    "source": "fallback",
                    "total_analyzed": len(frequency_results),
                },
            }
            print(f"✓ Generated {len(sorted_items)} fallback recommendations\n")

        print("="*80)
        print("Processing Complete!")
        print("="*80)

        return results

    def _run_frequency_analysis(
        self,
        receipts: List[Dict[str, Any]],
        customer_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Run frequency analysis on receipts.

        Args:
            receipts: List of receipts
            customer_id: Customer ID

        Returns:
            List of items with frequency analysis
        """
        from collections import defaultdict

        # Aggregate items
        item_purchases = defaultdict(list)

        for receipt in receipts:
            try:
                date = datetime.strptime(receipt["pickup_date"], "%A, %B %d, %Y")
                for item in receipt.get("items", []):
                    item_purchases[item["name"]].append(date)
            except (ValueError, KeyError):
                continue

        # Find most recent date for recency calculations
        all_dates = [d for dates in item_purchases.values() for d in dates]
        reference_date = max(all_dates) if all_dates else datetime.now()

        # Analyze each item
        results = []
        for item_name, dates in item_purchases.items():
            if len(dates) >= config.FREQ_MIN_PURCHASES:
                stats = calculate_item_statistics(dates, reference_date)

                if stats and stats["confidence"] >= config.FREQ_MIN_CONFIDENCE:
                    stats["name"] = item_name
                    results.append(stats)

        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)

        return results

    def cleanup(self):
        """Clean up resources."""
        if self.db_client:
            self.db_client.close()


async def demo_orchestrator():
    """Demo the complete orchestration."""
    print("\n" + "="*80)
    print("DEMO: Complete Subscribe & Save Orchestration")
    print("="*80 + "\n")

    # Create orchestrator
    orchestrator = SubscribeSaveOrchestrator(
        simulation_months=6,
        stream_delay=0.1,  # Fast for demo
        enable_llama=False,  # Disable for demo
        enable_sagemaker=False,  # Disable for demo
    )

    # Define streaming callback
    async def print_month_update(month_data):
        print(f"  → {month_data['month_display']}: {month_data['receipt_count']} receipts, ${month_data['total_spent']:.2f}")

    # Seed purchase
    seed_items = [
        {"name": "Bananas", "price": 1.99},
        {"name": "Chicken Breast", "price": 12.99},
        {"name": "Whole Milk (Gallon)", "price": 5.49},
        {"name": "Whole Wheat Bread", "price": 3.99},
        {"name": "Greek Yogurt", "price": 5.99},
    ]

    # Process
    results = await orchestrator.process_seed_purchase(
        seed_items=seed_items,
        customer_id="demo_customer_001",
        customer_name="Demo Customer",
        archetype="health_conscious",
        streaming_callback=print_month_update,
    )

    # Print recommendations
    print("\n" + "="*80)
    print("FINAL RECOMMENDATIONS")
    print("="*80)

    recs = results.get("recommendations", {}).get("recommendations", [])
    for idx, rec in enumerate(recs, 1):
        print(f"\n{idx}. {rec.get('name', 'Unknown')}")
        print(f"   Confidence: {rec.get('confidence', 0):.1f}%")
        print(f"   Purchase Count: {rec.get('count', 0)}")
        print(f"   Avg Interval: {rec.get('avg_interval', 0):.1f} days")

        if "subscription" in rec:
            sub = rec["subscription"]
            print(f"   Subscription: {sub['frequency']} (every {sub['interval_days']} days)")
            print(f"   Est. Annual Savings: ${sub.get('estimated_annual_savings', 0):.2f}")

    # Cleanup
    orchestrator.cleanup()


if __name__ == "__main__":
    asyncio.run(demo_orchestrator())
