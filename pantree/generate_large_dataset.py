#!/usr/bin/env python3
"""
Generate large-scale fictional customer receipt dataset.
Supports generating 100,000+ customers across 10 archetypes.
"""

import json
import random
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import time


# Define 10 customer archetypes (expanded from 4)
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
    },
    "vegan_vegetarian": {
        "description": "Vegan/vegetarian focused, plant-based proteins, organic produce",
        "avg_items_per_trip": (18, 28),
        "trip_frequency_days": (7, 10),
        "preferences": {
            "produce": 0.40,
            "protein": 0.05,
            "dairy": 0.10,
            "grains": 0.20,
            "snacks": 0.10,
            "beverages": 0.10,
            "pantry": 0.05
        }
    },
    "senior_couple": {
        "description": "Senior couple, traditional meals, regular schedule, moderate quantities",
        "avg_items_per_trip": (18, 28),
        "trip_frequency_days": (7, 10),
        "preferences": {
            "produce": 0.20,
            "protein": 0.20,
            "dairy": 0.15,
            "grains": 0.15,
            "snacks": 0.05,
            "beverages": 0.15,
            "pantry": 0.10
        }
    },
    "college_student": {
        "description": "College student, cheap meals, instant foods, budget-focused",
        "avg_items_per_trip": (8, 15),
        "trip_frequency_days": (10, 14),
        "preferences": {
            "produce": 0.10,
            "protein": 0.15,
            "dairy": 0.15,
            "grains": 0.20,
            "snacks": 0.20,
            "beverages": 0.10,
            "pantry": 0.10
        }
    },
    "gourmet_foodie": {
        "description": "Gourmet foodie, specialty items, premium ingredients, experimental cooking",
        "avg_items_per_trip": (15, 25),
        "trip_frequency_days": (7, 10),
        "preferences": {
            "produce": 0.25,
            "protein": 0.30,
            "dairy": 0.15,
            "grains": 0.10,
            "snacks": 0.05,
            "beverages": 0.10,
            "pantry": 0.05
        }
    },
    "meal_prepper": {
        "description": "Meal prepper, bulk purchases, container-focused, organized shopping",
        "avg_items_per_trip": (25, 40),
        "trip_frequency_days": (14, 21),
        "preferences": {
            "produce": 0.25,
            "protein": 0.30,
            "dairy": 0.15,
            "grains": 0.15,
            "snacks": 0.05,
            "beverages": 0.05,
            "pantry": 0.05
        }
    },
    "convenience_shopper": {
        "description": "Convenience shopper, ready-made meals, quick shopping trips",
        "avg_items_per_trip": (8, 15),
        "trip_frequency_days": (3, 5),
        "preferences": {
            "produce": 0.10,
            "protein": 0.20,
            "dairy": 0.15,
            "grains": 0.10,
            "snacks": 0.20,
            "beverages": 0.15,
            "pantry": 0.10
        }
    }
}


# Comprehensive grocery items database (same as before)
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


# First and last names for customer generation
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Barbara", "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Andrew", "Emily", "Paul", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Melissa", "George", "Deborah",
    "Timothy", "Stephanie", "Ronald", "Dorothy", "Edward", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Raymond", "Christine", "Frank", "Debra",
    "Gregory", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Raymond", "Catherine",
    "Jack", "Maria", "Dennis", "Heather", "Jerry", "Diane", "Tyler", "Ruth"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey",
    "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson",
    "Watson", "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza",
    "Ruiz", "Hughes", "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers"
]


