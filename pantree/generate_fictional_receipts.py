#!/usr/bin/env python3
"""
Generate fictional customer receipts based on archetypes.
"""

import json
import random
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


# Define 4 customer archetypes
ARCHETYPES = {
    "health_conscious": {
        "description": "Health-conscious, shops for organic and fresh foods, meal preps",
        "avg_items_per_trip": (15, 25),
        "trip_frequency_days": (7, 10),
        "preferences": {
            "produce": 0.30,
            "protein": 0.25,
            "dairy": 0.15,
            "grains": 0.10,
            "snacks": 0.05,
            "beverages": 0.10,
            "pantry": 0.05
        }
    },
    "busy_family": {
        "description": "Busy family with kids, buys in bulk, frozen meals, snacks",
        "avg_items_per_trip": (30, 50),
        "trip_frequency_days": (10, 14),
        "preferences": {
            "produce": 0.15,
            "protein": 0.20,
            "dairy": 0.15,
            "grains": 0.10,
            "snacks": 0.20,
            "beverages": 0.10,
            "pantry": 0.10
        }
    },
    "budget_conscious": {
        "description": "Budget-conscious shopper, buys store brands, staples",
        "avg_items_per_trip": (20, 30),
        "trip_frequency_days": (10, 14),
        "preferences": {
            "produce": 0.20,
            "protein": 0.15,
            "dairy": 0.15,
            "grains": 0.15,
            "snacks": 0.10,
            "beverages": 0.15,
            "pantry": 0.10
        }
    },
    "single_professional": {
        "description": "Single professional, convenience foods, smaller quantities",
        "avg_items_per_trip": (10, 18),
        "trip_frequency_days": (5, 8),
        "preferences": {
            "produce": 0.15,
            "protein": 0.25,
            "dairy": 0.15,
            "grains": 0.10,
            "snacks": 0.15,
            "beverages": 0.10,
            "pantry": 0.10
        }
    }
}


