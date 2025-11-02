import json
from collections import Counter
from typing import List, Dict

def find_frequent_items(purchases: List[str], threshold: int = 3) -> Dict[str, List[str]]:
    """
    Identify items purchased frequently within a month.

    Args:
        purchases (List[str]): A list of item names representing purchases.
        threshold (int): Minimum number of purchases to qualify as frequent.

    Returns:
        Dict[str, List[str]]: JSON-compatible dict with frequent items.
    """
    item_counts = Counter(purchases)
    frequent_items = [item for item, count in item_counts.items() if count >= threshold]
    return {"frequent_items": frequent_items}


if __name__ == "__main__":
    # --- Test Dataset ---
    monthly_purchases = [
        "chicken", "eggs", "bread", "milk",
        "chicken", "eggs", "milk",
        "chicken", "eggs", "apples",
        "milk", "milk", "eggs"
    ]

    # --- Run Function ---
    result = find_frequent_items(monthly_purchases, threshold=3)

    # --- Output JSON ---
    print(json.dumps(result, indent=4))