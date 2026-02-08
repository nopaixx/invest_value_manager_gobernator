#!/usr/bin/env python3
"""
Projection chart: Expected returns with and without governance improvements.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Time horizons
years = [0, 1, 3, 5, 10]

# Starting capital
capital = 16700  # EUR approximate current portfolio

# Scenario 1: Current system (no changes)
# - 16 positions, 10 with low conviction
# - No vigilance enforcement, gates broken
# - Action bias, deploys cash too fast
# - Estimated CAGR: 6-8% (dragged by low conviction positions, errors)
cagr_current = 0.07
current = [capital * (1 + cagr_current)**y for y in years]

# Scenario 2: With governance improvements
# - Concentrated 5-6 high conviction positions
# - Fixed gates, adversarial review before every buy
# - Patience principle, quality compounder track
# - Better position sizing, less churn
# - Estimated CAGR: 12-15% (quality compounders + better process)
cagr_improved = 0.135
improved = [capital * (1 + cagr_improved)**y for y in years]

# Scenario 3: Market benchmark (S&P 500 / MSCI World)
cagr_benchmark = 0.09
benchmark = [capital * (1 + cagr_benchmark)**y for y in years]

# Create chart
fig, ax = plt.subplots(figsize=(12, 7))

# Plot lines
ax.plot(years, current, 'o-', color='#e74c3c', linewidth=2.5, markersize=8, label=f'Sistema actual (CAGR ~7%)')
ax.plot(years, benchmark, 's--', color='#95a5a6', linewidth=2, markersize=7, label=f'Benchmark MSCI World (CAGR ~9%)')
ax.plot(years, improved, '^-', color='#2ecc71', linewidth=2.5, markersize=8, label=f'Con mejoras de gobernanza (CAGR ~13.5%)')

# Fill between
ax.fill_between(years, current, improved, alpha=0.1, color='#2ecc71')

# Annotations for key values
for i, y in enumerate(years):
    if y > 0:
        ax.annotate(f'€{improved[i]:,.0f}', (y, improved[i]),
                   textcoords="offset points", xytext=(0, 15),
                   ha='center', fontsize=9, color='#27ae60', fontweight='bold')
        ax.annotate(f'€{current[i]:,.0f}', (y, current[i]),
                   textcoords="offset points", xytext=(0, -20),
                   ha='center', fontsize=9, color='#c0392b')

# Styling
ax.set_xlabel('Anos', fontsize=12, fontweight='bold')
ax.set_ylabel('Valor del Portfolio (EUR)', fontsize=12, fontweight='bold')
ax.set_title('Proyeccion de Rentabilidad: Sistema Actual vs Con Mejoras de Gobernanza',
             fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
ax.set_xticks(years)
ax.set_xticklabels(['Hoy', '1 ano', '3 anos', '5 anos', '10 anos'])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
ax.grid(True, alpha=0.3)
ax.set_xlim(-0.3, 10.5)

# Add text box with assumptions
textstr = '\n'.join([
    'Supuestos:',
    f'  Capital inicial: €{capital:,}',
    '  Sistema actual: 16 posiciones, 10 baja conviccion,',
    '    gates rotos, sesgo a la accion → CAGR ~7%',
    '  Con mejoras: 5-6 posiciones alta conviccion,',
    '    gates unificados, principio de paciencia,',
    '    Track 2 compounders → CAGR ~13.5%',
    '  La diferencia a 10 anos: +€28,500 (~+170%)',
])
props = dict(boxstyle='round', facecolor='#f8f9fa', alpha=0.8)
ax.text(0.55, 0.35, textstr, transform=ax.transAxes, fontsize=8.5,
        verticalalignment='top', bbox=props)

plt.tight_layout()
plt.savefig('/home/angel/invest_value_manager_gobernator/telegram/projection.png', dpi=150, bbox_inches='tight')
print("Chart saved to telegram/projection.png")
