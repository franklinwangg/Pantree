"""
Purchase Simulator - Generates realistic purchase history from a seed purchase.

This component takes an initial purchase (seed) and generates a realistic
purchase history pattern based on customer archetypes and product categories.
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict


class PurchaseSimulator:
    """
    Simulates customer purchase history based on seed purchase and archetype.
    """

    # Product categories and their typical repurchase frequencies (in days)
    CATEGORY_FREQUENCIES = {
        "produce": {"min": 5, "max": 10, "variance": 2},
        "protein": {"min": 7, "max": 14, "variance": 3},
        "dairy": {"min": 5, "max": 10, "variance": 2},
        "grains": {"min": 14, "max": 30, "variance": 5},
        "snacks": {"min": 10, "max": 21, "variance": 4},
        "beverages": {"min": 7, "max": 14, "variance": 3},
        "pantry": {"min": 30, "max": 60, "variance": 10},
    }

    # Archetype-specific shopping patterns
    ARCHETYPE_PATTERNS = {
        "health_conscious": {
            "shopping_frequency": 8,  # days between shops
            "variance": 2,
            "category_weights": {
                "produce": 0.30,
                "protein": 0.25,
                "dairy": 0.15,
                "grains": 0.10,
                "beverages": 0.10,
                "snacks": 0.05,
                "pantry": 0.05,
            },
        },
        "busy_family": {
            "shopping_frequency": 12,
            "variance": 3,
            "category_weights": {
                "snacks": 0.20,
                "protein": 0.20,
                "produce": 0.15,
                "dairy": 0.15,
                "grains": 0.10,
                "beverages": 0.10,
                "pantry": 0.10,
            },
        },
        "budget_conscious": {
            "shopping_frequency": 12,
            "variance": 2,
            "category_weights": {
                "produce": 0.20,
                "protein": 0.15,
                "dairy": 0.15,
                "grains": 0.15,
                "beverages": 0.15,
                "snacks": 0.10,
                "pantry": 0.10,
            },
        },
        "single_professional": {
            "shopping_frequency": 6,
            "variance": 2,
            "category_weights": {
                "protein": 0.25,
                "produce": 0.15,
                "dairy": 0.15,
                "snacks": 0.15,
                "grains": 0.10,
                "beverages": 0.10,
                "pantry": 0.10,
            },
        },
    }

    def __init__(self, product_catalog_path: Optional[str] = None):
        """
        Initialize the purchase simulator.

        Args:
            product_catalog_path: Path to product catalog JSON file
        """
        self.product_catalog = self._load_product_catalog(product_catalog_path)

    def _load_product_catalog(self, catalog_path: Optional[str]) -> Dict[str, List[Dict]]:
        """
        Load product catalog from file or use default products.

        Args:
            catalog_path: Path to catalog file

        Returns:
            Dictionary of products by category
        """
        if catalog_path and Path(catalog_path).exists():
            with open(catalog_path, 'r') as f:
                return json.load(f)

        # Default product catalog (simplified)
        return {
            "produce": [
                {"name": "Bananas", "price": 1.99, "category": "produce"},
                {"name": "White Onion", "price": 1.85, "category": "produce"},
                {"name": "Avocado", "price": 2.49, "category": "produce"},
                {"name": "Tomatoes", "price": 3.99, "category": "produce"},
                {"name": "Lettuce", "price": 2.99, "category": "produce"},
            ],
            "protein": [
                {"name": "Chicken Breast", "price": 12.99, "category": "protein"},
                {"name": "Ground Beef", "price": 9.99, "category": "protein"},
                {"name": "Salmon Fillet", "price": 15.99, "category": "protein"},
                {"name": "Eggs (Dozen)", "price": 4.99, "category": "protein"},
            ],
            "dairy": [
                {"name": "Whole Milk (Gallon)", "price": 5.49, "category": "dairy"},
                {"name": "Cheddar Cheese", "price": 6.99, "category": "dairy"},
                {"name": "Greek Yogurt", "price": 5.99, "category": "dairy"},
            ],
            "grains": [
                {"name": "Whole Wheat Bread", "price": 3.99, "category": "grains"},
                {"name": "Brown Rice", "price": 4.99, "category": "grains"},
                {"name": "Pasta", "price": 2.99, "category": "grains"},
            ],
            "snacks": [
                {"name": "Potato Chips", "price": 3.99, "category": "snacks"},
                {"name": "Granola Bars", "price": 5.99, "category": "snacks"},
            ],
            "beverages": [
                {"name": "Orange Juice", "price": 6.99, "category": "beverages"},
                {"name": "Coffee", "price": 8.99, "category": "beverages"},
            ],
            "pantry": [
                {"name": "Olive Oil", "price": 11.99, "category": "pantry"},
                {"name": "Soy Sauce", "price": 4.99, "category": "pantry"},
            ],
        }

    def categorize_item(self, item_name: str) -> str:
        """
        Determine the category of a product.

        Args:
            item_name: Name of the product

        Returns:
            Category name
        """
        # Search through catalog to find matching item
        for category, products in self.product_catalog.items():
            for product in products:
                if product["name"].lower() in item_name.lower() or item_name.lower() in product["name"].lower():
                    return category

        # Default categorization based on keywords
        keywords = {
            "produce": ["banana", "apple", "orange", "lettuce", "tomato", "onion", "avocado"],
            "protein": ["chicken", "beef", "pork", "fish", "salmon", "egg"],
            "dairy": ["milk", "cheese", "yogurt", "butter", "cream"],
            "grains": ["bread", "rice", "pasta", "cereal", "flour"],
            "snacks": ["chip", "cookie", "cracker", "candy", "bar"],
            "beverages": ["juice", "soda", "coffee", "tea", "water"],
            "pantry": ["oil", "sauce", "spice", "vinegar", "sugar"],
        }

        item_lower = item_name.lower()
        for category, words in keywords.items():
            if any(word in item_lower for word in words):
                return category

        return "pantry"  # Default category

    def generate_purchase_history(
        self,
        seed_items: List[Dict[str, Any]],
        archetype: str = "health_conscious",
        months: int = 6,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate simulated purchase history from seed items.

        Args:
            seed_items: List of initial items from seed purchase
            archetype: Customer archetype (health_conscious, busy_family, etc.)
            months: Number of months of history to generate
            customer_id: Optional customer ID
            customer_name: Optional customer name

        Returns:
            List of receipt dictionaries with purchase history
        """
        if archetype not in self.ARCHETYPE_PATTERNS:
            raise ValueError(f"Unknown archetype: {archetype}")

        pattern = self.ARCHETYPE_PATTERNS[archetype]
        receipts = []

        # Categorize seed items and determine their frequencies
        item_frequencies = {}
        for item in seed_items:
            category = self.categorize_item(item["name"])
            freq_info = self.CATEGORY_FREQUENCIES.get(category, {"min": 14, "max": 30, "variance": 5})

            # Calculate frequency for this specific item (with some randomness)
            avg_days = random.randint(freq_info["min"], freq_info["max"])
            item_frequencies[item["name"]] = {
                "category": category,
                "avg_days": avg_days,
                "variance": freq_info["variance"],
                "price": item.get("price", 5.99),
                "last_purchased": None,
            }

        # Generate receipts over the time period
        start_date = datetime.now() - timedelta(days=months * 30)
        current_date = start_date

        receipt_counter = 1

        while current_date <= datetime.now():
            # Determine items for this receipt
            receipt_items = []

            for item_name, freq_data in item_frequencies.items():
                # Check if item should be purchased based on frequency
                if freq_data["last_purchased"] is None:
                    # First purchase
                    should_buy = random.random() < 0.7  # 70% chance in first receipt
                else:
                    days_since = (current_date - freq_data["last_purchased"]).days
                    expected_days = freq_data["avg_days"]

                    # Probability increases as we approach expected repurchase date
                    if days_since >= expected_days - freq_data["variance"]:
                        probability = min(0.95, (days_since - expected_days + freq_data["variance"]) / (freq_data["variance"] * 2) + 0.5)
                        should_buy = random.random() < probability
                    else:
                        should_buy = False

                if should_buy:
                    quantity = random.randint(1, 3) if freq_data["category"] in ["produce", "protein"] else 1
                    receipt_items.append({
                        "quantity": quantity,
                        "name": item_name,
                        "price": freq_data["price"],
                    })
                    freq_data["last_purchased"] = current_date

            # Only create receipt if there are items
            if receipt_items:
                subtotal = sum(item["price"] * item["quantity"] for item in receipt_items)
                savings = subtotal * random.uniform(0.05, 0.15)
                total = subtotal - savings + (subtotal * 0.08)  # Add 8% tax

                receipt = {
                    "store": "Safeway",
                    "customer_id": customer_id or f"sim_customer_{random.randint(1000, 9999)}",
                    "customer_name": customer_name or "Simulated Customer",
                    "archetype": archetype,
                    "order_number": f"SIM{receipt_counter:06d}",
                    "pickup_date": current_date.strftime("%A, %B %d, %Y"),
                    "pickup_time": "10:00 AM - 6:00 PM",
                    "items": receipt_items,
                    "subtotal": round(subtotal, 2),
                    "total": round(total, 2),
                    "savings": {
                        "total": round(savings, 2),
                        "member_price": round(savings * 0.8, 2),
                        "safeway_for_u": round(savings * 0.2, 2),
                    },
                }

                receipts.append(receipt)
                receipt_counter += 1

            # Move to next shopping date
            days_to_next = pattern["shopping_frequency"] + random.randint(-pattern["variance"], pattern["variance"])
            current_date += timedelta(days=max(1, days_to_next))

        return receipts

    def generate_from_seed_receipt(
        self,
        seed_receipt_path: str,
        months: int = 6,
    ) -> List[Dict[str, Any]]:
        """
        Generate purchase history from a seed receipt file.

        Args:
            seed_receipt_path: Path to seed receipt JSON file
            months: Number of months of history to generate

        Returns:
            List of receipt dictionaries
        """
        with open(seed_receipt_path, 'r') as f:
            seed_receipt = json.load(f)

        return self.generate_purchase_history(
            seed_items=seed_receipt.get("items", []),
            archetype=seed_receipt.get("archetype", "health_conscious"),
            months=months,
            customer_id=seed_receipt.get("customer_id"),
            customer_name=seed_receipt.get("customer_name"),
        )


if __name__ == "__main__":
    # Example usage
    simulator = PurchaseSimulator()

    # Example seed items
    seed_items = [
        {"name": "Bananas", "price": 1.99},
        {"name": "Chicken Breast", "price": 12.99},
        {"name": "Whole Milk (Gallon)", "price": 5.49},
        {"name": "Whole Wheat Bread", "price": 3.99},
    ]

    history = simulator.generate_purchase_history(
        seed_items=seed_items,
        archetype="health_conscious",
        months=6,
        customer_id="demo_001",
        customer_name="Demo Customer"
    )

    print(f"Generated {len(history)} receipts")
    for i, receipt in enumerate(history[:3], 1):
        print(f"\nReceipt {i}:")
        print(f"  Date: {receipt['pickup_date']}")
        print(f"  Items: {len(receipt['items'])}")
        print(f"  Total: ${receipt['total']:.2f}")
