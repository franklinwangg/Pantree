#!/usr/bin/env python3
"""
Utility script to read and analyze large dataset batch files.
"""

import json
from pathlib import Path
import sys


def read_dataset_summary(dataset_dir):
    """Read the dataset summary."""
    summary_path = Path(dataset_dir) / "dataset_summary.json"

    if not summary_path.exists():
        print(f"Error: Summary file not found at {summary_path}")
        return None

    with open(summary_path) as f:
        return json.load(f)


def read_batch(dataset_dir, batch_num):
    """Read a specific batch file."""
    batch_path = Path(dataset_dir) / f"batch_{batch_num:05d}.json"

    if not batch_path.exists():
        print(f"Error: Batch file not found at {batch_path}")
        return None

    with open(batch_path) as f:
        return json.load(f)


def get_customer_by_id(dataset_dir, customer_id):
    """Find a customer by ID across all batches."""
    dataset_path = Path(dataset_dir)
    batch_files = sorted(dataset_path.glob("batch_*.json"))

    for batch_file in batch_files:
        with open(batch_file) as f:
            batch_data = json.load(f)

        for customer in batch_data:
            if customer["customer_id"] == customer_id:
                return customer

    return None


def search_customers_by_archetype(dataset_dir, archetype, limit=10):
    """Search for customers by archetype."""
    dataset_path = Path(dataset_dir)
    batch_files = sorted(dataset_path.glob("batch_*.json"))

    results = []

    for batch_file in batch_files:
        with open(batch_file) as f:
            batch_data = json.load(f)

        for customer in batch_data:
            if customer["archetype"] == archetype:
                results.append(customer)

                if len(results) >= limit:
                    return results

    return results


def analyze_dataset(dataset_dir):
    """Analyze the entire dataset."""
    print("="*70)
    print("DATASET ANALYSIS")
    print("="*70)

    summary = read_dataset_summary(dataset_dir)
    if not summary:
        return

    print(f"\nGeneration Date: {summary['generation_date']}")
    print(f"Total Customers: {summary['total_customers']:,}")
    print(f"Total Receipts: {summary['total_receipts']:,}")
    print(f"Total Batches: {summary['total_batches']}")

    print("\nStatistics:")
    stats = summary['statistics']
    print(f"  Total Spent: ${stats['total_spent']:,.2f}")
    print(f"  Total Savings: ${stats['total_savings']:,.2f}")
    print(f"  Total Items: {stats['total_items']:,}")
    print(f"  Avg Spent/Customer: ${stats['avg_spent_per_customer']:,.2f}")
    print(f"  Avg Items/Receipt: {stats['avg_items_per_receipt']:.1f}")

    print("\nArchetype Distribution:")
    for archetype, count in sorted(summary['archetypes'].items()):
        pct = count / summary['total_customers'] * 100
        print(f"  {archetype:25s}: {count:6,} customers ({pct:5.1f}%)")

    print("="*70)


def show_customer_details(customer):
    """Display detailed information about a customer."""
    print("\n" + "="*70)
    print("CUSTOMER DETAILS")
    print("="*70)
    print(f"ID: {customer['customer_id']}")
    print(f"Name: {customer['customer_name']}")
    print(f"Archetype: {customer['archetype']}")
    print(f"Total Receipts: {customer['total_receipts']}")
    print(f"Total Spent: ${customer['total_spent']:,.2f}")
    print(f"Total Savings: ${customer['total_savings']:,.2f}")
    print(f"Total Items: {customer['total_items']}")

    print(f"\nFirst 3 Receipts:")
    for i, receipt in enumerate(customer['receipts'][:3]):
        print(f"\n  Receipt {i+1}:")
        print(f"    Date: {receipt['pickup_date']}")
        print(f"    Items: {len(receipt['items'])}")
        print(f"    Total: ${receipt['total']:.2f}")
        print(f"    Savings: ${receipt['savings']:.2f}")
        print(f"    Sample Items:")
        for item in receipt['items'][:3]:
            print(f"      - {item['quantity']}x {item['name']}: ${item['price']:.2f}")

    print("="*70)


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Read and analyze large dataset"
    )
    parser.add_argument(
        "dataset_dir",
        help="Path to dataset directory"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show dataset summary"
    )
    parser.add_argument(
        "--customer",
        type=str,
        help="Show details for specific customer ID (e.g., customer_000001)"
    )
    parser.add_argument(
        "--archetype",
        type=str,
        help="Search for customers by archetype"
    )
    parser.add_argument(
        "--batch",
        type=int,
        help="Display batch number"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit results for searches (default: 10)"
    )

    args = parser.parse_args()

    # Default action is to show summary
    if not any([args.summary, args.customer, args.archetype, args.batch]):
        args.summary = True

    if args.summary:
        analyze_dataset(args.dataset_dir)

    if args.customer:
        customer = get_customer_by_id(args.dataset_dir, args.customer)
        if customer:
            show_customer_details(customer)
        else:
            print(f"Customer {args.customer} not found")

    if args.archetype:
        customers = search_customers_by_archetype(
            args.dataset_dir,
            args.archetype,
            args.limit
        )
        print(f"\nFound {len(customers)} customers with archetype '{args.archetype}':")
        for customer in customers:
            print(f"  {customer['customer_id']}: {customer['customer_name']} "
                  f"(${customer['total_spent']:.2f} spent)")

    if args.batch is not None:
        batch_data = read_batch(args.dataset_dir, args.batch)
        if batch_data:
            print(f"\nBatch {args.batch} contains {len(batch_data)} customers")
            for customer in batch_data[:5]:  # Show first 5
                print(f"  {customer['customer_id']}: {customer['customer_name']} "
                      f"({customer['archetype']})")
            if len(batch_data) > 5:
                print(f"  ... and {len(batch_data) - 5} more customers")


if __name__ == "__main__":
    main()
