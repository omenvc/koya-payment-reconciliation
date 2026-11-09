#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (see README):
- Skip lines that can't be parsed, and events without a txn_id.
- A txn_id can have several attempts; only the latest (by ts) counts.
- A payment is collected only if its latest attempt is "success".
"""
import json
from datetime import datetime


def parse_amount(value):
    """Amounts arrive as numbers or as strings like "1,234.56"."""
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(",", "").strip())


def parse_ts(value):
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


latest = {}  # txn_id -> (timestamp, event)

with open("payments.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue  # truncated / unreadable line
        if not isinstance(event, dict):
            continue

        txn_id = event.get("txn_id")
        if not txn_id:
            continue

        ts = parse_ts(event["ts"])
        current = latest.get(txn_id)
        if current is None or ts > current[0]:
            latest[txn_id] = (ts, event)

total = 0.0
count = 0
for ts, event in latest.values():
    if str(event["status"]).strip().lower() == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
