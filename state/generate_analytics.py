#!/usr/bin/env python3
"""
Daily analytics dashboard generator.
Creates a 4-panel chart: returns vs S&P, allocation, P&L by position, key metrics.

Usage: python3 state/generate_analytics.py
Output: reports/daily/images/analytics_YYYY-MM-DD.png
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import csv
import numpy as np
import os
import sys
import json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
TRACKER_FILE = os.path.join(SCRIPT_DIR, "portfolio_tracker.csv")
IMAGES_DIR = os.path.join(ROOT_DIR, "reports", "daily", "images")
TODAY = datetime.now().strftime("%Y-%m-%d")


def get_portfolio_data():
    """Get current portfolio positions and P&L from eToro demo."""
    sys.path.insert(0, ROOT_DIR)
    from collections import defaultdict
    from etoro.client import EtoroClient

    c = EtoroClient()
    portfolio = c.get_portfolio()
    positions = portfolio.get("clientPortfolio", {}).get("positions", [])
    pnl_data = c.get_pnl()
    pnl_positions = pnl_data.get("clientPortfolio", {}).get("positions", [])

    with open(os.path.join(ROOT_DIR, "etoro", "instruments.json")) as f:
        cache = json.load(f)
    cache["WKL.NV"] = 4545
    id_to_ticker = {v: k for k, v in cache.items()}

    grouped = defaultdict(lambda: {"amount": 0, "pnl": 0, "dir": "LONG"})
    for pos in positions:
        iid = pos["instrumentID"]
        ticker = id_to_ticker.get(iid, f"ID:{iid}")
        grouped[ticker]["amount"] += pos.get("amount", 0)
        if not pos.get("isBuy", True):
            grouped[ticker]["dir"] = "SHORT"

    for pos in pnl_positions:
        iid = pos.get("instrumentID", 0)
        ticker = id_to_ticker.get(iid, f"ID:{iid}")
        grouped[ticker]["pnl"] += pos.get("unrealizedPnL", {}).get("pnL", 0)

    return dict(grouped)


def read_tracker():
    """Read portfolio tracker CSV."""
    dates, portfolio, sp500 = [], [], []
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"][5:])
            portfolio.append(float(row["portfolio_pnl_pct"]))
            sp500.append(float(row["sp500_pnl_pct"]))
    return dates, np.array(portfolio), np.array(sp500)


def generate_dashboard(positions_data, dates, portfolio, sp500, metrics):
    """Generate 4-panel analytics dashboard."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    alpha = portfolio - sp500

    fig = plt.figure(figsize=(14, 28))
    fig.suptitle(f'Portfolio Analytics — {TODAY}', fontsize=20, fontweight='bold', y=0.99)
    gs = gridspec.GridSpec(4, 1, hspace=0.3)

    # 1. Returns vs S&P 500
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(dates, portfolio, 'b-o', linewidth=2.5, markersize=10, label='Portfolio', zorder=5)
    ax1.plot(dates, sp500, 'r--o', linewidth=2.5, markersize=10, label='S&P 500', zorder=5)
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax1.fill_between(range(len(dates)), portfolio, sp500, alpha=0.15,
                     color='red' if portfolio[-1] < sp500[-1] else 'green')
    for i, (p, s) in enumerate(zip(portfolio, sp500)):
        ax1.annotate(f'{p:+.1f}%', (i, p), textcoords='offset points',
                     xytext=(0, 12), fontsize=10, color='blue', fontweight='bold')
        ax1.annotate(f'{s:+.1f}%', (i, s), textcoords='offset points',
                     xytext=(0, -18), fontsize=10, color='red', fontweight='bold')
    ax1.set_title('Retorno vs S&P 500', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel('Retorno (%)')

    # 2. Portfolio allocation pie
    ax2 = fig.add_subplot(gs[1, 0])
    labels = sorted(positions_data.keys(), key=lambda x: positions_data[x]["amount"], reverse=True)
    sizes = [positions_data[t]["amount"] for t in labels]
    display_labels = [f'{t} ({"S" if positions_data[t]["dir"] == "SHORT" else "L"})' for t in labels]
    colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
    wedges, texts, autotexts = ax2.pie(sizes, labels=display_labels, autopct='%1.1f%%',
                                        colors=colors, startangle=90, textprops={'fontsize': 9})
    for autotext in autotexts:
        autotext.set_fontsize(8)
    ax2.set_title('Distribución del Portfolio', fontsize=13, fontweight='bold')

    # 3. P&L by position
    ax3 = fig.add_subplot(gs[2, 0])
    tickers_sorted = sorted(positions_data.keys(), key=lambda x: positions_data[x]["pnl"])
    values_sorted = [positions_data[t]["pnl"] for t in tickers_sorted]
    colors_bar = ['#e74c3c' if v < 0 else '#2ecc71' for v in values_sorted]
    bars = ax3.barh(tickers_sorted, values_sorted, color=colors_bar, edgecolor='white', linewidth=0.5)
    ax3.axvline(x=0, color='gray', linewidth=0.8)
    for bar, val in zip(bars, values_sorted):
        sign = '+' if val >= 0 else ''
        offset = 2 if val >= 0 else -2
        ha = 'left' if val >= 0 else 'right'
        ax3.text(val + offset, bar.get_y() + bar.get_height() / 2,
                 f'{sign}${val:.0f}', va='center', ha=ha, fontsize=9, fontweight='bold')
    ax3.set_title('P&L por Posición ($)', fontsize=13, fontweight='bold')
    ax3.set_xlabel('P&L ($)')

    # 4. Key metrics
    ax4 = fig.add_subplot(gs[3, 0])
    ax4.axis('off')
    y_pos = 0.95
    for label, value in metrics:
        color = '#2c3e50'
        if 'Gap' in label and '-' in str(value):
            color = '#e74c3c'
        if 'Alpha' in label:
            try:
                if float(alpha[-1]) > 0:
                    color = '#2ecc71'
                else:
                    color = '#e74c3c'
            except:
                pass
        ax4.text(0.05, y_pos, label, fontsize=11, transform=ax4.transAxes,
                 fontweight='bold', color='#7f8c8d')
        ax4.text(0.65, y_pos, str(value), fontsize=11, transform=ax4.transAxes,
                 fontweight='bold', color=color)
        y_pos -= 0.07
    ax4.set_title('Métricas Clave', fontsize=13, fontweight='bold')

    output_path = os.path.join(IMAGES_DIR, f"analytics_{TODAY}.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"Dashboard saved: {output_path}")
    return output_path


def main():
    # Get data
    positions_data = get_portfolio_data()
    dates, portfolio, sp500 = read_tracker()
    alpha = portfolio[-1] - sp500[-1]

    total_invested = sum(d["amount"] for d in positions_data.values())
    total_pnl = sum(d["pnl"] for d in positions_data.values())
    portfolio_value = total_invested + total_pnl

    metrics = [
        ("Valor Portfolio", f"${portfolio_value:,.0f}"),
        ("P&L Total", f"${total_pnl:+,.1f} ({total_pnl / total_invested * 100:+.1f}%)"),
        ("Alpha vs S&P", f"{alpha:+.1f}pp"),
        ("E[CAGR] Blended", "16.6%"),
        ("Objetivo CAGR", "30%"),
        ("Gap al Objetivo", "-13.4pp"),
        ("Beta Portfolio", "0.627"),
        ("Posiciones", f"{sum(1 for d in positions_data.values() if d['dir'] == 'LONG')}L + {sum(1 for d in positions_data.values() if d['dir'] == 'SHORT')}S"),
        ("Cash", "EUR 424 (4.1%)"),
        ("Max Drawdown", f"{min(portfolio):+.1f}%"),
        ("Sector Views Fresh", "32/33"),
        ("Pipeline (thesis.md)", "139"),
        ("DAs Completados", "45"),
        ("Días hasta Mar 26", str((datetime(2026, 3, 26) - datetime.now()).days)),
    ]

    generate_dashboard(positions_data, dates, portfolio, sp500, metrics)


if __name__ == "__main__":
    main()