# Comprehensive grocery items database organized by category
GROCERY_ITEMS = {
    "produce": {
        "frequent": [
            ("Bananas - 1 Lb", 0.69, 1.29),
            ("White Onion", 1.29, 2.49),
            ("Russet Potatoes - 5 Lb", 3.99, 5.99),
            ("Roma Tomatoes - 1 Lb", 1.49, 2.99),
            ("Green Bell Pepper", 0.99, 1.99),
            ("Carrots - 2 Lb Bag", 1.99, 3.49),
            ("Celery Bunch", 1.49, 2.99),
            ("Lettuce Iceberg", 1.99, 3.49),
            ("Garlic Bulb", 0.79, 1.49),
            ("Fresh Spinach - 10 Oz", 2.99, 4.99),
        ],
        "occasional": [
            ("Organic Avocados - 4 Count", 5.99, 8.99),
            ("Fresh Strawberries - 1 Lb", 3.99, 6.99),
            ("Fresh Blueberries - 6 Oz", 3.49, 5.99),
            ("Seedless Cucumbers - 2 Count", 2.99, 4.49),
            ("Sweet Mini Peppers - 1 Lb", 3.99, 5.49),
            ("Fresh Broccoli Crowns", 2.49, 3.99),
            ("Organic Baby Carrots - 1 Lb", 2.49, 3.99),
            ("Fresh Cilantro Bunch", 0.99, 1.99),
            ("Green Grapes - 2 Lb", 4.99, 7.99),
            ("Fresh Asparagus - 1 Lb", 3.99, 6.99),
            ("Sweet Potatoes - 3 Lb", 3.99, 5.99),
            ("Organic Kale Bunch", 2.49, 3.99),
        ]
    },
    "protein": {
        "frequent": [
            ("80% Lean 20% Fat Ground Beef Value Pack - 3 Lb", 12.99, 18.99),
            ("Boneless Skinless Chicken Breasts Value Pack - 3.5 Lb", 18.99, 25.99),
            ("Large Eggs Grade A - 18 Count", 3.99, 6.99),
            ("Chicken Thighs Bone-In - 3 Lb", 9.99, 14.99),
        ],
        "occasional": [
            ("96% Lean 4% Fat Ground Beef - 1.35 Lb", 15.99, 19.99),
            ("Pork Loin Chops Value Pack - 4 Lb", 11.99, 16.99),
            ("Salmon Fillets Fresh - 1 Lb", 12.99, 18.99),
            ("All Natural Chicken Tenders - 1 Lb", 7.99, 10.99),
            ("Turkey Breast Sliced Deli - 1 Lb", 8.99, 12.99),
            ("Beef Sirloin Steak - 2 Lb", 15.99, 22.99),
            ("Pork Sausage Links - 1 Lb", 5.99, 8.99),
            ("Bacon Thick Cut - 16 Oz", 7.99, 11.99),
            ("Ham Deli Honey - 1 Lb", 7.99, 10.99),
            ("Tilapia Fillets Frozen - 2 Lb", 9.99, 13.99),
        ]
    },
    "dairy": {
        "frequent": [
            ("Whole Milk - 1 Gallon", 3.99, 5.99),
            ("Shredded Cheese Mozzarella - 8 Oz", 3.49, 5.49),
            ("Butter Salted - 16 Oz", 4.99, 7.49),
            ("Sour Cream - 16 Oz", 2.99, 4.49),
            ("Cream Cheese - 8 Oz", 2.49, 3.99),
        ],
        "occasional": [
            ("Greek Yogurt Plain - 32 Oz", 4.99, 7.49),
            ("Cheddar Cheese Block Sharp - 8 Oz", 4.49, 6.99),
            ("Cottage Cheese - 16 Oz", 3.49, 5.49),
            ("String Cheese Mozzarella - 12 Oz", 4.99, 6.99),
            ("Heavy Whipping Cream - 16 Oz", 3.99, 5.99),
            ("Yogurt Cups Variety Pack - 6 Count", 4.49, 6.49),
            ("Parmesan Cheese Grated - 8 Oz", 5.49, 7.99),
            ("Half and Half - 32 Oz", 3.99, 5.49),
        ]
    },
    "grains": {
        "frequent": [
            ("White Bread Sandwich - 24 Oz", 2.99, 4.99),
            ("Wheat Bread Whole Grain - 24 Oz", 3.49, 5.49),
            ("Flour All Purpose - 5 Lb", 3.99, 5.99),
            ("White Rice Long Grain - 5 Lb", 4.99, 7.49),
        ],
        "occasional": [
            ("Pasta Penne - 16 Oz", 1.49, 2.99),
            ("Pasta Spaghetti - 16 Oz", 1.49, 2.99),
            ("Tortillas Flour - 20 Count", 3.99, 5.99),
            ("English Muffins - 12 Oz", 2.99, 4.49),
            ("Bagels Plain - 6 Count", 3.49, 5.49),
            ("Dinner Rolls - 12 Count", 3.49, 4.99),
            ("Brown Rice - 2 Lb", 4.49, 6.99),
            ("Quinoa Organic - 16 Oz", 5.99, 8.99),
            ("Oatmeal Quick Oats - 42 Oz", 4.49, 6.49),
        ]
    },
    "snacks": {
        "frequent": [
            ("Potato Chips Classic - 10 Oz", 3.99, 5.99),
            ("Crackers Saltine - 16 Oz", 3.49, 4.99),
            ("Granola Bars Variety Pack - 12 Count", 4.99, 7.49),
        ],
        "occasional": [
            ("Cookies Chocolate Chip - 13 Oz", 4.49, 6.49),
            ("Pretzels - 16 Oz", 3.49, 4.99),
            ("Trail Mix - 26 Oz", 6.99, 9.99),
            ("Popcorn Microwave Butter - 6 Count", 3.99, 5.49),
            ("Tortilla Chips - 13 Oz", 3.99, 5.49),
            ("Candy Chocolate Bar Variety - 18 Oz", 8.99, 12.99),
            ("Nuts Mixed Roasted - 16 Oz", 7.99, 11.99),
            ("Cheese Crackers - 12 Oz", 3.99, 5.49),
            ("Fruit Snacks - 22 Count", 5.99, 8.49),
            ("Rice Cakes - 9 Oz", 3.49, 4.99),
        ]
    },
    "beverages": {
        "frequent": [
            ("Coca-Cola 12 Pack Cans - 12 Fl. Oz.", 5.99, 7.99),
            ("Bottled Water - 24 Pack", 3.49, 5.99),
            ("Orange Juice - 64 Fl. Oz.", 4.99, 7.49),
        ],
        "occasional": [
            ("Diet Coke 12 Pack Cans - 12 Fl. Oz.", 5.99, 7.99),
            ("Coffee Ground Medium Roast - 30 Oz", 8.99, 12.99),
            ("Apple Juice - 64 Fl. Oz.", 3.99, 5.99),
            ("Sports Drink Variety - 8 Pack", 6.99, 9.49),
            ("Iced Tea Lemon - 64 Fl. Oz.", 2.99, 4.49),
            ("Energy Drink - 4 Pack", 6.99, 9.99),
            ("Sparkling Water Variety - 12 Pack", 5.99, 8.49),
            ("Almond Milk Unsweetened - 64 Fl. Oz.", 3.99, 5.99),
            ("Cranberry Juice - 64 Fl. Oz.", 4.99, 6.99),
        ]
    },
    "pantry": {
        "frequent": [
            ("Tomato Sauce - 24 Oz", 1.99, 3.49),
            ("Vegetable Oil - 48 Fl. Oz.", 4.99, 7.49),
            ("Sugar Granulated - 4 Lb", 3.49, 4.99),
            ("Salt Iodized - 26 Oz", 1.49, 2.49),
        ],
        "occasional": [
            ("Peanut Butter Creamy - 40 Oz", 5.99, 8.99),
            ("Strawberry Jam - 18 Oz", 3.99, 5.99),
            ("Honey - 24 Oz", 6.99, 9.99),
            ("Ketchup - 20 Oz", 3.49, 4.99),
            ("Mustard Yellow - 20 Oz", 2.49, 3.99),
            ("Mayonnaise - 30 Oz", 4.99, 6.99),
            ("Olive Oil Extra Virgin - 25 Fl. Oz.", 8.99, 12.99),
            ("Soy Sauce - 15 Fl. Oz.", 3.49, 4.99),
            ("Vinegar White - 32 Fl. Oz.", 2.49, 3.99),
            ("Canned Beans Black - 15 Oz", 1.29, 2.49),
            ("Canned Tomatoes Diced - 14.5 Oz", 1.49, 2.49),
            ("Chicken Broth - 32 Oz", 2.49, 3.99),
            ("Cereal Corn Flakes - 18 Oz", 3.99, 5.49),
            ("Pancake Mix - 32 Oz", 3.99, 5.49),
            ("Maple Syrup - 24 Oz", 6.99, 9.99),
        ]
    }
}


