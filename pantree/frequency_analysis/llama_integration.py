"""
Llama NIM Integration - Uses Llama NIM to identify related products and enhance recommendations.

This module integrates with NVIDIA's Llama NIM (NVIDIA Inference Microservices)
to query for similar/related products based on purchase patterns.
"""

import requests
import json
from typing import List, Dict, Any, Optional


class LlamaNIMClient:
    """
    Client for interacting with Llama NIM endpoints.
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:8001",
        api_key: Optional[str] = None,
        model: str = "meta/llama-3.1-8b-instruct",
    ):
        """
        Initialize Llama NIM client.

        Args:
            endpoint: Llama NIM endpoint URL
            api_key: Optional API key for authentication
            model: Model name to use
        """
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate text using Llama NIM.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = self.session.post(
                f"{self.endpoint}/v1/chat/completions",
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            print(f"Error calling Llama NIM: {e}")
            return ""
        except (KeyError, IndexError) as e:
            print(f"Error parsing response: {e}")
            return ""

    def find_related_products(
        self,
        product_name: str,
        category: Optional[str] = None,
        max_results: int = 5,
    ) -> List[str]:
        """
        Find products related to the given product.

        Args:
            product_name: Name of the product
            category: Optional category hint
            max_results: Maximum number of related products

        Returns:
            List of related product names
        """
        system_prompt = """You are a grocery store product expert.
Your task is to identify related products that customers typically buy together or as alternatives.
Respond ONLY with a JSON array of product names, nothing else."""

        category_text = f" in the {category} category" if category else ""
        prompt = f"""Given the product "{product_name}"{category_text}, list {max_results} related products that:
1. Are commonly purchased together with this product
2. Are alternatives or substitutes for this product
3. Complement this product in recipes or meals

Respond with a JSON array of product names only.
Example: ["Product 1", "Product 2", "Product 3"]"""

        response = self.generate(prompt, max_tokens=200, temperature=0.3, system_prompt=system_prompt)

        # Parse JSON response
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                # Remove code blocks
                lines = response.split("\n")
                response = "\n".join([l for l in lines if not l.startswith("```")])

            related = json.loads(response)
            if isinstance(related, list):
                return related[:max_results]

        except json.JSONDecodeError:
            print(f"Could not parse Llama response as JSON: {response}")

        return []

    def suggest_subscription_frequency(
        self,
        product_name: str,
        avg_interval_days: float,
        purchase_count: int,
    ) -> Dict[str, Any]:
        """
        Get AI suggestion for subscription frequency.

        Args:
            product_name: Product name
            avg_interval_days: Average days between purchases
            purchase_count: Number of purchases

        Returns:
            Dictionary with frequency suggestion and reasoning
        """
        system_prompt = """You are a subscription service expert for grocery stores.
Analyze purchase patterns and suggest appropriate subscription frequencies.
Respond with JSON only."""

        prompt = f"""Analyze this purchase pattern:
- Product: {product_name}
- Average interval: {avg_interval_days:.1f} days
- Purchase count: {purchase_count}

Suggest:
1. Best subscription frequency (weekly, bi-weekly, monthly, etc.)
2. Confidence level (0-100)
3. Brief reasoning

Respond with JSON:
{{
  "frequency": "weekly|bi-weekly|monthly|custom",
  "interval_days": number,
  "confidence": number,
  "reasoning": "brief explanation"
}}"""

        response = self.generate(prompt, max_tokens=256, temperature=0.5, system_prompt=system_prompt)

        try:
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join([l for l in lines if not l.startswith("```")])

            suggestion = json.loads(response)
            return suggestion

        except json.JSONDecodeError:
            print(f"Could not parse suggestion response: {response}")

        # Fallback to heuristic
        if avg_interval_days <= 8:
            freq = "weekly"
        elif avg_interval_days <= 16:
            freq = "bi-weekly"
        else:
            freq = "monthly"

        return {
            "frequency": freq,
            "interval_days": int(avg_interval_days),
            "confidence": 50,
            "reasoning": "Fallback heuristic based on average interval",
        }

    def analyze_product_category(self, product_name: str) -> Dict[str, Any]:
        """
        Analyze and categorize a product using AI.

        Args:
            product_name: Product name

        Returns:
            Dictionary with category and attributes
        """
        system_prompt = """You are a grocery product categorization expert.
Analyze products and assign appropriate categories and attributes.
Respond with JSON only."""

        prompt = f"""Categorize this product: "{product_name}"

Provide:
1. Category (produce, protein, dairy, grains, snacks, beverages, pantry)
2. Subcategory
3. Perishability (high, medium, low)
4. Typical purchase frequency (weekly, bi-weekly, monthly, occasionally)

