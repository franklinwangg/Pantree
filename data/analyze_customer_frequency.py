#!/usr/bin/env python3
"""
Analyzes customer purchase frequency to identify potential "Subscribe & Save" candidates.
Includes statistical analysis: confidence scores, trend analysis, recency weighting, and consistency metrics.

NOTE: This is a statistical/heuristic approach for frequency analysis.
TODO: Future enhancement - implement ML-based prediction models for more accurate
      purchase frequency forecasting. Consider using:
      - Time series forecasting (ARIMA, Prophet, LSTM)
      - Classification models for purchase likelihood
      - Collaborative filtering for cross-customer patterns
      - Survival analysis for churn prediction
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics
from typing import List, Dict, Any

def calculate_item_statistics(dates: List[datetime], current_date: datetime) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for an item's purchase history.

    Args:
        dates: List of purchase dates for the item
        current_date: Reference date for recency calculations (typically most recent purchase)

    Returns:
        Dictionary containing statistical measures
    """
    if len(dates) < 2:
        return None

    sorted_dates = sorted(dates)
    intervals = [(sorted_dates[i] - sorted_dates[i-1]).days for i in range(1, len(sorted_dates))]

    # Basic statistics
    avg_interval = statistics.mean(intervals)
    std_dev = statistics.stdev(intervals) if len(intervals) > 1 else 0

    # Coefficient of Variation (CV) - normalized measure of consistency
    # Lower CV = more consistent purchasing pattern
    coefficient_of_variation = (std_dev / avg_interval * 100) if avg_interval > 0 else 100

    # Consistency Score (0-100, higher is better)
    # Based on inverse of CV, capped at reasonable values
    consistency_score = max(0, min(100, 100 - coefficient_of_variation))

    # Trend Analysis - are intervals getting shorter (buying more frequently) or longer?
    # Using linear regression slope on intervals
    if len(intervals) >= 3:
        n = len(intervals)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(intervals) / n

        numerator = sum((x[i] - x_mean) * (intervals[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        trend_slope = numerator / denominator if denominator != 0 else 0

        # Classify trend
        if trend_slope < -2:
            trend = "increasing frequency"  # intervals getting shorter
        elif trend_slope > 2:
            trend = "decreasing frequency"  # intervals getting longer
        else:
            trend = "stable"
    else:
        trend_slope = 0
        trend = "insufficient data"

    # Recency Score - how recent was the last purchase?
    # Score from 0-100, where 100 = purchased today, decreases over time
    days_since_last = (current_date - sorted_dates[-1]).days
    recency_score = max(0, 100 - (days_since_last / 30 * 20))  # Decreases 20 points per month

    # Confidence Score (0-100) - overall confidence in subscription recommendation
    # Factors: consistency, recency, number of purchases, trend stability
    purchase_count_score = min(100, (len(dates) / 10) * 100)  # Max out at 10 purchases
    trend_stability_score = max(0, 100 - abs(trend_slope) * 5)  # Penalize volatile trends

    confidence = (
        consistency_score * 0.35 +      # Consistency is most important
        recency_score * 0.25 +           # Recent purchases matter
        purchase_count_score * 0.25 +    # More data = more confidence
        trend_stability_score * 0.15     # Stable trends are better
    )

    return {
        "count": len(dates),
        "avg_interval": round(avg_interval, 1),
        "std_dev": round(std_dev, 1),
        "coefficient_of_variation": round(coefficient_of_variation, 1),
        "consistency_score": round(consistency_score, 1),
        "trend": trend,
        "trend_slope": round(trend_slope, 2),
        "days_since_last": days_since_last,
        "recency_score": round(recency_score, 1),
        "confidence": round(confidence, 1)
    }


def analyze_customer_frequency(dataset_dir: str, limit_customers: int = 5, min_purchases: int = 3, min_confidence: float = 50.0):
    """
    Analyzes purchase frequency for customers in the dataset with statistical measures.

    Args:
        dataset_dir: The path to the directory containing the large dataset batches.
        limit_customers: The number of customers to display analysis for.
        min_purchases: Minimum number of purchases required for analysis.
        min_confidence: Minimum confidence score to display recommendations.
    """
    dataset_path = Path(dataset_dir)
    if not dataset_path.is_dir():
        print(f"Error: Dataset directory not found at '{dataset_dir}'")
        return

    batch_files = sorted(list(dataset_path.glob("batch_*.json")))
    if not batch_files:
        print(f"Error: No batch files found in '{dataset_dir}'.")
        print("Please generate the large dataset first using 'generate_large_dataset.py'.")
        return

    print(f"Reading {len(batch_files)} batch files from '{dataset_dir}'...")
    print(f"Analysis parameters: min_purchases={min_purchases}, min_confidence={min_confidence}")
    customer_purchases = defaultdict(lambda: defaultdict(list))
    most_recent_date = None

    # Step 1: Aggregate all purchases for each customer and find most recent date
    for batch_file in batch_files:
        with open(batch_file, 'r', encoding='utf-8') as f:
            customers = json.load(f)
            for customer in customers:
                customer_id = customer['customer_id']
                for receipt in customer['receipts']:
                    try:
                        purchase_date = datetime.strptime(receipt['pickup_date'], "%A, %B %d, %Y")
                        if most_recent_date is None or purchase_date > most_recent_date:
                            most_recent_date = purchase_date
                        for item in receipt['items']:
                            customer_purchases[customer_id][item['name']].append(purchase_date)
                    except (ValueError, KeyError) as e:
                        print(f"Warning: Skipping receipt for customer {customer_id} due to parsing error: {e}")
                        continue

    # Use most recent date in dataset as reference for recency calculations
    reference_date = most_recent_date if most_recent_date else datetime.now()

    print("\n" + "="*100)
    print("Purchase Frequency Analysis for 'Subscribe & Save' with Statistical Confidence")
    print("="*100)

    customers_analyzed = 0
    # Step 2: Analyze each customer for recurring purchases with statistics
    for customer_id, items in customer_purchases.items():
        if customers_analyzed >= limit_customers:
            break

        recurring_items = []
        for item_name, dates in items.items():
            # Apply minimum purchase threshold
            if len(dates) >= min_purchases:
                stats = calculate_item_statistics(dates, reference_date)
                if stats and stats['confidence'] >= min_confidence:
                    recurring_items.append({
                        "name": item_name,
                        **stats
                    })

        # Step 3: Generate and print the recommendation report
        if recurring_items:
            customers_analyzed += 1
            print(f"\n{'='*100}")
            print(f"Customer: {customer_id}")
            print(f"{'='*100}")

            # Sort by confidence score (highest first)
            recurring_items.sort(key=lambda x: x['confidence'], reverse=True)

            print(f"Found {len(recurring_items)} high-confidence items. Showing top recommendations:\n")

            for idx, item in enumerate(recurring_items[:10], 1):  # Show top 10
                interval = item['avg_interval']
                suggestion = "monthly"
                if interval <= 8:
                    suggestion = "weekly"
                elif interval <= 16:
                    suggestion = "bi-weekly"
                elif interval <= 24:
                    suggestion = "every 3 weeks"

                # Confidence level description
                conf = item['confidence']
                if conf >= 80:
                    conf_level = "VERY HIGH"
                elif conf >= 65:
                    conf_level = "HIGH"
                elif conf >= 50:
                    conf_level = "MODERATE"
                else:
                    conf_level = "LOW"

                print(f"{idx}. Item: \"{item['name']}\"")
                print(f"   └─ Recommendation: {suggestion.upper()} subscription")
                print(f"   └─ Confidence: {conf}% ({conf_level})")
                print(f"   ")
                print(f"   Purchase History:")
                print(f"      • Total purchases: {item['count']}")
                print(f"      • Average interval: {interval} days")
                print(f"      • Last purchased: {item['days_since_last']} days ago")
                print(f"   ")
                print(f"   Statistical Measures:")
                print(f"      • Consistency score: {item['consistency_score']}% (std dev: ±{item['std_dev']} days)")
                print(f"      • Coefficient of variation: {item['coefficient_of_variation']}%")
                print(f"      • Trend: {item['trend']} (slope: {item['trend_slope']})")
                print(f"      • Recency score: {item['recency_score']}%")
                print()

    if customers_analyzed == 0:
        print(f"\nNo customers found with {min_purchases}+ purchases and {min_confidence}+ confidence score.")
        print("Try lowering --min-purchases or --min-confidence thresholds.")

    print("="*100)
    print("Analysis complete.")
    print("="*100)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze customer purchase frequency for 'Subscribe & Save' recommendations with statistical confidence."
    )
    parser.add_argument(
        "dataset_dir",
        type=str,
        help="Directory containing the large dataset batch files (e.g., 'large_dataset/')."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="The number of customers to display analysis for (default: 5)."
    )
    parser.add_argument(
        "--min-purchases",
        type=int,
        default=3,
        help="Minimum number of purchases required to analyze an item (default: 3)."
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=50.0,
        help="Minimum confidence score (0-100) to display recommendations (default: 50.0)."
    )
    args = parser.parse_args()
    analyze_customer_frequency(
        args.dataset_dir,
        args.limit,
        args.min_purchases,
        args.min_confidence
    )
