# Large-Scale Receipt Dataset Generator

## Overview
This toolkit can generate 100,000+ fictional customer receipt datasets with 10 distinct shopping archetypes. The system is optimized for large-scale generation with batch processing and efficient file storage.

## Quick Start

### Generate 100,000 Customers (Default)
```bash
python3 generate_large_dataset.py
```

This will create:
- 100,000 customers
- 17 receipts per customer (1.7 million total receipts)
- Organized into batches of 1,000 customers each (100 batch files)
- Estimated time: ~3-5 minutes on modern hardware
- Estimated disk space: ~5-7 GB

### Custom Generation Examples

**Generate 1,000 customers (testing):**
```bash
python3 generate_large_dataset.py --customers 1000 --output small_dataset
```

**Generate 500,000 customers with 20 receipts each:**
```bash
python3 generate_large_dataset.py --customers 500000 --receipts 20 --batch-size 5000 --output mega_dataset
```

**Generate 10,000 customers with custom batch size:**
```bash
python3 generate_large_dataset.py --customers 10000 --batch-size 500 --output medium_dataset
```

## Command Line Options

```
--customers NUM      Number of customers to generate (default: 100000)
--receipts NUM       Number of receipts per customer (default: 17)
--batch-size NUM     Number of customers per batch file (default: 1000)
--output DIR         Output directory name (default: large_dataset)
```

## 10 Customer Archetypes

The system generates customers across 10 distinct shopping archetypes with different behaviors:

### 1. **Health Conscious**
- Focus: Organic foods, fresh produce, lean proteins
- Items per trip: 15-25
- Shopping frequency: Every 7-10 days
- Category preferences: Produce (30%), Protein (25%), Dairy (15%)

### 2. **Busy Family**
- Focus: Bulk purchases, snacks, convenience items
- Items per trip: 30-50
- Shopping frequency: Every 10-14 days
- Category preferences: Snacks (20%), Protein (20%), Produce (15%)

### 3. **Budget Conscious**
- Focus: Store brands, staples, value items
- Items per trip: 20-30
- Shopping frequency: Every 10-14 days
- Category preferences: Balanced across all categories

### 4. **Single Professional**
- Focus: Convenience foods, smaller quantities
- Items per trip: 10-18
- Shopping frequency: Every 5-8 days
- Category preferences: Protein (25%), Snacks (15%)

### 5. **Vegan/Vegetarian**
- Focus: Plant-based proteins, organic produce
- Items per trip: 18-28
- Shopping frequency: Every 7-10 days
- Category preferences: Produce (40%), Grains (20%)

### 6. **Senior Couple**
- Focus: Traditional meals, regular schedule, moderate quantities
- Items per trip: 18-28
- Shopping frequency: Every 7-10 days
- Category preferences: Balanced protein (20%), produce (20%)

### 7. **College Student**
- Focus: Cheap meals, instant foods, budget-focused
- Items per trip: 8-15
- Shopping frequency: Every 10-14 days
- Category preferences: Grains (20%), Snacks (20%)

### 8. **Gourmet Foodie**
- Focus: Specialty items, premium ingredients
- Items per trip: 15-25
- Shopping frequency: Every 7-10 days
- Category preferences: Protein (30%), Produce (25%)

### 9. **Meal Prepper**
- Focus: Bulk purchases, organized shopping
- Items per trip: 25-40
- Shopping frequency: Every 14-21 days
- Category preferences: Protein (30%), Produce (25%)

### 10. **Convenience Shopper**
- Focus: Ready-made meals, quick trips
- Items per trip: 8-15
- Shopping frequency: Every 3-5 days
- Category preferences: Snacks (20%), Protein (20%)

## Output Structure

### File Organization
```
large_dataset/
├── dataset_summary.json          # Overall statistics
├── batch_00000.json              # First 1000 customers
├── batch_00001.json              # Next 1000 customers
├── batch_00002.json
└── ...
```

### Batch File Format
Each batch file contains an array of customer objects:

```json
[
  {
    "customer_id": "customer_000000",
    "customer_name": "John Smith",
    "archetype": "health_conscious",
    "total_receipts": 17,
    "total_spent": 3245.67,
    "total_savings": 521.34,
    "total_items": 345,
    "receipts": [
      {
        "store": "Safeway",
        "customer_id": "customer_000000",
        "customer_name": "John Smith",
        "archetype": "health_conscious",
        "order_number": "123456789",
        "pickup_date": "2025-04-30",
        "items": [
          {
            "quantity": 2,
            "name": "Organic Avocados - 4 Count",
            "price": 14.50
          }
        ],
        "subtotal": 245.67,
        "total": 234.56,
        "savings": 35.20
      }
    ]
  }
]
```

### Summary File Format
```json
{
  "generation_date": "2025-10-26T14:28:46.222656",
  "total_customers": 100000,
  "receipts_per_customer": 17,
  "total_receipts": 1700000,
  "total_batches": 100,
  "batch_size": 1000,
  "archetypes": {
    "health_conscious": 10000,
    "busy_family": 10000,
    ...
  },
  "statistics": {
    "total_spent": 347016980.00,
    "total_savings": 56878160.00,
    "total_items": 36499000,
    "avg_spent_per_customer": 3470.17,
    "avg_items_per_receipt": 21.5
  },
  "generation_time_seconds": 180.5
}
```

## Reading and Analyzing Data

### View Dataset Summary
```bash
python3 read_large_dataset.py large_dataset --summary
```