Respond with JSON:
{{
  "category": "category_name",
  "subcategory": "subcategory_name",
  "perishability": "high|medium|low",
  "typical_frequency": "weekly|bi-weekly|monthly|occasionally"
}}"""

        response = self.generate(prompt, max_tokens=200, temperature=0.3, system_prompt=system_prompt)

        try:
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join([l for l in lines if not l.startswith("```")])

            return json.loads(response)

        except json.JSONDecodeError:
            print(f"Could not parse categorization response: {response}")

        return {
            "category": "unknown",
            "subcategory": "unknown",
            "perishability": "medium",
            "typical_frequency": "monthly",
        }


class EnhancedFrequencyAnalyzer:
    """
    Enhanced frequency analyzer that integrates Llama NIM for smarter recommendations.
    """

    def __init__(
        self,
        llama_client: LlamaNIMClient,
        min_purchases: int = 3,
        min_confidence: float = 50.0,
    ):
        """
        Initialize enhanced analyzer.

        Args:
            llama_client: LlamaNIMClient instance
            min_purchases: Minimum purchases required
            min_confidence: Minimum confidence threshold
        """
        self.llama = llama_client
        self.min_purchases = min_purchases
        self.min_confidence = min_confidence

    def analyze_with_ai_enhancement(
        self,
        item_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze item with AI enhancement.

        Args:
            item_stats: Item statistics from frequency analysis

        Returns:
            Enhanced analysis with AI suggestions
        """
        item_name = item_stats.get("name", "")
        avg_interval = item_stats.get("avg_interval", 30)
        purchase_count = item_stats.get("count", 0)

        # Get AI suggestion for subscription
        ai_suggestion = self.llama.suggest_subscription_frequency(
            product_name=item_name,
            avg_interval_days=avg_interval,
            purchase_count=purchase_count,
        )

        # Find related products
        related_products = self.llama.find_related_products(
            product_name=item_name,
            max_results=3,
        )

        # Get product categorization
        categorization = self.llama.analyze_product_category(item_name)

        return {
            **item_stats,
            "ai_suggestion": ai_suggestion,
            "related_products": related_products,
            "product_info": categorization,
        }


def demo_llama_integration():
    """Demo Llama NIM integration."""
    print("Demo: Llama NIM Integration\n")
    print("Note: This demo requires a running Llama NIM endpoint.\n")

    # Create client
    client = LlamaNIMClient(
        endpoint="http://localhost:8001",
        model="meta/llama-3.1-8b-instruct",
    )

    # Test 1: Find related products
    print("Test 1: Finding related products for 'Bananas'")
    related = client.find_related_products("Bananas", category="produce")
    print(f"Related products: {related}\n")

    # Test 2: Suggest subscription frequency
    print("Test 2: Suggesting subscription frequency")
    suggestion = client.suggest_subscription_frequency(
        product_name="Whole Milk",
        avg_interval_days=7.2,
        purchase_count=8,
    )
    print(f"Suggestion: {json.dumps(suggestion, indent=2)}\n")

    # Test 3: Categorize product
    print("Test 3: Categorizing product")
    category_info = client.analyze_product_category("Organic Greek Yogurt")
    print(f"Category info: {json.dumps(category_info, indent=2)}\n")

    # Test 4: Enhanced analysis
    print("Test 4: Enhanced frequency analysis")
    analyzer = EnhancedFrequencyAnalyzer(client, min_purchases=3)

    item_stats = {
        "name": "Chicken Breast",
        "count": 6,
        "avg_interval": 14.5,
        "confidence": 78.5,
    }

    enhanced = analyzer.analyze_with_ai_enhancement(item_stats)
    print(f"Enhanced analysis:")
    print(f"  Product: {enhanced['name']}")
    print(f"  AI Suggestion: {enhanced['ai_suggestion']}")
    print(f"  Related: {enhanced['related_products']}")
    print(f"  Category: {enhanced['product_info']}")


if __name__ == "__main__":
    print("="*60)
    print("Llama NIM Integration for Frequency Analysis")
    print("="*60 + "\n")

    # Check if endpoint is available
    print("Checking Llama NIM endpoint availability...")
    try:
        response = requests.get("http://localhost:8001/health", timeout=2)
        if response.ok:
            print("✓ Llama NIM endpoint is available\n")
            demo_llama_integration()
        else:
            print("✗ Llama NIM endpoint returned error")
            print("Please ensure Llama NIM is running on http://localhost:8001")
    except requests.exceptions.RequestException:
        print("✗ Llama NIM endpoint is not available")
        print("\nTo run Llama NIM:")
        print("  docker run -d -p 8001:8000 nvcr.io/nvidia/nim/meta/llama-3.1-8b-instruct")
        print("\nFor demo purposes, showing expected structure:")
        print("\nExpected output structure:")
        print(json.dumps({
            "related_products": ["Product A", "Product B", "Product C"],
            "ai_suggestion": {
                "frequency": "bi-weekly",
                "interval_days": 14,
                "confidence": 85,
                "reasoning": "Based on purchase pattern..."
            },
            "product_info": {
                "category": "dairy",
                "subcategory": "yogurt",
                "perishability": "high",
                "typical_frequency": "weekly"
            }
        }, indent=2))
