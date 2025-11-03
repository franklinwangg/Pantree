# Receipt Dataset Usage Guide

## Quick Reference

### What You Have

1. **Ground Truth Data** (17 real receipts)
   - Location: `ground_truth/receipts_json/`
   - Parsed from: `receipts.mbox`

2. **Small Fictional Dataset** (10 customers)
   - Location: `fictional_customers/`
   - 10 customers across 4 archetypes
   - 17 receipts per customer (170 total)

3. **Large-Scale Generator** (100k+ customers)
   - Script: `generate_large_dataset.py`
   - Supports 10 archetypes
   - Can generate millions of customers

## Generation Commands

### Generate 100,000 Customers (Recommended for Production)

```bash
python3 generate_large_dataset.py
```

**Output:**
- Directory: `large_dataset/`
- 100,000 customers
- 1.7 million receipts
- 10 archetypes evenly distributed
- ~5-7 GB disk space
- ~3-5 minutes generation time

### Test with Smaller Dataset First

```bash
# Generate 1,000 customers (good for testing)
python3 generate_large_dataset.py --customers 1000 --output test_1k

# Generate 10,000 customers (medium test)
python3 generate_large_dataset.py --customers 10000 --output test_10k
```

### Generate Even Larger Datasets

```bash
# 500,000 customers
python3 generate_large_dataset.py --customers 500000 --output dataset_500k

# 1 million customers
python3 generate_large_dataset.py --customers 1000000 --batch-size 5000 --output dataset_1m
```

## Analyzing Generated Data

### View Summary Statistics
```bash
python3 read_large_dataset.py large_dataset --summary
```

### Find Specific Customer
```bash
python3 read_large_dataset.py large_dataset --customer customer_000123
```

### Search by Shopping Type
```bash
# Find health conscious shoppers
python3 read_large_dataset.py large_dataset --archetype health_conscious --limit 10

# Find busy families
python3 read_large_dataset.py large_dataset --archetype busy_family --limit 10

# See all 10 archetypes in LARGE_DATASET_README.md
```

## Available Scripts

### 1. `parse_receipts.py`
Original script to parse mbox files into JSON receipts.
```bash
python3 parse_receipts.py
```

### 2. `generate_fictional_receipts.py`
Generate small fictional dataset (10 customers, 4 archetypes).
```bash
python3 generate_fictional_receipts.py
```

### 3. `generate_large_dataset.py`
Generate large-scale datasets (100k+ customers, 10 archetypes).
```bash
python3 generate_large_dataset.py --customers 100000
```

### 4. `read_large_dataset.py`
Read and analyze batch-formatted large datasets.
```bash
python3 read_large_dataset.py <dataset_dir> [options]
```

### 5. `validate_dataset.py`
Validate small fictional customer dataset.
```bash
python3 validate_dataset.py
```

## Dataset Comparison

| Feature | Small Dataset | Large Dataset |
|---------|---------------|---------------|
| **Customers** | 10 | 100,000+ |
| **Archetypes** | 4 | 10 |
| **File Format** | Individual JSON files | Batch JSON files |
| **Use Case** | Testing, examples | ML training, production |
| **Disk Space** | ~100 KB | 5-7 GB per 100k |
| **Generation Time** | < 1 second | 3-5 minutes |
| **Organization** | One dir per customer | Batched in single dir |

## Common Workflows

### Workflow 1: Quick Testing
```bash
# Generate small test set
python3 generate_large_dataset.py --customers 100 --output quick_test

# View results
python3 read_large_dataset.py quick_test --summary

# Clean up
rm -rf quick_test
```

### Workflow 2: Production Dataset Generation
```bash
# Generate full dataset
python3 generate_large_dataset.py --customers 100000 --output production_dataset

# Verify generation
python3 read_large_dataset.py production_dataset --summary

# Sample some customers
python3 read_large_dataset.py production_dataset --archetype meal_prepper --limit 5
```

