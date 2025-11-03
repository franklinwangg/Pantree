# Receipt Dataset Documentation

## Overview
This dataset contains grocery store receipts organized into ground truth (real) receipts and fictional customer receipts representing 10 customers across 4 distinct shopping archetypes.

## Directory Structure

```
pantree/
├── ground_truth/
│   └── receipts_json/          # 17 original receipts
│       ├── receipt_001_09_13_24 Safeway.json
│       ├── receipt_002_12_16_24 Safeway.json
│       └── ...
├── fictional_customers/
│   ├── customer_01/            # Sarah Mitchell (health_conscious)
│   ├── customer_02/            # David Park (health_conscious)
│   ├── customer_03/            # Jennifer Rodriguez (busy_family)
│   ├── customer_04/            # Michael Chen (busy_family)
│   ├── customer_05/            # Lisa Thompson (busy_family)
│   ├── customer_06/            # Robert Martinez (budget_conscious)
│   ├── customer_07/            # Amanda Johnson (budget_conscious)
│   ├── customer_08/            # Chris Anderson (single_professional)
│   ├── customer_09/            # Emily White (single_professional)
│   ├── customer_10/            # James Taylor (budget_conscious)
│   └── dataset_summary.json
└── generate_fictional_receipts.py
```

## Dataset Statistics

### Ground Truth
- **Total receipts**: 17
- **Total items**: 609
- **Total spent**: $4,885.50
- **Total savings**: $1,659.07
- **Date range**: September 2024 - July 2025

### Fictional Customers
- **Total customers**: 10
- **Receipts per customer**: 17
- **Total receipts**: 170
- **Total items**: ~4,500+
- **Date range**: ~6 months per customer

## Customer Archetypes

### 1. Health Conscious (2 customers)
**Characteristics:**
- Focuses on organic and fresh foods
- Meal preparation oriented
- Higher proportion of produce and lean proteins
- Moderate shopping frequency (every 7-10 days)
- Average items per trip: 15-25

**Customers:**
- Sarah Mitchell (customer_01)
- David Park (customer_02)

**Category Preferences:**
- Produce: 30%
- Protein: 25%
- Dairy: 15%
- Grains: 10%
- Beverages: 10%
- Snacks: 5%
- Pantry: 5%

### 2. Busy Family (3 customers)
**Characteristics:**
- Buys in bulk for family needs
- Higher proportion of snacks and convenience items
- Shops less frequently but buys more items
- Shopping frequency: every 10-14 days
- Average items per trip: 30-50

**Customers:**
- Jennifer Rodriguez (customer_03)
- Michael Chen (customer_04)
- Lisa Thompson (customer_05)

**Category Preferences:**
- Snacks: 20%
- Protein: 20%
- Produce: 15%
- Dairy: 15%
- Grains: 10%
- Beverages: 10%
- Pantry: 10%

### 3. Budget Conscious (3 customers)
**Characteristics:**
- Focuses on value and store brands
- Balanced purchases across categories
- Regular shopping pattern
- Shopping frequency: every 10-14 days
- Average items per trip: 20-30

**Customers:**
- Robert Martinez (customer_06)
- Amanda Johnson (customer_07)
- James Taylor (customer_10)

**Category Preferences:**
- Produce: 20%
- Protein: 15%
- Dairy: 15%
- Grains: 15%
- Beverages: 15%
- Snacks: 10%
- Pantry: 10%

### 4. Single Professional (2 customers)
**Characteristics:**
- Shops frequently with smaller quantities
- Preference for convenience and ready-to-eat items
- Higher protein purchases
- Shopping frequency: every 5-8 days
- Average items per trip: 10-18

**Customers:**
- Chris Anderson (customer_08)
- Emily White (customer_09)

**Category Preferences:**
- Protein: 25%
- Produce: 15%
- Dairy: 15%
- Snacks: 15%
- Grains: 10%
- Beverages: 10%
- Pantry: 10%

## Receipt JSON Format

Each receipt contains the following fields:

```json
{
  "store": "Safeway",
  "customer_id": "customer_01",
  "customer_name": "Sarah Mitchell",
  "archetype": "health_conscious",
  "order_number": "123456789",
  "subject": "04/30/25 Safeway",
  "email_date": "Wed, 30 Apr 2025 14:23:15 +0000",
  "pickup_date": "Wednesday, April 30, 2025",
  "pickup_time": "10:00 AM - 6:00 PM",
  "pickup_address": "2720 41st Ave, Soquel, CA 95073",
  "items": [
    {
      "quantity": 1,
      "name": "White Onion",
      "price": 1.85
    }
  ],
  "subtotal": 167.44,
  "total": 145.67,
  "taxes_and_fees": 8.49,
  "savings": {
    "total": 30.26,
    "member_price": 28.56,
    "safeway_for_u": 1.70
  },
  "payment_method": "Card ending in 9149"
}
```

## Product Categories

The dataset includes items from 7 main categories:

1. **Produce**: Fresh fruits, vegetables, herbs
2. **Protein**: Meat, poultry, fish, eggs
3. **Dairy**: Milk, cheese, yogurt, butter
4. **Grains**: Bread, pasta, rice, cereal
5. **Snacks**: Chips, crackers, cookies, nuts
6. **Beverages**: Soda, juice, coffee, water
7. **Pantry**: Sauces, oils, condiments, canned goods

### Item Frequency Pattern
- **Frequent items** (70%): Staples bought regularly (e.g., milk, bread, bananas)
- **Occasional items** (30%): Items bought less frequently (e.g., specialty items, treats)

## Customer Profiles

Each customer directory contains:
- **17 receipt JSON files**: One for each shopping trip
- **customer_profile.json**: Summary statistics including:
  - Customer ID and name
  - Archetype and description
  - Total receipts
  - Total amount spent
  - Total savings
  - Average items per trip
  - Date range of purchases

## Usage Examples

### Load a customer profile
```python
import json

with open('fictional_customers/customer_01/customer_profile.json') as f:
    profile = json.load(f)
print(f"{profile['customer_name']} - {profile['archetype']}")
print(f"Total spent: ${profile['total_spent']:.2f}")
```

### Analyze shopping patterns
```python
import json
from pathlib import Path

customer_dir = Path('fictional_customers/customer_01')
receipts = []

for receipt_file in customer_dir.glob('receipt_*.json'):
    with open(receipt_file) as f:
        receipts.append(json.load(f))

# Calculate average basket size
avg_items = sum(len(r['items']) for r in receipts) / len(receipts)
print(f"Average items per trip: {avg_items:.1f}")
```

### Compare archetypes
```python
import json
from pathlib import Path
from collections import defaultdict

archetype_spending = defaultdict(list)

for customer_dir in Path('fictional_customers').glob('customer_*'):
    profile_path = customer_dir / 'customer_profile.json'
    with open(profile_path) as f:
        profile = json.load(f)
        archetype_spending[profile['archetype']].append(profile['total_spent'])

for archetype, amounts in archetype_spending.items():
    avg = sum(amounts) / len(amounts)
    print(f"{archetype}: ${avg:.2f} avg per customer")
```

## Data Generation

The fictional receipts were generated using `generate_fictional_receipts.py`, which:
1. Defines 4 distinct customer archetypes with different shopping behaviors
2. Creates a comprehensive grocery item database with realistic prices
3. Generates 17 receipts per customer with appropriate date spacing
4. Varies quantities and item selections based on archetype preferences
5. Calculates realistic totals, taxes, and savings

To regenerate the data:
```bash
python3 generate_fictional_receipts.py
```

## Research Applications

This dataset can be used for:
- **Customer segmentation** analysis
- **Shopping pattern** prediction
- **Recommendation systems** development
- **Demand forecasting** models
- **Basket analysis** studies
- **Customer lifetime value** estimation
- **Promotional effectiveness** analysis

## Notes

- All prices are in USD
- Savings percentages vary between 5-25% of subtotal
- Shopping frequency varies by archetype
- Item quantities typically range from 1-4 per item
- Receipt dates are generated with realistic spacing based on shopping frequency
- All items are realistic grocery store products