# Customer profiles (10 customers across 4 archetypes)
CUSTOMERS = [
    {"id": "customer_01", "name": "Sarah Mitchell", "archetype": "health_conscious"},
    {"id": "customer_02", "name": "David Park", "archetype": "health_conscious"},
    {"id": "customer_03", "name": "Jennifer Rodriguez", "archetype": "busy_family"},
    {"id": "customer_04", "name": "Michael Chen", "archetype": "busy_family"},
    {"id": "customer_05", "name": "Lisa Thompson", "archetype": "busy_family"},
    {"id": "customer_06", "name": "Robert Martinez", "archetype": "budget_conscious"},
    {"id": "customer_07", "name": "Amanda Johnson", "archetype": "budget_conscious"},
    {"id": "customer_08", "name": "Chris Anderson", "archetype": "single_professional"},
    {"id": "customer_09", "name": "Emily White", "archetype": "single_professional"},
    {"id": "customer_10", "name": "James Taylor", "archetype": "budget_conscious"},
]


def generate_receipt_date(base_date, trip_number, avg_frequency_days):
    """Generate a receipt date based on shopping frequency."""
    days_variation = random.randint(-2, 3)
    days_offset = (trip_number * avg_frequency_days) + days_variation
    return base_date + timedelta(days=days_offset)


def select_items(archetype_prefs, num_items):
    """Select items based on archetype preferences."""
    items = []

    # Determine how many items from each category
    category_counts = {}
    for category, preference in archetype_prefs.items():
        count = int(num_items * preference)
        category_counts[category] = max(1, count)  # At least 1 item per category

    # Adjust to match total
    total_assigned = sum(category_counts.values())
    diff = num_items - total_assigned
    if diff > 0:
        # Add remaining items to random categories
        for _ in range(diff):
            category = random.choice(list(category_counts.keys()))
            category_counts[category] += 1
    elif diff < 0:
        # Remove excess items from categories with most items
        for _ in range(abs(diff)):
            max_cat = max(category_counts.items(), key=lambda x: x[1])
            category_counts[max_cat[0]] -= 1

    # Select items from each category
    for category, count in category_counts.items():
        if category in GROCERY_ITEMS:
            category_items = GROCERY_ITEMS[category]

            # Mix of frequent and occasional items (70/30 split)
            freq_count = int(count * 0.7)
            occ_count = count - freq_count

            # Select frequent items
            if freq_count > 0:
                freq_items = random.choices(
                    category_items["frequent"],
                    k=min(freq_count, len(category_items["frequent"]))
                )
                items.extend(freq_items)

            # Select occasional items
            if occ_count > 0:
                occ_items = random.choices(
                    category_items["occasional"],
                    k=min(occ_count, len(category_items["occasional"]))
                )
                items.extend(occ_items)

    return items


