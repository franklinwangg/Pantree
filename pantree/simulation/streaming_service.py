"""
Streaming Service - Streams simulated purchase data month-by-month in real-time.

This service takes generated purchase history and streams it back to the frontend
month by month, simulating real-time data arrival.
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, AsyncGenerator, Optional, Callable
from collections import defaultdict


class StreamingService:
    """
    Streams purchase history data month-by-month to simulate real-time updates.
    """

    def __init__(self, stream_delay: float = 0.5):
        """
        Initialize streaming service.

        Args:
            stream_delay: Delay in seconds between streaming each month's data
        """
        self.stream_delay = stream_delay

    def group_by_month(self, receipts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group receipts by month.

        Args:
            receipts: List of receipt dictionaries

        Returns:
            Dictionary mapping month keys to receipt lists
        """
        monthly_data = defaultdict(list)

        for receipt in receipts:
            try:
                date = datetime.strptime(receipt["pickup_date"], "%A, %B %d, %Y")
                month_key = date.strftime("%Y-%m")
                monthly_data[month_key].append(receipt)
            except (ValueError, KeyError) as e:
                print(f"Warning: Could not parse date for receipt: {e}")
                continue

        return dict(monthly_data)

    async def stream_monthly_data(
        self,
        receipts: List[Dict[str, Any]],
        callback: Optional[Callable] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream receipt data month by month.

        Args:
            receipts: List of all receipts to stream
            callback: Optional callback function to call with each month's data

        Yields:
            Dictionary containing month info and receipts
        """
        monthly_data = self.group_by_month(receipts)
        sorted_months = sorted(monthly_data.keys())

        total_months = len(sorted_months)

        for idx, month in enumerate(sorted_months, 1):
            month_receipts = monthly_data[month]

            # Calculate statistics for this month
            total_spent = sum(r.get("total", 0) for r in month_receipts)
            total_items = sum(len(r.get("items", [])) for r in month_receipts)
            total_savings = sum(r.get("savings", {}).get("total", 0) for r in month_receipts)

            month_data = {
                "month": month,
                "month_display": datetime.strptime(f"{month}-01", "%Y-%m-%d").strftime("%B %Y"),
                "receipts": month_receipts,
                "receipt_count": len(month_receipts),
                "total_spent": round(total_spent, 2),
                "total_items": total_items,
                "total_savings": round(total_savings, 2),
                "progress": {
                    "current": idx,
                    "total": total_months,
                    "percentage": round((idx / total_months) * 100, 1),
                },
            }

            # Call callback if provided
            if callback:
                try:
                    await callback(month_data)
                except Exception as e:
                    print(f"Error in callback: {e}")

            # Yield the data
            yield month_data

            # Wait before streaming next month (except for last month)
            if idx < total_months:
                await asyncio.sleep(self.stream_delay)

    async def stream_to_websocket(
        self,
        receipts: List[Dict[str, Any]],
        websocket,
    ):
        """
        Stream data directly to a WebSocket connection.

        Args:
            receipts: List of receipts to stream
            websocket: WebSocket connection object
        """
        async for month_data in self.stream_monthly_data(receipts):
            try:
                message = {
                    "type": "monthly_data",
                    "data": month_data,
                }
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to websocket: {e}")
                break

        # Send completion message
        try:
            await websocket.send_json({
                "type": "simulation_complete",
                "data": {
                    "total_receipts": len(receipts),
                    "message": "Purchase history simulation complete",
                },
            })
        except Exception as e:
            print(f"Error sending completion message: {e}")

    def create_summary(self, receipts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary of all receipts.

        Args:
            receipts: List of receipts

        Returns:
            Summary statistics
        """
        if not receipts:
            return {
                "total_receipts": 0,
                "total_spent": 0,
                "total_savings": 0,
                "total_items": 0,
                "date_range": None,
            }

        # Parse dates
        dates = []
        for receipt in receipts:
            try:
                date = datetime.strptime(receipt["pickup_date"], "%A, %B %d, %Y")
                dates.append(date)
            except (ValueError, KeyError):
                continue

        total_spent = sum(r.get("total", 0) for r in receipts)
        total_savings = sum(r.get("savings", {}).get("total", 0) for r in receipts)
        total_items = sum(len(r.get("items", [])) for r in receipts)

        return {
            "total_receipts": len(receipts),
            "total_spent": round(total_spent, 2),
            "total_savings": round(total_savings, 2),
            "total_items": total_items,
            "avg_receipt_value": round(total_spent / len(receipts), 2) if receipts else 0,
            "date_range": {
                "start": min(dates).strftime("%Y-%m-%d") if dates else None,
                "end": max(dates).strftime("%Y-%m-%d") if dates else None,
                "months": len(set(d.strftime("%Y-%m") for d in dates)) if dates else 0,
            },
        }


async def demo_streaming():
    """Demo function showing how to use the streaming service."""
    from simulation.purchase_simulator import PurchaseSimulator

    # Create simulator and generate data
    simulator = PurchaseSimulator()
    seed_items = [
        {"name": "Bananas", "price": 1.99},
        {"name": "Chicken Breast", "price": 12.99},
        {"name": "Whole Milk (Gallon)", "price": 5.49},
    ]

    history = simulator.generate_purchase_history(
        seed_items=seed_items,
        archetype="health_conscious",
        months=6,
        customer_id="demo_001",
    )

    # Create streaming service
    streamer = StreamingService(stream_delay=1.0)

    # Define callback
    async def print_month(month_data):
        print(f"\n{'='*60}")
        print(f"Streaming: {month_data['month_display']}")
        print(f"Receipts: {month_data['receipt_count']}")
        print(f"Total Spent: ${month_data['total_spent']:.2f}")
        print(f"Progress: {month_data['progress']['percentage']}%")
        print(f"{'='*60}")

    # Stream the data
    print("Starting simulation stream...")
    async for month_data in streamer.stream_monthly_data(history, callback=print_month):
        pass  # Data already printed in callback

    print("\nSimulation complete!")

    # Print summary
    summary = streamer.create_summary(history)
    print(f"\nSummary:")
    print(f"  Total Receipts: {summary['total_receipts']}")
    print(f"  Total Spent: ${summary['total_spent']:.2f}")
    print(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(demo_streaming())
