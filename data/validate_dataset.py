#!/usr/bin/env python3
"""
Validate and analyze the generated receipt dataset.
"""

import json
from pathlib import Path
from collections import defaultdict


def validate_dataset():
    """Validate the entire dataset and provide statistics."""

    print("="*70)
    print("DATASET VALIDATION REPORT")
    print("="*70)

    # Validate ground truth
    print("\n1. GROUND TRUTH RECEIPTS")
    print("-" * 70)
    ground_truth_dir = Path("ground_truth/receipts_json")
    gt_receipts = list(ground_truth_dir.glob("*.json"))
    print(f"   Total receipts: {len(gt_receipts)}")

    gt_total_spent = 0
    gt_total_items = 0
    for receipt_file in gt_receipts:
        with open(receipt_file) as f:
            data = json.load(f)
            gt_total_items += len(data['items'])
            if data.get('total'):
                gt_total_spent += data['total']

    print(f"   Total items: {gt_total_items}")
    print(f"   Total spent: ${gt_total_spent:,.2f}")
    print(f"   Avg items per receipt: {gt_total_items / len(gt_receipts):.1f}")

    # Validate fictional customers
    print("\n2. FICTIONAL CUSTOMERS")
    print("-" * 70)

    fictional_dir = Path("fictional_customers")
    customer_dirs = sorted([d for d in fictional_dir.iterdir() if d.is_dir()])

    archetype_stats = defaultdict(lambda: {
        'count': 0,
        'total_spent': 0,
        'total_items': 0,
        'total_receipts': 0
    })

    customer_summaries = []

    for customer_dir in customer_dirs:
        profile_path = customer_dir / "customer_profile.json"

        if profile_path.exists():
            with open(profile_path) as f:
                profile = json.load(f)

            receipt_files = list(customer_dir.glob("receipt_*.json"))

            # Count items across all receipts
            total_items = 0
            for receipt_file in receipt_files:
                with open(receipt_file) as f:
                    receipt = json.load(f)
                    total_items += len(receipt['items'])

            customer_summaries.append({
                'id': profile['customer_id'],
                'name': profile['customer_name'],
                'archetype': profile['archetype'],
                'receipts': len(receipt_files),
                'spent': profile['total_spent'],
                'savings': profile['total_savings'],
                'items': total_items,
                'avg_items': profile['avg_items_per_trip']
            })

            # Update archetype stats
            arch = profile['archetype']
            archetype_stats[arch]['count'] += 1
            archetype_stats[arch]['total_spent'] += profile['total_spent']
            archetype_stats[arch]['total_items'] += total_items
            archetype_stats[arch]['total_receipts'] += len(receipt_files)

    # Print customer summaries
    print(f"\n   {'Customer':<25} {'Archetype':<20} {'Receipts':<10} {'Total Spent':<15} {'Avg Items'}")
    print("   " + "-" * 85)

    for customer in customer_summaries:
        print(f"   {customer['name']:<25} {customer['archetype']:<20} "
              f"{customer['receipts']:<10} ${customer['spent']:<14,.2f} {customer['avg_items']:.1f}")

    # Print archetype analysis
    print("\n3. ARCHETYPE ANALYSIS")
    print("-" * 70)

    for archetype, stats in sorted(archetype_stats.items()):
        print(f"\n   {archetype.upper().replace('_', ' ')}")
        print(f"   • Customers: {stats['count']}")
        print(f"   • Total receipts: {stats['total_receipts']}")
        print(f"   • Total spent: ${stats['total_spent']:,.2f}")
        print(f"   • Avg spent per customer: ${stats['total_spent'] / stats['count']:,.2f}")
        print(f"   • Avg items per receipt: {stats['total_items'] / stats['total_receipts']:.1f}")

    # Overall summary
    print("\n4. OVERALL DATASET SUMMARY")
    print("-" * 70)

    total_customers = len(customer_summaries)
    total_receipts = sum(c['receipts'] for c in customer_summaries)
    total_spent = sum(c['spent'] for c in customer_summaries)
    total_savings = sum(c['savings'] for c in customer_summaries)
    total_items = sum(c['items'] for c in customer_summaries)

    print(f"   Total customers: {total_customers}")
    print(f"   Total receipts: {total_receipts} (fictional) + {len(gt_receipts)} (ground truth)")
    print(f"   Total items: {total_items:,} (fictional) + {gt_total_items} (ground truth)")
    print(f"   Total spent: ${total_spent:,.2f} (fictional)")
    print(f"   Total savings: ${total_savings:,.2f} (fictional)")
    print(f"   Avg receipt value: ${total_spent / total_receipts:.2f}")
    print(f"   Avg items per receipt: {total_items / total_receipts:.1f}")
    print(f"   Savings rate: {(total_savings / (total_spent + total_savings)) * 100:.1f}%")

    # Validate data integrity
    print("\n5. DATA INTEGRITY CHECKS")
    print("-" * 70)

    issues = 0

    # Check all customers have 17 receipts
    for customer in customer_summaries:
        if customer['receipts'] != 17:
            print(f"   ⚠ {customer['name']} has {customer['receipts']} receipts (expected 17)")
            issues += 1

    # Check all receipts have required fields
    required_fields = ['store', 'customer_id', 'items', 'total', 'savings']

    for customer_dir in customer_dirs:
        for receipt_file in customer_dir.glob("receipt_*.json"):
            with open(receipt_file) as f:
                receipt = json.load(f)

            for field in required_fields:
                if field not in receipt:
                    print(f"   ⚠ {receipt_file.name} missing field: {field}")
                    issues += 1

            # Check items have required fields
            for item in receipt.get('items', []):
                if not all(k in item for k in ['quantity', 'name', 'price']):
                    print(f"   ⚠ {receipt_file.name} has item missing required fields")
                    issues += 1
                    break

    if issues == 0:
        print("   ✓ All data integrity checks passed!")
    else:
        print(f"   ⚠ Found {issues} issues")

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    validate_dataset()