### Find Specific Customer
```bash
python3 read_large_dataset.py large_dataset --customer customer_000123
```

### Search by Archetype
```bash
python3 read_large_dataset.py large_dataset --archetype health_conscious --limit 20
```

### View Batch Contents
```bash
python3 read_large_dataset.py large_dataset --batch 5
```

## Python API Usage

### Load Dataset Summary
```python
import json
from pathlib import Path

with open('large_dataset/dataset_summary.json') as f:
    summary = json.load(f)

print(f"Total customers: {summary['total_customers']:,}")
print(f"Total spent: ${summary['statistics']['total_spent']:,.2f}")
```

### Iterate Through All Customers
```python
import json
from pathlib import Path

dataset_dir = Path('large_dataset')

for batch_file in sorted(dataset_dir.glob('batch_*.json')):
    with open(batch_file) as f:
        customers = json.load(f)

    for customer in customers:
        # Process each customer
        print(f"{customer['customer_id']}: {customer['customer_name']}")
```

### Filter Customers by Criteria
```python
import json
from pathlib import Path

dataset_dir = Path('large_dataset')
high_spenders = []

for batch_file in sorted(dataset_dir.glob('batch_*.json')):
    with open(batch_file) as f:
        customers = json.load(f)

    for customer in customers:
        if customer['total_spent'] > 5000:
            high_spenders.append(customer)

print(f"Found {len(high_spenders)} customers who spent over $5000")
```

### Analyze Shopping Patterns
```python
import json
from pathlib import Path
from collections import defaultdict

dataset_dir = Path('large_dataset')
archetype_stats = defaultdict(lambda: {'count': 0, 'total_spent': 0})

for batch_file in sorted(dataset_dir.glob('batch_*.json')):
    with open(batch_file) as f:
        customers = json.load(f)

    for customer in customers:
        arch = customer['archetype']
        archetype_stats[arch]['count'] += 1
        archetype_stats[arch]['total_spent'] += customer['total_spent']

for archetype, stats in archetype_stats.items():
    avg = stats['total_spent'] / stats['count']
    print(f"{archetype}: ${avg:.2f} avg spent")
```

## Performance Characteristics

### Generation Speed
- **100 customers**: < 1 second
- **1,000 customers**: ~2 seconds
- **10,000 customers**: ~20 seconds
- **100,000 customers**: ~3-5 minutes
- **1,000,000 customers**: ~30-50 minutes

### Memory Usage
- Batch processing keeps memory usage constant (~50-100 MB)
- Only one batch is held in memory at a time
- Safe for generating millions of customers

### Disk Space
- **Per customer**: ~50-70 KB (including all 17 receipts)
- **100,000 customers**: ~5-7 GB
- **1,000,000 customers**: ~50-70 GB

### File Organization
- Batch size of 1,000 creates manageable file sizes (~50 MB per batch)
- Easy to distribute or process in parallel
- Can be loaded into databases or data warehouses

## Data Characteristics

### Realistic Patterns
- Shopping frequency varies by archetype
- Date spacing includes realistic variations
- Item quantities follow natural distributions (70% qty=1, 25% qty=2, etc.)
- Prices vary within realistic ranges
- Savings percentage varies between 5-25%

### Product Categories
- **7 main categories**: Produce, Protein, Dairy, Grains, Snacks, Beverages, Pantry
- **~100 unique products** across all categories
- **Frequency split**: 70% frequent items, 30% occasional items
- All items are realistic grocery store products

### Customer Distribution
- Archetypes evenly distributed (10% each)
- Names generated from common first and last name lists
- Customer IDs sequential with zero-padding for sorting

## Use Cases

This dataset is ideal for:

1. **Machine Learning Training**
   - Customer segmentation models
   - Purchase prediction algorithms
   - Recommendation systems
   - Demand forecasting

2. **Data Science Projects**
   - Exploratory data analysis
   - Pattern recognition
   - Time series analysis
   - Basket analysis

3. **System Testing**
   - Database performance testing
   - ETL pipeline testing
   - API load testing
   - Analytics platform benchmarking

4. **Education & Research**
   - Teaching data analysis
   - Academic research projects
   - Algorithm development
   - Visualization examples

## Tips for Large-Scale Generation

### For 100,000 customers:
```bash
# Default settings work well
python3 generate_large_dataset.py
```

### For 1,000,000+ customers:
```bash
# Use larger batch size for better performance
python3 generate_large_dataset.py --customers 1000000 --batch-size 5000
```

### Memory-Constrained Systems:
```bash
# Use smaller batch size
python3 generate_large_dataset.py --customers 100000 --batch-size 500
```

### SSD Storage Recommended:
- Generation involves many small writes
- SSD dramatically improves performance
- HDD will work but may be 2-3x slower

## Troubleshooting

### Generation is slow
- Check disk I/O (use `iostat` or similar)
- Ensure sufficient free disk space
- Consider using SSD storage
- Try larger batch sizes

### Out of memory
- Reduce batch size with `--batch-size`
- Close other applications
- Verify system has at least 2GB free RAM

### Disk space issues
- Each 100k customers needs ~5-7 GB
- Check available space with `df -h`
- Consider external storage for large datasets

## Comparing with Ground Truth

The original ground truth receipts are preserved in `ground_truth/receipts_json/` for comparison and validation purposes.

## License & Attribution

This is synthetic data generated for research, development, and testing purposes. All customer names, receipts, and transactions are fictional.
