#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py
"""
import json
from datetime import datetime
from decimal import Decimal


def parse_ts(value):
    """Parse an ISO 8601 UTC timestamp such as 2026-09-21T15:30:26Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_amount(value):
    """Amounts arrive as numbers or as strings with thousands separators.

    Decimal avoids the float rounding drift that builds up over ~20k payments.
    """
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return Decimal(str(value))


def read_events(path):
    """Yield every readable event that has a txn_id."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get("txn_id"):
                yield event


def latest_attempts(events):
    """Keep one event per txn_id: the most recent attempt by timestamp.

    The file is not in time order, so line position cannot be trusted.
    """
    latest = {}
    for event in events:
        key = event["txn_id"]
        ts = parse_ts(event["ts"])
        if key not in latest or ts >= latest[key][0]:
            latest[key] = (ts, event)
    return [event for _, event in latest.values()]


def main():
    collected = [e for e in latest_attempts(read_events("payments.jsonl"))
                 if e["status"] == "success"]
    count = len(collected)
    total = sum((parse_amount(e["amount"]) for e in collected), Decimal(0))

    with open("expected.txt") as f:
        expected = int(f.read().strip())

    if count != expected:
        print(f"Check failed: counted {count} successful payments, expected {expected}.")
        print("Something in the data isn't being handled the way the README describes.")
    else:
        print(f"Check passed: {count} successful payments.")
        print(f"Your code: KOYA-{round(total)}")


if __name__ == "__main__":
    main()
