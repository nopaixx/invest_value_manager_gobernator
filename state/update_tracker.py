#!/usr/bin/env python3
"""
Daily portfolio tracker — updates portfolio_tracker.csv and prints comparison vs S&P 500.
Run at end of each day before daily report.

Usage: python3 state/update_tracker.py
"""

import csv
import os
import sys
from datetime import datetime

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "portfolio_tracker.csv")

def get_portfolio_value():
    """Get current portfolio value from eToro demo."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from etoro.client import EtoroClient
    c = EtoroClient()
    portfolio = c.get_portfolio()
    positions = portfolio.get("clientPortfolio", {}).get("positions", [])
    pnl_data = c.get_pnl()
    pnl_positions = pnl_data.get("clientPortfolio", {}).get("positions", [])

    total_invested = sum(p.get("amount", 0) for p in positions)
    total_pnl = 0
    for pos in pnl_positions:
        total_pnl += pos.get("unrealizedPnL", {}).get("pnL", 0)

    # Include pending buy orders (not yet settled but capital committed)
    pending_buys = portfolio.get("clientPortfolio", {}).get("ordersForOpen", [])
    pending_buy_amount = sum(o.get("amount", 0) for o in pending_buys)

    return round(total_invested + total_pnl + pending_buy_amount, 2)


def get_sp500():
    """Get S&P 500 current price via specialist's price_checker."""
    import subprocess
    try:
        result = subprocess.run(
            ["python3", "/home/angel/value_invest2/tools/price_checker.py", "^GSPC"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().split("\n"):
            if "GSPC" in line or "S&P" in line:
                parts = line.split()
                for p in parts:
                    try:
                        val = float(p.replace(",", "").replace("$", ""))
                        if val > 1000:
                            return val
                    except ValueError:
                        continue
    except Exception:
        pass
    return None


def read_tracker():
    """Read existing tracker data."""
    rows = []
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return rows


def update_tracker():
    """Add today's data and print comparison."""
    today = datetime.now().strftime("%Y-%m-%d")
    rows = read_tracker()

    # Check if today already exists
    if rows and rows[-1]["date"] == today:
        print(f"Already tracked for {today}. Updating...")
        rows = rows[:-1]

    # Get current values
    portfolio_value = get_portfolio_value()
    sp500 = get_sp500()

    if not portfolio_value:
        print("ERROR: Could not get portfolio value")
        return

    # Calculate P&L from inception
    inception_portfolio = float(rows[0]["portfolio_value"]) if rows else portfolio_value
    inception_sp500 = float(rows[0]["sp500"]) if rows and rows[0]["sp500"] else sp500
    portfolio_pnl_pct = round((portfolio_value / inception_portfolio - 1) * 100, 2)
    sp500_pnl_pct = round((sp500 / inception_sp500 - 1) * 100, 2) if sp500 and inception_sp500 else 0

    # Add today
    rows.append({
        "date": today,
        "portfolio_value": str(portfolio_value),
        "portfolio_pnl_pct": str(portfolio_pnl_pct),
        "sp500": str(sp500) if sp500 else "",
        "sp500_pnl_pct": str(sp500_pnl_pct),
    })

    # Write
    with open(TRACKER_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "portfolio_value", "portfolio_pnl_pct", "sp500", "sp500_pnl_pct"])
        writer.writeheader()
        writer.writerows(rows)

    # Print comparison
    print(f"\n{'='*55}")
    print(f"  Portfolio vs S&P 500 — desde {rows[0]['date']}")
    print(f"{'='*55}")
    print(f"  {'Fecha':<12} {'Portfolio':>10} {'P&L%':>8} {'S&P500':>10} {'P&L%':>8}")
    print(f"  {'-'*48}")
    for row in rows:
        p_pnl = float(row["portfolio_pnl_pct"])
        s_pnl = float(row["sp500_pnl_pct"]) if row["sp500_pnl_pct"] else 0
        p_sign = "+" if p_pnl >= 0 else ""
        s_sign = "+" if s_pnl >= 0 else ""
        print(f"  {row['date']:<12} ${float(row['portfolio_value']):>9.0f} {p_sign}{p_pnl:>6.1f}% ${float(row['sp500'] or 0):>9.0f} {s_sign}{s_pnl:>6.1f}%")

    diff = portfolio_pnl_pct - sp500_pnl_pct
    diff_sign = "+" if diff >= 0 else ""
    print(f"  {'-'*48}")
    print(f"  Alpha vs S&P 500: {diff_sign}{diff:.1f}pp")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    update_tracker()
