#!/usr/bin/env python3
"""
Daily analytics dashboard — Quant Edition v2.
Full quantitative metrics: Sharpe, Sortino, Calmar, beta, correlation,
volatility (daily/weekly/monthly), drawdown, alpha, information ratio.
Metrics improve as data accumulates. Shows N/A when insufficient data.

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
RF_RATE = 0.045  # risk-free rate annual (US 10Y ~4.5%)


def get_portfolio_data():
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


def resample_weekly(dates, *arrays):
    """Resample daily data to weekly (every 5 trading days + first + last)."""
    n = len(dates)
    if n <= 10:
        return dates, arrays  # too few, return as-is
    indices = [0]
    for i in range(4, n - 1, 5):
        indices.append(i)
    if n - 1 not in indices:
        indices.append(n - 1)
    w_dates = [dates[i] for i in indices]
    w_arrays = tuple(arr[indices] for arr in arrays)
    return w_dates, w_arrays


def safe(val, fmt=".2f", suffix="", prefix="", na="N/A"):
    if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
        return na
    return f"{prefix}{val:{fmt}}{suffix}"


def calc_metrics(port_pcts, sp_pcts, port_vals, sp_vals):
    n = len(port_pcts)
    alpha_series = port_pcts - sp_pcts

    # Daily returns from cumulative %
    port_daily = np.diff(port_pcts) / 100 if n > 1 else np.array([])
    sp_daily = np.diff(sp_pcts) / 100 if n > 1 else np.array([])
    excess = port_daily - sp_daily if len(port_daily) > 0 else np.array([])
    rf_daily = RF_RATE / 252

    # Drawdown
    port_peak = np.maximum.accumulate(port_vals)
    drawdown = (port_vals - port_peak) / port_peak * 100

    m = {}
    m["n_days"] = n
    m["total_return"] = port_pcts[-1] if n > 0 else 0
    m["sp500_return"] = sp_pcts[-1] if n > 0 else 0
    m["alpha_total"] = alpha_series[-1] if n > 0 else 0
    m["max_drawdown"] = drawdown.min() if n > 0 else 0
    m["current_drawdown"] = drawdown[-1] if n > 0 else 0

    # Daily stats
    if len(port_daily) > 0:
        m["avg_daily_return"] = port_daily.mean() * 100
        m["avg_daily_sp"] = sp_daily.mean() * 100
        m["best_day"] = port_daily.max() * 100
        m["worst_day"] = port_daily.min() * 100
        m["winning_days"] = int(sum(port_daily > 0))
        m["losing_days"] = int(sum(port_daily < 0))
        m["win_rate"] = m["winning_days"] / len(port_daily) * 100 if len(port_daily) > 0 else None
    else:
        m["avg_daily_return"] = None
        m["avg_daily_sp"] = None
        m["best_day"] = None
        m["worst_day"] = None
        m["winning_days"] = 0
        m["losing_days"] = 0
        m["win_rate"] = None

    # Volatility
    if len(port_daily) >= 2:
        m["vol_daily"] = port_daily.std() * 100
        m["vol_annual"] = port_daily.std() * np.sqrt(252) * 100
        m["sp_vol_annual"] = sp_daily.std() * np.sqrt(252) * 100
        m["vol_weekly"] = port_daily.std() * np.sqrt(5) * 100 if len(port_daily) >= 5 else None
        m["vol_monthly"] = port_daily.std() * np.sqrt(21) * 100 if len(port_daily) >= 21 else None
    else:
        m["vol_daily"] = None
        m["vol_annual"] = None
        m["sp_vol_annual"] = None
        m["vol_weekly"] = None
        m["vol_monthly"] = None

    # Beta & Correlation
    if len(port_daily) >= 2 and np.var(sp_daily) > 0:
        m["beta"] = np.cov(port_daily, sp_daily)[0, 1] / np.var(sp_daily)
        m["correlation"] = np.corrcoef(port_daily, sp_daily)[0, 1]
        m["r_squared"] = m["correlation"] ** 2
    else:
        m["beta"] = None
        m["correlation"] = None
        m["r_squared"] = None

    # Sharpe Ratio (annualized)
    if len(port_daily) >= 2 and port_daily.std() > 0:
        m["sharpe"] = (port_daily.mean() - rf_daily) / port_daily.std() * np.sqrt(252)
    else:
        m["sharpe"] = None

    # Sortino Ratio (downside deviation only)
    if len(port_daily) >= 2:
        downside = port_daily[port_daily < 0]
        if len(downside) > 0 and downside.std() > 0:
            m["sortino"] = (port_daily.mean() - rf_daily) / downside.std() * np.sqrt(252)
        else:
            m["sortino"] = None
    else:
        m["sortino"] = None

    # Calmar Ratio (return / max drawdown)
    if m["max_drawdown"] < 0 and m["total_return"] != 0:
        m["calmar"] = (m["total_return"] / 100 * 252 / max(n, 1)) / abs(m["max_drawdown"] / 100)
    else:
        m["calmar"] = None

    # Information Ratio
    if len(excess) >= 2 and excess.std() > 0:
        m["info_ratio"] = excess.mean() / excess.std() * np.sqrt(252)
    else:
        m["info_ratio"] = None

    # Tracking Error
    if len(excess) >= 2:
        m["tracking_error"] = excess.std() * np.sqrt(252) * 100
    else:
        m["tracking_error"] = None

    # Up/Down capture
    if len(port_daily) >= 2:
        up_days = sp_daily > 0
        down_days = sp_daily < 0
        if up_days.sum() > 0:
            m["up_capture"] = port_daily[up_days].mean() / sp_daily[up_days].mean() * 100
        else:
            m["up_capture"] = None
        if down_days.sum() > 0:
            m["down_capture"] = port_daily[down_days].mean() / sp_daily[down_days].mean() * 100
        else:
            m["down_capture"] = None
    else:
        m["up_capture"] = None
        m["down_capture"] = None

    return m, drawdown, alpha_series


def generate_dashboard(positions_data, dates, port_vals, port_pcts, sp_vals, sp_pcts):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    m, drawdown, alpha_series = calc_metrics(port_pcts, sp_pcts, port_vals, sp_vals)
    total_invested = sum(d["amount"] for d in positions_data.values())
    total_pnl = sum(d["pnl"] for d in positions_data.values())
    portfolio_value = total_invested + total_pnl

    # Resample to weekly for cleaner charts (metrics use daily data)
    w_dates, (w_port_pcts, w_sp_pcts, w_port_vals, w_drawdown, w_alpha) = resample_weekly(
        dates, port_pcts, sp_pcts, port_vals, drawdown, alpha_series)
    short_dates = [d[5:] for d in w_dates]
    port_pcts_chart = w_port_pcts
    sp_pcts_chart = w_sp_pcts
    port_vals_chart = w_port_vals
    drawdown_chart = w_drawdown
    alpha_chart = w_alpha

    fig = plt.figure(figsize=(16, 48))
    fig.suptitle(f'Portfolio Analytics Dashboard — {TODAY}', fontsize=22, fontweight='bold', y=0.998)
    gs = gridspec.GridSpec(8, 1, hspace=0.3)

    # ── 1. Cumulative Returns ──
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(short_dates, port_pcts_chart, 'b-o', lw=2.5, ms=9, label=f'Portfolio ({port_pcts_chart[-1]:+.1f}%)', zorder=5)
    ax1.plot(short_dates, sp_pcts_chart, 'r--o', lw=2.5, ms=9, label=f'S&P 500 ({sp_pcts_chart[-1]:+.1f}%)', zorder=5)
    ax1.axhline(y=0, color='gray', alpha=0.3)
    ax1.fill_between(range(len(short_dates)), port_pcts_chart, sp_pcts_chart, alpha=0.15,
                     color='red' if port_pcts[-1] < sp_pcts[-1] else 'green')
    for i, (p, s) in enumerate(zip(port_pcts_chart, sp_pcts_chart)):
        ax1.annotate(f'{p:+.1f}%', (i, p), textcoords='offset points', xytext=(0, 12), fontsize=10, color='blue', fontweight='bold')
        ax1.annotate(f'{s:+.1f}%', (i, s), textcoords='offset points', xytext=(0, -18), fontsize=10, color='red', fontweight='bold')
    ax1.set_title('Retorno Acumulado', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylabel('Retorno (%)')

    # ── 2. Alpha ──
    ax2 = fig.add_subplot(gs[1])
    colors_a = ['#2ecc71' if a >= 0 else '#e74c3c' for a in alpha_series]
    ax2.bar(short_dates, alpha_chart, color=colors_a, edgecolor='white', width=0.6)
    ax2.axhline(y=0, color='gray', lw=1)
    for i, a in enumerate(alpha_chart):
        ax2.annotate(f'{a:+.1f}pp', (i, a), textcoords='offset points',
                     xytext=(0, 8 if a >= 0 else -15), fontsize=10, fontweight='bold',
                     color='#2ecc71' if a >= 0 else '#e74c3c')
    ax2.set_title('Alpha vs S&P 500', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Alpha (pp)')
    ax2.grid(True, alpha=0.3, axis='y')

    # ── 3. Drawdown ──
    ax3 = fig.add_subplot(gs[2])
    ax3.fill_between(short_dates, drawdown_chart, 0, color='#e74c3c', alpha=0.3)
    ax3.plot(short_dates, drawdown_chart, 'r-o', lw=2, ms=8)
    ax3.axhline(y=0, color='gray', lw=1)
    for i, dd in enumerate(drawdown_chart):
        if dd < 0:
            ax3.annotate(f'{dd:.1f}%', (i, dd), textcoords='offset points', xytext=(0, -15),
                         fontsize=10, color='#e74c3c', fontweight='bold')
    ax3.set_title(f'Drawdown (Max: {drawdown.min():.1f}%)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Drawdown (%)')
    ax3.grid(True, alpha=0.3)

    # ── 4. Portfolio Value ──
    ax4 = fig.add_subplot(gs[3])
    ax4.plot(short_dates, port_vals_chart, 'b-o', lw=2.5, ms=9)
    ax4.fill_between(short_dates, port_vals_chart, port_vals_chart[0], alpha=0.1,
                     color='green' if port_vals_chart[-1] >= port_vals_chart[0] else 'red')
    for i, v in enumerate(port_vals_chart):
        ax4.annotate(f'${v:,.0f}', (i, v), textcoords='offset points', xytext=(0, 12),
                     fontsize=10, fontweight='bold', color='#2c3e50')
    ax4.set_title('Valor del Portfolio ($)', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Valor ($)')
    ax4.grid(True, alpha=0.3)

    # ── 5. Allocation ──
    ax5 = fig.add_subplot(gs[4])
    tickers_sorted = sorted(positions_data.keys(), key=lambda x: positions_data[x]["amount"], reverse=True)
    pcts_alloc = [positions_data[t]["amount"] / total_invested * 100 for t in tickers_sorted]
    colors_alloc = plt.cm.Set3(np.linspace(0, 1, len(tickers_sorted)))
    bars = ax5.barh(tickers_sorted[::-1], pcts_alloc[::-1], color=colors_alloc[::-1], edgecolor='white')
    for bar, pct, t in zip(bars, pcts_alloc[::-1], tickers_sorted[::-1]):
        d = positions_data[t]
        ax5.text(pct + 0.5, bar.get_y() + bar.get_height() / 2,
                 f'{pct:.1f}% {"(S)" if d["dir"] == "SHORT" else ""}', va='center', fontsize=10, fontweight='bold')
    ax5.set_title('Distribución (%)', fontsize=14, fontweight='bold')
    ax5.set_xlabel('%')

    # ── 6. P&L ──
    ax6 = fig.add_subplot(gs[5])
    tickers_pnl = sorted(positions_data.keys(), key=lambda x: positions_data[x]["pnl"])
    pnl_pcts = [positions_data[t]["pnl"] / positions_data[t]["amount"] * 100 if positions_data[t]["amount"] > 0 else 0
                for t in tickers_pnl]
    pnls = [positions_data[t]["pnl"] for t in tickers_pnl]
    colors_pnl = ['#e74c3c' if v < 0 else '#2ecc71' for v in pnls]
    bars = ax6.barh(tickers_pnl, pnl_pcts, color=colors_pnl, edgecolor='white')
    ax6.axvline(x=0, color='gray', lw=1)
    for bar, pct, val in zip(bars, pnl_pcts, pnls):
        s = '+' if val >= 0 else ''
        ax6.text(pct + (0.3 if pct >= 0 else -0.3), bar.get_y() + bar.get_height() / 2,
                 f'{s}{pct:.1f}% ({s}${val:.0f})', va='center', ha='left' if pct >= 0 else 'right',
                 fontsize=9, fontweight='bold')
    ax6.set_title('P&L por Posición', fontsize=14, fontweight='bold')
    ax6.set_xlabel('P&L (%)')

    # ── 7. Risk-Adjusted Ratios (bar chart) ──
    ax7 = fig.add_subplot(gs[6])
    ratio_names = ['Sharpe', 'Sortino', 'Calmar', 'Info Ratio']
    ratio_vals = [m.get("sharpe"), m.get("sortino"), m.get("calmar"), m.get("info_ratio")]
    ratio_colors = []
    ratio_display = []
    for v in ratio_vals:
        if v is None or np.isnan(v) or np.isinf(v):
            ratio_display.append(0)
            ratio_colors.append('#bdc3c7')
        else:
            ratio_display.append(v)
            ratio_colors.append('#2ecc71' if v > 0 else '#e74c3c')
    bars = ax7.bar(ratio_names, ratio_display, color=ratio_colors, edgecolor='white', width=0.5)
    ax7.axhline(y=0, color='gray', lw=1)
    ax7.axhline(y=1, color='green', lw=0.5, ls='--', alpha=0.5)
    ax7.axhline(y=-1, color='red', lw=0.5, ls='--', alpha=0.5)
    for bar, v, rv in zip(bars, ratio_display, ratio_vals):
        label = f'{v:.2f}' if rv is not None and not np.isnan(rv) else 'N/A'
        ax7.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 label, ha='center', fontsize=11, fontweight='bold')
    ax7.set_title('Ratios Risk-Adjusted', fontsize=14, fontweight='bold')
    ax7.set_ylabel('Ratio')
    ax7.grid(True, alpha=0.3, axis='y')

    # ── 8. Full Metrics Table ──
    ax8 = fig.add_subplot(gs[7])
    ax8.axis('off')

    col1 = [
        ("── RETORNO ──", ""),
        ("Total Return", safe(m["total_return"], "+.2f", "%")),
        ("S&P 500 Return", safe(m["sp500_return"], "+.2f", "%")),
        ("Alpha Total", safe(m["alpha_total"], "+.2f", suffix="pp")),
        ("Media Diaria", safe(m["avg_daily_return"], "+.3f", "%")),
        ("Media Diaria S&P", safe(m["avg_daily_sp"], "+.3f", "%")),
        ("Mejor Día", safe(m["best_day"], "+.2f", "%")),
        ("Peor Día", safe(m["worst_day"], "+.2f", "%")),
        ("Días Ganadores", f"{m['winning_days']}"),
        ("Días Perdedores", f"{m['losing_days']}"),
        ("Win Rate", safe(m["win_rate"], ".0f", "%")),
    ]

    col2 = [
        ("── VOLATILIDAD ──", ""),
        ("Vol Diaria", safe(m["vol_daily"], ".3f", "%")),
        ("Vol Semanal", safe(m["vol_weekly"], ".2f", "%")),
        ("Vol Mensual", safe(m["vol_monthly"], ".1f", "%")),
        ("Vol Anualizada", safe(m["vol_annual"], ".1f", "%")),
        ("Vol S&P Annual", safe(m["sp_vol_annual"], ".1f", "%")),
        ("── DRAWDOWN ──", ""),
        ("Max Drawdown", safe(m["max_drawdown"], ".2f", "%")),
        ("Drawdown Actual", safe(m["current_drawdown"], ".2f", "%")),
        ("", ""),
        ("", ""),
    ]

    col3 = [
        ("── RISK-ADJUSTED ──", ""),
        ("Sharpe Ratio", safe(m["sharpe"], ".2f")),
        ("Sortino Ratio", safe(m["sortino"], ".2f")),
        ("Calmar Ratio", safe(m["calmar"], ".2f")),
        ("Information Ratio", safe(m["info_ratio"], ".2f")),
        ("── VS S&P 500 ──", ""),
        ("Beta", safe(m["beta"], ".3f")),
        ("Correlación", safe(m["correlation"], ".3f")),
        ("R²", safe(m["r_squared"], ".3f")),
        ("Tracking Error", safe(m["tracking_error"], ".1f", "%")),
        ("Up Capture", safe(m["up_capture"], ".0f", "%")),
        ("Down Capture", safe(m["down_capture"], ".0f", "%")),
    ]

    col4 = [
        ("── PORTFOLIO ──", ""),
        ("Valor", f"${portfolio_value:,.0f}"),
        ("P&L Total", f"${total_pnl:+,.1f}"),
        ("P&L %", f"{total_pnl / total_invested * 100:+.2f}%"),
        ("E[CAGR]", "16.6%"),
        ("Objetivo", "30% CAGR"),
        ("Gap", "-13.4pp"),
        ("Cash", "EUR 424 (4.1%)"),
        (f"Posiciones", f"{sum(1 for d in positions_data.values() if d['dir'] == 'LONG')}L + {sum(1 for d in positions_data.values() if d['dir'] == 'SHORT')}S"),
        ("Días Operando", f"{m['n_days']}"),
        ("", ""),
    ]

    for metrics_col, x_off in [(col1, 0.01), (col2, 0.26), (col3, 0.51), (col4, 0.76)]:
        y = 0.95
        for label, value in metrics_col:
            is_hdr = label.startswith("──")
            fs = 10 if is_hdr else 9
            cl = '#2c3e50' if is_hdr else '#7f8c8d'
            cv = '#2c3e50'
            if value == 'N/A':
                cv = '#bdc3c7'
            elif any(k in label for k in ['Alpha', 'Mejor', 'Ganad', 'Win', 'Up Cap']):
                cv = '#2ecc71' if value and '+' in value else '#e74c3c'
            elif any(k in label for k in ['Drawdown', 'Peor', 'Gap', 'Down Cap']):
                cv = '#e74c3c'
            ax8.text(x_off, y, label, fontsize=fs, transform=ax8.transAxes, fontweight='bold', color=cl)
            ax8.text(x_off + 0.15, y, value, fontsize=fs, transform=ax8.transAxes, fontweight='bold', color=cv)
            y -= 0.058

    ax8.set_title('Métricas Cuantitativas Completas', fontsize=14, fontweight='bold')

    if m["n_days"] < 30:
        fig.text(0.5, 0.003,
                 f"⚠️ {m['n_days']} días de datos. Ratios y volatilidades se estabilizarán con ≥30 días de historia.",
                 ha='center', fontsize=11, color='#95a5a6', style='italic')

    output = os.path.join(IMAGES_DIR, f"analytics_{TODAY}.png")
    plt.savefig(output, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    print(f"Dashboard saved: {output}")
    return output


def main():
    positions_data = get_portfolio_data()
    dates, port_vals, port_pcts, sp_vals, sp_pcts = read_tracker()
    generate_dashboard(positions_data, dates, port_vals, port_pcts, sp_vals, sp_pcts)


if __name__ == "__main__":
    main()
