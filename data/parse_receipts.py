#!/usr/bin/env python3
"""
Parse receipts from mbox file and convert to JSON format.
"""

import mailbox
import json
import re
import os
from email import policy
from email.parser import BytesParser
from datetime import datetime
from pathlib import Path


def extract_text_from_email(msg):
    """Extract plain text content from email message."""
    text_content = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        text_content += payload.decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"Error decoding part: {e}")
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                text_content = payload.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error decoding message: {e}")

    return text_content


def parse_safeway_receipt(text, subject, date_str):
    """Parse Safeway receipt from email text."""
    receipt = {
        "store": "Safeway",
        "subject": subject,
        "email_date": date_str,
        "items": [],
        "order_number": None,
        "pickup_date": None,
        "pickup_time": None,
        "pickup_address": None,
        "subtotal": None,
        "total": None,
        "taxes_and_fees": None,
        "savings": {},
        "payment_method": None
    }

    # Extract order number
    order_match = re.search(r'Order:\s*#?(\d+)', text)
    if order_match:
        receipt["order_number"] = order_match.group(1)

    # Extract pickup date
    date_match = re.search(r'Pickup Date & Time.*?\n.*?([A-Z][a-z]+day,\s+[A-Z][a-z]+\s+\d+,\s+\d{4})', text, re.DOTALL)
    if date_match:
        receipt["pickup_date"] = date_match.group(1)

    # Extract pickup time
    time_match = re.search(r'(\d+:\d+\s+[AP]M)\s*-\s*(\d+:\d+\s+[AP]M)', text)
    if time_match:
        receipt["pickup_time"] = f"{time_match.group(1)} - {time_match.group(2)}"

    # Extract pickup address
    address_match = re.search(r'Pickup Address.*?\n.*?(\d+\s+[^\n]+)\s*\n\s*([^|]+)', text, re.DOTALL)
    if address_match:
        receipt["pickup_address"] = f"{address_match.group(1).strip()}, {address_match.group(2).strip()}"

    # Extract items - pattern: quantity x | item name | price
    item_pattern = r'(\d+)x\s*\|\s*([^|]+?)\s*\|\s*\$?([\d,]+\.\d{2})'
    for match in re.finditer(item_pattern, text):
        quantity = int(match.group(1))
        item_name = match.group(2).strip()
        # Clean up item name (remove extra spaces and line breaks)
        item_name = re.sub(r'\s+', ' ', item_name)
        price = match.group(3).replace(',', '')

        receipt["items"].append({
            "quantity": quantity,
            "name": item_name,
            "price": float(price)
        })

    # Extract subtotal
    subtotal_match = re.search(r'Estimated Subtotal\s*\|\s*\$?([\d,]+\.\d{2})', text)
    if subtotal_match:
        receipt["subtotal"] = float(subtotal_match.group(1).replace(',', ''))

    # Extract total
    total_match = re.search(r'Estimated Total\s*\|\s*\$?([\d,]+\.\d{2})', text)
    if total_match:
        receipt["total"] = float(total_match.group(1).replace(',', ''))

    # Extract taxes and fees
    taxes_match = re.search(r'Estimated Taxes and Fees\s*\|\s*\$?([\d,]+\.\d{2})', text)
    if taxes_match:
        receipt["taxes_and_fees"] = float(taxes_match.group(1).replace(',', ''))

    # Extract savings
    total_savings_match = re.search(r'Estimated Savings\s*\|\s*-?\$?([\d,]+\.\d{2})', text)
    if total_savings_match:
        receipt["savings"]["total"] = float(total_savings_match.group(1).replace(',', ''))

    member_savings_match = re.search(r'Member Price Savings\s*\|\s*-?\$?([\d,]+\.\d{2})', text)
    if member_savings_match:
        receipt["savings"]["member_price"] = float(member_savings_match.group(1).replace(',', ''))

    safeway_savings_match = re.search(r'Safeway for U Savings\s*\|\s*-?\$?([\d,]+\.\d{2})', text)
    if safeway_savings_match:
        receipt["savings"]["safeway_for_u"] = float(safeway_savings_match.group(1).replace(',', ''))

    # Extract payment method
    payment_match = re.search(r'Card ending in (\d+)\s*\|\s*\$?([\d,]+\.\d{2})', text)
    if payment_match:
        receipt["payment_method"] = f"Card ending in {payment_match.group(1)}"

    return receipt


def parse_generic_receipt(text, subject, date_str, sender):
    """Parse generic receipt from email text."""
    receipt = {
        "store": sender,
        "subject": subject,
        "email_date": date_str,
        "raw_text": text[:1000],  # Store first 1000 chars for reference
        "items": [],
        "total": None
    }

    # Try to extract common patterns
    # Look for dollar amounts
    amounts = re.findall(r'\$?([\d,]+\.\d{2})', text)
    if amounts:
        # Try to find the largest amount as potential total
        max_amount = max([float(a.replace(',', '')) for a in amounts])
        receipt["total"] = max_amount

    return receipt


def sanitize_filename(filename):
    """Create a safe filename from string."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def main():
    mbox_path = "data/pantree/receipts.mbox"
    output_dir = "data/pantree/receipts_json"

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Open mbox file
    mbox = mailbox.mbox(mbox_path)

    receipt_count = 0

    for idx, message in enumerate(mbox):
        try:
            # Extract basic email info
            subject = message.get('Subject', 'No Subject')
            date_str = message.get('Date', 'No Date')
            from_addr = message.get('From', 'Unknown')

            print(f"\nProcessing email {idx + 1}: {subject}")

            # Extract text content
            text = extract_text_from_email(message)

            # Determine receipt type and parse accordingly
            if 'safeway' in subject.lower() or 'safeway' in from_addr.lower():
                receipt_data = parse_safeway_receipt(text, subject, date_str)
            else:
                # Generic parser for other receipts
                receipt_data = parse_generic_receipt(text, subject, date_str, from_addr)

            # Create filename from subject and index
            safe_subject = sanitize_filename(subject)
            filename = f"receipt_{idx + 1:03d}_{safe_subject}.json"
            filepath = os.path.join(output_dir, filename)

            # Write JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(receipt_data, f, indent=2, ensure_ascii=False)

            print(f"  Saved to: {filename}")
            print(f"  Items found: {len(receipt_data['items'])}")
            if receipt_data.get('total'):
                print(f"  Total: ${receipt_data['total']:.2f}")

            receipt_count += 1

        except Exception as e:
            print(f"  Error processing email {idx + 1}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n\nCompleted! Processed {receipt_count} receipts.")
    print(f"JSON files saved to: {output_dir}")


if __name__ == "__main__":
    main()