def generate_customer_name():
    """Generate a random customer name."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


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
        category_counts[category] = max(1, count)

    # Adjust to match total
    total_assigned = sum(category_counts.values())
    diff = num_items - total_assigned
    if diff > 0:
        for _ in range(diff):
            category = random.choice(list(category_counts.keys()))
            category_counts[category] += 1
    elif diff < 0:
        for _ in range(abs(diff)):
            max_cat = max(category_counts.items(), key=lambda x: x[1])
            if max_cat[1] > 1:
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


def generate_receipt(customer_id, customer_name, archetype, trip_number, base_date):
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

    # Create receipt (compact version for large datasets)
    receipt = {
        "store": "Safeway",
        "customer_id": customer_id,
        "customer_name": customer_name,
        "archetype": archetype,
        "order_number": f"{random.randint(100000000, 999999999)}",
        "pickup_date": receipt_date.strftime("%Y-%m-%d"),
        "items": receipt_items,
        "subtotal": subtotal,
        "total": total,
        "savings": total_savings
    }

    return receipt


def generate_customer_batch(start_idx, batch_size, num_receipts, output_dir, base_date):
    """Generate a batch of customers with their receipts."""

    archetype_list = list(ARCHETYPES.keys())
    batch_data = []

    for i in range(batch_size):
        customer_idx = start_idx + i
        customer_id = f"customer_{customer_idx:06d}"
        customer_name = generate_customer_name()

        # Assign archetype (evenly distributed)
        archetype = archetype_list[customer_idx % len(archetype_list)]

        # Generate receipts for this customer
        receipts = []
        for trip_num in range(num_receipts):
            receipt = generate_receipt(customer_id, customer_name, archetype, trip_num, base_date)
            receipts.append(receipt)

        # Calculate customer summary
        total_spent = sum(r["total"] for r in receipts)
        total_savings = sum(r["savings"] for r in receipts)
        total_items = sum(len(r["items"]) for r in receipts)

        customer_data = {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "archetype": archetype,
            "total_receipts": len(receipts),
            "total_spent": round(total_spent, 2),
            "total_savings": round(total_savings, 2),
            "total_items": total_items,
            "receipts": receipts
        }

        batch_data.append(customer_data)

    return batch_data


def save_batch_to_file(batch_data, batch_num, output_dir):
    """Save a batch of customer data to a single JSON file."""
    batch_file = output_dir / f"batch_{batch_num:05d}.json"

    with open(batch_file, 'w', encoding='utf-8') as f:
        json.dump(batch_data, f, indent=2, ensure_ascii=False)

    return batch_file


def generate_large_dataset(
    num_customers=100000,
    num_receipts=17,
    batch_size=1000,
    output_dir="large_dataset"
):
    """Generate large-scale customer receipt dataset."""

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    base_date = datetime.now() - timedelta(days=180)

    print("="*70)
    print(f"GENERATING LARGE DATASET")
    print("="*70)
    print(f"Total customers: {num_customers:,}")
    print(f"Receipts per customer: {num_receipts}")
    print(f"Total receipts: {num_customers * num_receipts:,}")
    print(f"Batch size: {batch_size}")
    print(f"Total batches: {num_customers // batch_size}")
    print(f"Output directory: {output_dir}")
    print("="*70)
    print()

    num_batches = num_customers // batch_size
    archetype_counts = defaultdict(int)
    total_spent = 0.0
    total_savings = 0.0
    total_items = 0

    start_time = time.time()

    for batch_num in range(num_batches):
        batch_start_idx = batch_num * batch_size

        # Generate batch
        batch_data = generate_customer_batch(
            batch_start_idx,
            batch_size,
            num_receipts,
            output_path,
            base_date
        )

        # Save batch
        batch_file = save_batch_to_file(batch_data, batch_num, output_path)

        # Update statistics
        for customer in batch_data:
            archetype_counts[customer["archetype"]] += 1
            total_spent += customer["total_spent"]
            total_savings += customer["total_savings"]
            total_items += customer["total_items"]

        # Progress report
        elapsed = time.time() - start_time
        customers_processed = (batch_num + 1) * batch_size
        rate = customers_processed / elapsed
        remaining = (num_customers - customers_processed) / rate if rate > 0 else 0

        print(f"Batch {batch_num + 1}/{num_batches} complete | "
              f"Customers: {customers_processed:,}/{num_customers:,} | "
              f"Rate: {rate:.0f} cust/sec | "
              f"ETA: {remaining/60:.1f} min")

    # Generate summary
    summary = {
        "generation_date": datetime.now().isoformat(),
        "total_customers": num_customers,
        "receipts_per_customer": num_receipts,
        "total_receipts": num_customers * num_receipts,
        "total_batches": num_batches,
        "batch_size": batch_size,
        "archetypes": dict(archetype_counts),
        "statistics": {
            "total_spent": round(total_spent, 2),
            "total_savings": round(total_savings, 2),
            "total_items": total_items,
            "avg_spent_per_customer": round(total_spent / num_customers, 2),
            "avg_items_per_receipt": round(total_items / (num_customers * num_receipts), 1)
        },
        "generation_time_seconds": round(time.time() - start_time, 2)
    }

    # Save summary
    with open(output_path / "dataset_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print()
    print("="*70)
    print("GENERATION COMPLETE!")
    print("="*70)
    print(f"Total time: {summary['generation_time_seconds'] / 60:.1f} minutes")
    print(f"Total customers: {num_customers:,}")
    print(f"Total receipts: {num_customers * num_receipts:,}")
    print(f"Total spent: ${total_spent:,.2f}")
    print(f"Total savings: ${total_savings:,.2f}")
    print()
    print("Archetype distribution:")
    for archetype, count in sorted(archetype_counts.items()):
        print(f"  {archetype}: {count:,} customers ({count/num_customers*100:.1f}%)")
    print("="*70)


def main():
    """Main function with command line argument handling."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate large-scale fictional customer receipt dataset"
    )
    parser.add_argument(
        "--customers",
        type=int,
        default=100000,
        help="Number of customers to generate (default: 100000)"
    )
    parser.add_argument(
        "--receipts",
        type=int,
        default=17,
        help="Number of receipts per customer (default: 17)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for processing (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="large_dataset",
        help="Output directory (default: large_dataset)"
    )

    args = parser.parse_args()

    generate_large_dataset(
        num_customers=args.customers,
        num_receipts=args.receipts,
        batch_size=args.batch_size,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