### Workflow 3: Load into Database
```python
import json
from pathlib import Path
import sqlite3

# Create database
conn = sqlite3.connect('receipts.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        customer_name TEXT,
        archetype TEXT,
        total_spent REAL,
        total_savings REAL
    )
''')

cursor.execute('''
    CREATE TABLE receipts (
        receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT,
        pickup_date TEXT,
        total REAL,
        savings REAL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
''')

# Load data from batches
dataset_dir = Path('large_dataset')
for batch_file in sorted(dataset_dir.glob('batch_*.json')):
    with open(batch_file) as f:
        customers = json.load(f)

    for customer in customers:
        # Insert customer
        cursor.execute('''
            INSERT INTO customers VALUES (?, ?, ?, ?, ?)
        ''', (
            customer['customer_id'],
            customer['customer_name'],
            customer['archetype'],
            customer['total_spent'],
            customer['total_savings']
        ))

        # Insert receipts
        for receipt in customer['receipts']:
            cursor.execute('''
                INSERT INTO receipts (customer_id, pickup_date, total, savings)
                VALUES (?, ?, ?, ?)
            ''', (
                customer['customer_id'],
                receipt['pickup_date'],
                receipt['total'],
                receipt['savings']
            ))

conn.commit()
conn.close()
print("Database created successfully!")
```

### Workflow 4: Data Science Analysis
```python
import json
import pandas as pd
from pathlib import Path

# Load all customers into a DataFrame
customers_data = []

dataset_dir = Path('large_dataset')
for batch_file in sorted(dataset_dir.glob('batch_*.json')):
    with open(batch_file) as f:
        customers = json.load(f)

    for customer in customers:
        customers_data.append({
            'customer_id': customer['customer_id'],
            'name': customer['customer_name'],
            'archetype': customer['archetype'],
            'total_spent': customer['total_spent'],
            'total_savings': customer['total_savings'],
            'total_items': customer['total_items'],
            'avg_receipt_value': customer['total_spent'] / customer['total_receipts']
        })

df = pd.DataFrame(customers_data)

# Analyze by archetype
print(df.groupby('archetype')['total_spent'].describe())

# Find high-value customers
high_value = df[df['total_spent'] > df['total_spent'].quantile(0.95)]
print(f"Top 5% customers: {len(high_value)}")
```

## 10 Customer Archetypes

Quick reference for the 10 archetypes:

1. **health_conscious** - Organic foods, fresh produce
2. **busy_family** - Bulk purchases, snacks
3. **budget_conscious** - Store brands, value items
4. **single_professional** - Convenience, smaller quantities
5. **vegan_vegetarian** - Plant-based, organic produce
6. **senior_couple** - Traditional meals, regular schedule
7. **college_student** - Cheap meals, instant foods
8. **gourmet_foodie** - Specialty, premium ingredients
9. **meal_prepper** - Bulk purchases, organized
10. **convenience_shopper** - Ready-made, quick trips

## File Locations

```
pantree/
├── receipts.mbox                      # Original mbox file
├── parse_receipts.py                  # Parse mbox → JSON
├── generate_fictional_receipts.py     # Generate 10 customers (4 archetypes)
├── generate_large_dataset.py          # Generate 100k+ customers (10 archetypes)
├── read_large_dataset.py              # Read batch-format datasets
├── validate_dataset.py                # Validate small dataset
├── DATASET_README.md                  # Small dataset documentation
├── LARGE_DATASET_README.md            # Large dataset documentation
├── USAGE_GUIDE.md                     # This file
├── ground_truth/
│   └── receipts_json/                 # 17 original receipts
└── fictional_customers/               # 10 customers, 4 archetypes
    ├── customer_01/
    ├── customer_02/
    ├── ...
    └── dataset_summary.json
```

## Getting Started Checklist

- [ ] Read this guide
- [ ] Review `LARGE_DATASET_README.md` for detailed documentation
- [ ] Test with small dataset: `python3 generate_large_dataset.py --customers 100 --output test`
- [ ] Verify output: `python3 read_large_dataset.py test --summary`
- [ ] Generate production dataset: `python3 generate_large_dataset.py`
- [ ] Begin your analysis!

## Support & Documentation

- **Small dataset details**: See `DATASET_README.md`
- **Large dataset details**: See `LARGE_DATASET_README.md`
- **Script help**: Run any script with `--help` flag
  ```bash
  python3 generate_large_dataset.py --help
  python3 read_large_dataset.py --help
  ```

## Estimated Resource Requirements

### For 100,000 Customers
- **Time**: 3-5 minutes
- **Disk Space**: 5-7 GB
- **Memory**: 100-200 MB (during generation)
- **CPU**: Any modern processor

### For 1,000,000 Customers
- **Time**: 30-50 minutes
- **Disk Space**: 50-70 GB
- **Memory**: 100-200 MB (batch processing keeps it constant)
- **CPU**: Multi-core recommended for faster generation
