#!/usr/bin/env python3
"""
Daily analytics dashboard generator — Quant Edition.
Generates multi-panel analytics: returns, alpha, drawdown, allocation, P&L, risk metrics.
Metrics improve as more daily data accumulates.

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
    dates, port_vals, port_pcts, sp_vals, sp_pcts = [], [], [], [], []
    with open(TRACKER_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dates.append(row["date"])
            port_vals.append(float(row["portfolio_value"]))
            port_pcts.append(float(row["portfolio_pnl_pct"]))
            sp_vals.append(float(row["sp500"]) if row["sp500"] else 0)
            sp_pcts.append(float(row["sp500_pnl_pct"]) if row["sp500_pnl_pct"] else 0)
    return dates, np.array(port_vals), np.array(port_pcts), np.array(sp_vals), np.array(sp_pcts)


def calc_quant_metrics(port_pcts, sp_pcts, port_vals):
    """Calculate quant metrics from daily data."""
    n = len(port_pcts)
    alpha = port_pcts - sp_pcts

    # Daily returns (from cumulative)
    port_daily = np.diff(port_pcts) if n > 1 else np.array([0])
    sp_daily = np.diff(sp_pcts) if n > 1 else np.array([0])

    # Drawdown series
    port_peak = np.maximum.accumulate(port_vals)
    drawdown = (port_vals - port_peak) / port_peak * 100

    metrics = {
        "total_return": port_pcts[-1],
        "sp500_return": sp_pcts[-1],
        "alpha": alpha[-1],
        "max_drawdown": drawdown.min(),
        "current_drawdown": drawdown[-1],
        "days": n,
        "winning_days": sum(1 for d in port_daily if d > 0) if n > 1 else 0,
        "losing_days": sum(1 for d in port_daily if d < 0) if n > 1 else 0,
        "best_day": port_daily.max() if n > 1 else 0,
        "worst_day": port_daily.min() if n > 1 else 0,
        "avg_daily": port_daily.mean() if n > 1 else 0,
        "volatility": port_daily.std() * np.sqrt(252) if n > 2 else 0,
        "sp_volatility": sp_daily.std() * np.sqrt(252) if n > 2 else 0,
        "beta": np.cov(port_daily, sp_daily)[0, 1] / np.var(sp_daily) if n > 2 and np.var(sp_daily) > 0 else 0.627,
        "sharpe": (port_daily.mean() * 252) / (port_daily.std() * np.sqrt(252)) if n > 2 and port_daily.std() > 0 else 0,
        "information_ratio": (np.mean(port_daily - sp_daily) * 252) / (np.std(port_daily - sp_daily) * np.sqrt(252)) if n > 2 and np.std(port_daily - sp_daily) > 0 else 0,
        "tracking_error": np.std(port_daily - sp_daily) * np.sqrt(252) if n > 2 else 0,
    }
    return metrics, drawdown, alpha


def generate_dashboard(positions_data, dates, port_vals, port_pcts, sp_vals, sp_pcts):
    """Generate multi-panel analytics dashboard."""
    os.makedirs(IMAGES_DIR, exist_ok=True)

    qmetrics, drawdown, alpha_series = calc_quant_metrics(port_pcts, sp_pcts, port_vals)
    total_invested = sum(d["amount"] for d in positions_data.values())
    total_pnl = sum(d["pnl"] for d in positions_data.values())
    portfolio_value = total_invested + total_pnl

    short_dates = [d[5:] for d in dates]

    fig = plt.figure(figsize=(14, 36))
    fig.suptitle(f'Portfolio Analytics — {TODAY}', fontsize=20, fontweight='bold', y=0.995)
    gs = gridspec.GridSpec(6, 1, hspace=0.35)

    # ── 1. Cumulative Returns vs S&P 500 ──
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(short_dates, port_pcts, 'b-o', linewidth=2.5, markersize=9, label=f'Portfolio ({port_pcts[-1]:+.1f}%)', zorder=5)
    ax1.plot(short_dates, sp_pcts, 'r--o', linewidth=2.5, markersize=9, label=f'S&P 500 ({sp_pcts[-1]:+.1f}%)', zorder=5)
    ax1.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    ax1.fill_between(range(len(short_dates)), port_pcts, sp_pcts, alpha=0.15,
                     color='red' if port_pcts[-1] < sp_pcts[-1] else 'green')
    for i, (p, s) in enumerate(zip(port_pcts, sp_pcts)):
        ax1.annotate(f'{p:+.1f}%', (i, p), textcoords='offset points', xytext=(0, 12),
                     fontsize=10, color='blue', fontweight='bold')
        ax1.annotate(f'{s:+.1f}%', (i, s), textcoords='offset points', xytext=(0, -18),
                     fontsize=10, color='red', fontweight='bold')
    ax1.set_title('Retorno Acumulado vs S&P 500', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=12, loc='best')
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel('Retorno (%)')

    # ── 2. Alpha (outperformance) ──
    ax2 = fig.add_subplot(gs[1, 0])
    colors_alpha = ['#2ecc71' if a >= 0 else '#e74c3c' for a in alpha_series]
    ax2.bar(short_dates, alpha_series, color=colors_alpha, edgecolor='white', linewidth=0.5, width=0.6)
    ax2.axhline(y=0, color='gray', linewidth=1)
    for i, a in enumerate(alpha_series):
        ax2.annotate(f'{a:+.1f}pp', (i, a), textcoords='offset points',
                     xytext=(0, 8 if a >= 0 else -15), fontsize=10, fontweight='bold',
                     color='#2ecc71' if a >= 0 else '#e74c3c')
    ax2.set_title('Alpha vs S&P 500 (Outperformance)', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Alpha (pp)')
    ax2.grid(True, alpha=0.3, axis='y')

    # ── 3. Drawdown ──
    ax3 = fig.add_subplot(gs[2, 0])
    ax3.fill_between(short_dates, drawdown, 0, color='#e74c3c', alpha=0.3)
    ax3.plot(short_dates, drawdown, 'r-o', linewidth=2, markersize=8)
    ax3.axhline(y=0, color='gray', linewidth=1)
    for i, dd in enumerate(drawdown):
        if dd < 0:
            ax3.annotate(f'{dd:.1f}%', (i, dd), textcoords='offset points',
                         xytext=(0, -15), fontsize=10, color='#e74c3c', fontweight='bold')
    ax3.set_title(f'Drawdown (Max: {drawdown.min():.1f}%)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Drawdown (%)')
    ax3.grid(True, alpha=0.3)

    # ── 4. Portfolio Allocation ──
    ax4 = fig.add_subplot(gs[3, 0])
    tickers_sorted = sorted(positions_data.keys(), key=lambda x: positions_data[x]["amount"], reverse=True)
    amounts = [positions_data[t]["amount"] for t in tickers_sorted]
    pcts = [a / total_invested * 100 for a in amounts]
    colors_alloc = plt.cm.Set3(np.linspace(0, 1, len(tickers_sorted)))
    bars = ax4.barh(tickers_sorted[::-1], pcts[::-1], color=colors_alloc[::-1], edgecolor='white', linewidth=0.5)
    for bar, pct, ticker in zip(bars, pcts[::-1], tickers_sorted[::-1]):
        d = positions_data[ticker]
        label = f'{pct:.1f}% ({"S" if d["dir"] == "SHORT" else "L"})'
        ax4.text(pct + 0.5, bar.get_y() + bar.get_height() / 2, label,
                 va='center', fontsize=10, fontweight='bold')
    ax4.set_title('Distribución del Portfolio (%)', fontsize=14, fontweight='bold')
    ax4.set_xlabel('% del Portfolio')

    # ── 5. P&L by Position ──
    ax5 = fig.add_subplot(gs[4, 0])
    tickers_pnl = sorted(positions_data.keys(), key=lambda x: positions_data[x]["pnl"])
    pnls = [positions_data[t]["pnl"] for t in tickers_pnl]
    pnl_pcts = [positions_data[t]["pnl"] / positions_data[t]["amount"] * 100 if positions_data[t]["amount"] > 0 else 0
                for t in tickers_pnl]
    colors_pnl = ['#e74c3c' if v < 0 else '#2ecc71' for v in pnls]
    bars = ax5.barh(tickers_pnl, pnl_pcts, color=colors_pnl, edgecolor='white', linewidth=0.5)
    ax5.axvline(x=0, color='gray', linewidth=1)
    for bar, pct, val in zip(bars, pnl_pcts, pnls):
        sign = '+' if val >= 0 else ''
        ax5.text(pct + (0.3 if pct >= 0 else -0.3), bar.get_y() + bar.get_height() / 2,
                 f'{sign}{pct:.1f}% ({sign}${val:.0f})', va='center',
                 ha='left' if pct >= 0 else 'right', fontsize=9, fontweight='bold')
    ax5.set_title('P&L por Posición (% y $)', fontsize=14, fontweight='bold')
    ax5.set_xlabel('P&L (%)')

    # ── 6. Quant Metrics Dashboard ──
    ax6 = fig.add_subplot(gs[5, 0])
    ax6.axis('off')

    # Two columns of metrics
    left_metrics = [
        ("── RETORNO ──", ""),
        ("Retorno Total", f"{qmetrics['total_return']:+.2f}%"),
        ("S&P 500", f"{qmetrics['sp500_return']:+.2f}%"),
        ("Alpha", f"{qmetrics['alpha']:+.2f}pp"),
        ("Días Operando", f"{qmetrics['days']}"),
        ("Días Ganadores", f"{qmetrics['winning_days']}"),
        ("Días Perdedores", f"{qmetrics['losing_days']}"),
        ("Mejor Día", f"{qmetrics['best_day']:+.2f}%"),
        ("Peor Día", f"{qmetrics['worst_day']:+.2f}%"),
    ]

    right_metrics = [
        ("── RIESGO ──", ""),
        ("Max Drawdown", f"{qmetrics['max_drawdown']:.2f}%"),
        ("Drawdown Actual", f"{qmetrics['current_drawdown']:.2f}%"),
        ("Volatilidad (ann.)", f"{qmetrics['volatility']:.1f}%"),
        ("S&P Vol (ann.)", f"{qmetrics['sp_volatility']:.1f}%"),
        ("Beta", f"{qmetrics['beta']:.3f}"),
        ("Sharpe Ratio", f"{qmetrics['sharpe']:.2f}"),
        ("Information Ratio", f"{qmetrics['information_ratio']:.2f}"),
        ("Tracking Error", f"{qmetrics['tracking_error']:.1f}%"),
    ]

    portfolio_metrics = [
        ("── PORTFOLIO ──", ""),
        ("Valor", f"${portfolio_value:,.0f}"),
        ("P&L Total", f"${total_pnl:+,.1f}"),
        ("E[CAGR] Blended", "16.6%"),
        ("Objetivo", "30% CAGR"),
        ("Gap", "-13.4pp"),
        ("Cash", "EUR 424 (4.1%)"),
        ("Posiciones", f"{sum(1 for d in positions_data.values() if d['dir'] == 'LONG')}L + {sum(1 for d in positions_data.values() if d['dir'] == 'SHORT')}S"),
    ]

    y_pos = 0.95
    for metrics_col, x_offset in [(left_metrics, 0.02), (right_metrics, 0.35), (portfolio_metrics, 0.68)]:
        y = y_pos
        for label, value in metrics_col:
            is_header = label.startswith("──")
            color_l = '#2c3e50' if is_header else '#7f8c8d'
            color_v = '#2c3e50'
            if 'Alpha' in label and value and '-' not in value:
                color_v = '#2ecc71'
            elif ('Drawdown' in label or 'Gap' in label or 'Peor' in label) and value and '-' in value:
                color_v = '#e74c3c'
            elif 'Mejor' in label or 'Ganadores' in label:
                color_v = '#2ecc71'
            fs = 11 if is_header else 10
            ax6.text(x_offset, y, label, fontsize=fs, transform=ax6.transAxes,
                     fontweight='bold', color=color_l)
            ax6.text(x_offset + 0.22, y, value, fontsize=fs, transform=ax6.transAxes,
                     fontweight='bold', color=color_v)
            y -= 0.065

    ax6.set_title('Métricas Cuantitativas', fontsize=14, fontweight='bold')

    # Note about data maturity
    if qmetrics['days'] < 30:
        fig.text(0.5, 0.005, f"⚠️ Solo {qmetrics['days']} días de datos. Sharpe, IR, volatilidad mejorarán con más historia.",
                 ha='center', fontsize=10, color='#95a5a6', style='italic')

    output_path = os.path.join(IMAGES_DIR, f"analytics_{TODAY}.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"Dashboard saved: {output_path}")
    return output_path


def main():
    positions_data = get_portfolio_data()
    dates, port_vals, port_pcts, sp_vals, sp_pcts = read_tracker()
    generate_dashboard(positions_data, dates, port_vals, port_pcts, sp_vals, sp_pcts)


if __name__ == "__main__":
    main()