def generate_receipt(customer, archetype, trip_number, base_date):
    """Generate a single receipt for a customer."""
    arch_data = ARCHETYPES[archetype]

    # Determine number of items for this trip
    min_items, max_items = arch_data["avg_items_per_trip"]
    num_items = random.randint(min_items, max_items)

    # Generate receipt date
    avg_freq = sum(arch_data["trip_frequency_days"]) // 2
    receipt_date = generate_receipt_date(base_date, trip_number, avg_freq)

    # Select items
    selected_items = select_items(arch_data["preferences"], num_items)

    # Build receipt items with quantities and prices
    receipt_items = []
    subtotal = 0.0

    for item_name, min_price, max_price in selected_items:
        quantity = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]

        # Price varies within range
        base_price = random.uniform(min_price, max_price)
        total_price = round(base_price * quantity, 2)

        receipt_items.append({
            "quantity": quantity,
            "name": item_name,
            "price": total_price
        })

        subtotal += total_price

    # Calculate savings (5-25% of subtotal)
    savings_pct = random.uniform(0.05, 0.25)
    total_savings = round(subtotal * savings_pct, 2)
    member_savings = round(total_savings * random.uniform(0.7, 0.95), 2)
    safeway_savings = round(total_savings - member_savings, 2)

    # Calculate final totals
    subtotal_after_savings = round(subtotal - total_savings, 2)
    taxes = round(subtotal_after_savings * random.uniform(0.06, 0.09), 2)
    bag_fee = round(random.choice([0.0, 0.25, 0.50, 0.75]), 2)
    total = round(subtotal_after_savings + taxes + bag_fee, 2)

    # Create receipt
    receipt = {
        "store": "Safeway",
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "archetype": archetype,
        "order_number": f"{random.randint(100000000, 999999999)}",
        "subject": receipt_date.strftime("%m/%d/%y Safeway"),
        "email_date": receipt_date.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        "pickup_date": receipt_date.strftime("%A, %B %d, %Y"),
        "pickup_time": random.choice([
            "8:00 AM - 4:00 PM",
            "10:00 AM - 6:00 PM",
            "12:00 PM - 8:00 PM",
            "2:00 PM - 10:00 PM"
        ]),
        "pickup_address": "2720 41st Ave, Soquel, CA 95073",
        "items": receipt_items,
        "subtotal": subtotal,
        "total": total,
        "taxes_and_fees": round(taxes + bag_fee, 2),
        "savings": {
            "total": total_savings,
            "member_price": member_savings,
            "safeway_for_u": safeway_savings
        },
        "payment_method": f"Card ending in {random.randint(1000, 9999)}"
    }

    return receipt


def main():
    output_base = "fictional_customers"
    Path(output_base).mkdir(exist_ok=True)

    # Base date for receipt generation (start 6 months ago)
    base_date = datetime.now() - timedelta(days=180)

    print(f"Generating receipts for {len(CUSTOMERS)} customers...\n")

    for customer in CUSTOMERS:
        customer_id = customer["id"]
        customer_name = customer["name"]
        archetype = customer["archetype"]

        print(f"Generating receipts for {customer_name} ({archetype})...")

        # Create customer directory
        customer_dir = Path(output_base) / customer_id
        customer_dir.mkdir(exist_ok=True)

        # Generate 17 receipts
        receipts = []
        for trip_num in range(17):
            receipt = generate_receipt(customer, archetype, trip_num, base_date)
            receipts.append(receipt)

            # Save individual receipt
            filename = f"receipt_{trip_num + 1:03d}_{receipt['subject'].replace('/', '_')}.json"
            filepath = customer_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(receipt, f, indent=2, ensure_ascii=False)

        # Save customer profile summary
        profile = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "archetype": archetype,
            "archetype_description": ARCHETYPES[archetype]["description"],
            "total_receipts": len(receipts),
            "total_spent": sum(r["total"] for r in receipts),
            "total_savings": sum(r["savings"]["total"] for r in receipts),
            "avg_items_per_trip": sum(len(r["items"]) for r in receipts) / len(receipts),
            "date_range": {
                "first": receipts[0]["pickup_date"],
                "last": receipts[-1]["pickup_date"]
            }
        }

        with open(customer_dir / "customer_profile.json", 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Generated {len(receipts)} receipts")
        print(f"  ✓ Total spent: ${profile['total_spent']:.2f}")
        print(f"  ✓ Avg items per trip: {profile['avg_items_per_trip']:.1f}\n")

    # Create summary of all customers
    summary = {
        "total_customers": len(CUSTOMERS),
        "archetypes": {
            arch: sum(1 for c in CUSTOMERS if c["archetype"] == arch)
            for arch in set(c["archetype"] for c in CUSTOMERS)
        },
        "customers": CUSTOMERS
    }

    with open(Path(output_base) / "dataset_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n" + "="*60)
    print("Dataset generation complete!")
    print(f"Total customers: {len(CUSTOMERS)}")
    print(f"Total receipts: {len(CUSTOMERS) * 17}")
    print("\nArchetype distribution:")
    for arch, count in summary["archetypes"].items():
        print(f"  {arch}: {count} customers")
    print("="*60)


if __name__ == "__main__":
    main()
