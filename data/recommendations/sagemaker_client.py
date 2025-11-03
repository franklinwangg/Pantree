"""
Sagemaker Client - Integrates with AWS Sagemaker for ML-based recommendations.

This module sends filtered high-frequency items to a Sagemaker endpoint
for final recommendations using trained ML models.
"""

import json
import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime


class SagemakerClient:
    """
    Client for AWS Sagemaker inference endpoints.
    """

    def __init__(
        self,
        endpoint_name: str,
        region: str = "us-west-2",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        """
        Initialize Sagemaker client.

        Args:
            endpoint_name: Name of the Sagemaker endpoint
            region: AWS region
            aws_access_key_id: Optional AWS access key
            aws_secret_access_key: Optional AWS secret key
        """
        self.endpoint_name = endpoint_name
        self.region = region

        # Initialize boto3 client
        session_kwargs = {"region_name": region}

        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
            })

        self.runtime = boto3.client("sagemaker-runtime", **session_kwargs)

    def invoke_endpoint(
        self,
        payload: Dict[str, Any],
        content_type: str = "application/json",
        accept: str = "application/json",
    ) -> Dict[str, Any]:
        """
        Invoke Sagemaker endpoint with payload.

        Args:
            payload: Input data for the model
            content_type: Content type of the payload
            accept: Accept type for response

        Returns:
            Model response
        """
        try:
            response = self.runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType=content_type,
                Accept=accept,
                Body=json.dumps(payload),
            )

            # Parse response
            result = json.loads(response["Body"].read().decode())
            return result

        except Exception as e:
            print(f"Error invoking Sagemaker endpoint: {e}")
            return {"error": str(e)}

    def get_recommendations(
        self,
        customer_id: str,
        frequent_items: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get Subscribe & Save recommendations from Sagemaker.

        Args:
            customer_id: Customer identifier
            frequent_items: List of items with frequency analysis
            top_k: Number of top recommendations to return

        Returns:
            List of recommended items with scores
        """
        # Prepare payload for Sagemaker model
        payload = {
            "customer_id": customer_id,
            "items": frequent_items,
            "top_k": top_k,
            "timestamp": datetime.now().isoformat(),
        }

        # Invoke endpoint
        response = self.invoke_endpoint(payload)

        if "error" in response:
            print(f"Sagemaker error: {response['error']}")
            # Fallback to heuristic recommendations
            return self._fallback_recommendations(frequent_items, top_k)

        # Parse recommendations from response
        recommendations = response.get("recommendations", [])

        return recommendations

    def _fallback_recommendations(
        self,
        frequent_items: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Fallback recommendations when Sagemaker is unavailable.

        Args:
            frequent_items: Frequent items
            top_k: Number of recommendations

        Returns:
            Top K items sorted by confidence
        """
        # Sort by confidence score
        sorted_items = sorted(
            frequent_items,
            key=lambda x: x.get("confidence_score", 0),
            reverse=True,
        )

        # Return top K with recommendation scores
        recommendations = []
        for item in sorted_items[:top_k]:
            rec = {
                **item,
                "recommendation_score": item.get("confidence_score", 50) / 100,
                "source": "fallback_heuristic",
            }
            recommendations.append(rec)

        return recommendations

    def batch_predict(
        self,
        batch_data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Perform batch prediction for multiple customers.

        Args:
            batch_data: List of customer data dictionaries

        Returns:
            List of predictions
        """
        payload = {
            "instances": batch_data,
        }

        response = self.invoke_endpoint(payload)

        if "error" in response:
            print(f"Batch prediction error: {response['error']}")
            return []

        return response.get("predictions", [])


class RecommendationService:
    """
    High-level recommendation service that combines frequency analysis with Sagemaker.
    """

    def __init__(
        self,
        sagemaker_client: SagemakerClient,
        min_confidence: float = 50.0,
    ):
        """
        Initialize recommendation service.

        Args:
            sagemaker_client: SagemakerClient instance
            min_confidence: Minimum confidence threshold
        """
        self.sagemaker = sagemaker_client
        self.min_confidence = min_confidence

    def generate_recommendations(
        self,
        customer_id: str,
        frequency_analysis: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate final recommendations for a customer.

        This is the main entry point for Step 5: Send to Sagemaker.

        Args:
            customer_id: Customer ID
            frequency_analysis: Results from frequency analyzer
            top_k: Number of recommendations

        Returns:
            Dictionary with recommendations and metadata
        """
        print(f"\nGenerating recommendations for customer: {customer_id}")

        # Filter items by confidence threshold
        filtered_items = [
            item for item in frequency_analysis
            if item.get("confidence_score", 0) >= self.min_confidence
        ]

        print(f"  Filtered to {len(filtered_items)} high-confidence items")

        if not filtered_items:
            print("  No items meet confidence threshold")
            return {
                "customer_id": customer_id,
                "recommendations": [],
                "metadata": {
                    "total_analyzed": len(frequency_analysis),
                    "filtered_count": 0,
                    "confidence_threshold": self.min_confidence,
                },
            }

        # Get recommendations from Sagemaker
        recommendations = self.sagemaker.get_recommendations(
            customer_id=customer_id,
            frequent_items=filtered_items,
            top_k=top_k,
        )

        print(f"  Generated {len(recommendations)} recommendations")

        # Enrich recommendations with subscription details
        enriched_recommendations = []
        for rec in recommendations:
            enriched = self._enrich_recommendation(rec)
            enriched_recommendations.append(enriched)

        return {
            "customer_id": customer_id,
            "recommendations": enriched_recommendations,
            "metadata": {
                "total_analyzed": len(frequency_analysis),
                "filtered_count": len(filtered_items),
                "confidence_threshold": self.min_confidence,
                "timestamp": datetime.now().isoformat(),
            },
        }

    def _enrich_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich recommendation with subscription details.

        Args:
            recommendation: Base recommendation

        Returns:
            Enriched recommendation
        """
        avg_interval = recommendation.get("avg_interval_days", 30)

        # Determine subscription frequency
        if avg_interval <= 8:
            frequency = "weekly"
            interval_days = 7
        elif avg_interval <= 16:
            frequency = "bi-weekly"
            interval_days = 14
        elif avg_interval <= 24:
            frequency = "tri-weekly"
            interval_days = 21
        else:
            frequency = "monthly"
            interval_days = 30

        # Calculate estimated savings
        price = recommendation.get("price", 0)
        purchases_per_year = 365 / avg_interval if avg_interval > 0 else 12
        subscription_discount = 0.05  # 5% subscription discount
        annual_savings = price * purchases_per_year * subscription_discount

        return {
            **recommendation,
            "subscription": {
                "frequency": frequency,
                "interval_days": interval_days,
                "estimated_annual_savings": round(annual_savings, 2),
                "discount_percentage": subscription_discount * 100,
            },
        }


def demo_sagemaker_integration():
    """Demo Sagemaker integration."""
    print("Demo: Sagemaker Integration\n")
    print("Note: This demo uses fallback mode (no actual Sagemaker endpoint).\n")

    # Create client (will use fallback if endpoint not available)
    try:
        client = SagemakerClient(
            endpoint_name="subscribe-save-recommendations",
            region="us-west-2",
        )

        # Create recommendation service
        rec_service = RecommendationService(client, min_confidence=60.0)

        # Sample frequency analysis data
        frequency_analysis = [
            {
                "name": "Bananas",
                "count": 8,
                "avg_interval_days": 7.2,
                "confidence_score": 85.3,
                "price": 1.99,
            },
            {
                "name": "Whole Milk",
                "count": 10,
                "avg_interval_days": 6.5,
                "confidence_score": 92.1,
                "price": 5.49,
            },
            {
                "name": "Chicken Breast",
                "count": 6,
                "avg_interval_days": 14.8,
                "confidence_score": 78.4,
                "price": 12.99,
            },
            {
                "name": "Bread",
                "count": 4,
                "avg_interval_days": 25.0,
                "confidence_score": 65.2,
                "price": 3.99,
            },
            {
                "name": "Coffee",
                "count": 2,
                "avg_interval_days": 45.0,
                "confidence_score": 42.5,
                "price": 8.99,
            },
        ]

        # Generate recommendations
        result = rec_service.generate_recommendations(
            customer_id="demo_001",
            frequency_analysis=frequency_analysis,
            top_k=3,
        )

        print("\n" + "="*60)
        print("Recommendations Result")
        print("="*60)
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        print("\nTo use actual Sagemaker endpoint:")
        print("1. Deploy a model to Sagemaker")
        print("2. Set endpoint name and AWS credentials")
        print("3. Ensure proper IAM permissions")


if __name__ == "__main__":
    demo_sagemaker_integration()
