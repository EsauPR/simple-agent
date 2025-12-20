#!/usr/bin/env python3
"""
Script to load the car catalog from CSV using the bulk upload API endpoint.
This script makes HTTP requests to the /api/v1/cars/bulk endpoint.
"""
import asyncio
import csv
import sys
from pathlib import Path
from typing import Dict, Any
import httpx


def parse_csv_row(row: Dict[str, str]) -> Dict[str, Any]:
    """Parse a CSV row into a CarCreate-compatible dictionary"""
    return {
        "stock_id": row["stock_id"],
        "km": int(row["km"]),
        "price": str(row["price"]),  # Decimal as string for JSON
        "make": row["make"],
        "model": row["model"],
        "year": int(row["year"]),
        "version": row.get("version") or None,
        "bluetooth": row.get("bluetooth", "").lower() == "sí",
        "length": str(row["largo"]) if row.get("largo") else None,
        "width": str(row["ancho"]) if row.get("ancho") else None,
        "height": str(row["altura"]) if row.get("altura") else None,
        "car_play": row.get("car_play", "").lower() == "sí",
    }


async def load_cars_via_api(
    csv_path: str,
    api_url: str = "http://localhost:8000",
    batch_size: int = 100
) -> None:
    """Load cars from CSV using the bulk upload API endpoint"""
    csv_file = Path(csv_path)

    if not csv_file.exists():
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)

    cars_data = []

    # Read CSV and parse rows
    print(f"Reading CSV file: {csv_path}")
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                car_data = parse_csv_row(row)
                cars_data.append(car_data)
            except Exception as e:
                print(f"Error parsing row {row.get('stock_id', 'unknown')}: {e}")
                continue

    if not cars_data:
        print("No valid cars found in CSV")
        return

    print(f"Found {len(cars_data)} cars to load")

    # Process in batches
    total_created = 0
    total_errors = 0
    endpoint = f"{api_url}/api/v1/cars/bulk"

    async with httpx.AsyncClient(timeout=60.0) as client:
        for i in range(0, len(cars_data), batch_size):
            batch = cars_data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(cars_data) + batch_size - 1) // batch_size

            print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} cars)...")

            try:
                response = await client.post(
                    endpoint,
                    json=batch,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()

                result = response.json()
                batch_created = result.get("created", 0)
                batch_errors = result.get("errors", 0)

                total_created += batch_created
                total_errors += batch_errors

                print(f"  ✓ Created: {batch_created}, Errors: {batch_errors}")

                # Print error details if any
                if batch_errors > 0 and result.get("error_details"):
                    for error in result["error_details"][:5]:  # Show first 5 errors
                        print(f"    - {error}")
                    if len(result["error_details"]) > 5:
                        print(f"    ... and {len(result['error_details']) - 5} more errors")

            except httpx.HTTPStatusError as e:
                print(f"  ✗ HTTP error {e.response.status_code}: {e.response.text}")
                total_errors += len(batch)
            except Exception as e:
                print(f"  ✗ Error processing batch: {e}")
                total_errors += len(batch)

    print("\nSummary:")
    print(f"  Total cars processed: {len(cars_data)}")
    print(f"  Successfully created: {total_created}")
    print(f"  Errors: {total_errors}")


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Load car catalog from CSV using the bulk upload API"
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="sample_caso_ai_engineer.csv",
        help="Path to CSV file (default: sample_caso_ai_engineer.csv)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of cars per batch (default: 100)"
    )

    args = parser.parse_args()

    # Resolve CSV path relative to project root
    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        csv_path = Path(__file__).parent.parent / csv_path

    await load_cars_via_api(
        csv_path=str(csv_path),
        api_url=args.api_url,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    asyncio.run(main())
