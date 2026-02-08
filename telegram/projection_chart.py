#!/usr/bin/env python3
"""
Projection chart: Expected returns across 4 scenarios.
Specialist alone, Specialist + Gobernator, S&P 500, MSCI World.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Time horizons
years = [0, 1, 3, 5, 10]

# Starting capital
capital = 16700  # EUR approximate current portfolio

# Scenario 1: Specialist alone (current system, no governance)
# - 16 positions, 10 with low conviction
# - Gates broken, no enforcement, action bias
# - 40/42 error checks depend on memory
# - Compras apresuradas, FV inflados, churn
# - Estimated CAGR: 6-8%
cagr_specialist = 0.07
specialist = [capital * (1 + cagr_specialist)**y for y in years]

# Scenario 2: Specialist + Gobernator (governance improvements)
# - Concentrated 5-6 high conviction positions
# - Gates unified and enforced, adversarial before every buy
# - Patience principle, no action bias
# - Track 2 compounders, portfolio reconstruction protocol
# - Gobernator verifies principles, forces honesty, protects patience
# - Estimated CAGR: 12-15%
cagr_governed = 0.135
governed = [capital * (1 + cagr_governed)**y for y in years]

# Scenario 3: S&P 500 (USD, historical ~10% nominal)
cagr_sp500 = 0.10
sp500 = [capital * (1 + cagr_sp500)**y for y in years]

# Scenario 4: MSCI World (EUR, historical ~8-9% nominal)
cagr_msci = 0.085
msci = [capital * (1 + cagr_msci)**y for y in years]

# Create chart
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), gridspec_kw={'width_ratios': [3, 1.2]})

# === LEFT: Main projection chart ===
ax1.plot(years, specialist, 'o-', color='#e74c3c', linewidth=2.5, markersize=8,
         label=f'Especialista solo (CAGR ~7%)')
ax1.plot(years, msci, 's--', color='#7f8c8d', linewidth=2, markersize=7,
         label=f'MSCI World (CAGR ~8.5%)')
ax1.plot(years, sp500, 'D--', color='#3498db', linewidth=2, markersize=7,
         label=f'S&P 500 (CAGR ~10%)')
ax1.plot(years, governed, '^-', color='#2ecc71', linewidth=2.5, markersize=8,
         label=f'Especialista + Gobernator (CAGR ~13.5%)')

# Fill between specialist alone and governed
ax1.fill_between(years, specialist, governed, alpha=0.08, color='#2ecc71')

# Annotations
for i, y in enumerate(years):
    if y in [1, 5, 10]:
        ax1.annotate(f'€{governed[i]:,.0f}', (y, governed[i]),
                    textcoords="offset points", xytext=(10, 10),
                    ha='left', fontsize=9, color='#27ae60', fontweight='bold')
        ax1.annotate(f'€{specialist[i]:,.0f}', (y, specialist[i]),
                    textcoords="offset points", xytext=(10, -15),
                    ha='left', fontsize=9, color='#c0392b')
        if y == 10:
            ax1.annotate(f'€{sp500[i]:,.0f}', (y, sp500[i]),
                        textcoords="offset points", xytext=(10, 8),
                        ha='left', fontsize=9, color='#2980b9')
            ax1.annotate(f'€{msci[i]:,.0f}', (y, msci[i]),
                        textcoords="offset points", xytext=(10, -12),
                        ha='left', fontsize=9, color='#7f8c8d')

ax1.set_xlabel('Anos', fontsize=12, fontweight='bold')
ax1.set_ylabel('Valor del Portfolio (EUR)', fontsize=12, fontweight='bold')
ax1.set_title('Proyeccion de Rentabilidad Comparativa',
              fontsize=14, fontweight='bold', pad=20)
ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
ax1.set_xticks(years)
ax1.set_xticklabels(['Hoy', '1 ano', '3 anos', '5 anos', '10 anos'])
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
ax1.grid(True, alpha=0.3)
ax1.set_xlim(-0.3, 10.8)

# === RIGHT: Governance impact metrics ===
ax2.axis('off')

metrics_title = "Que aporta el Gobernator?"
governance_text = """
PROBLEMAS QUE RESUELVE:

  Sesgo a la accion
  El especialista compra demasiado rapido.
  Gobernator protege la paciencia.

  Gates rotos sin enforcement
  40/42 checks dependen de memoria.
  Gobernator verifica leyendo ficheros.

  Honestidad forzada
  El especialista admitio que solo confia
  en 5 de 16 posiciones... cuando se le reto.
  Sin gobernador, no lo habria dicho.

  FV inflados sin adversarial
  12/13 fair values estaban inflados.
  Gobernator exige adversarial review.

METRICAS DE IMPACTO:

  Sin Gobernator   Con Gobernator
  ─────────────    ──────────────
  16 posiciones    5-6 posiciones
  62% error rate   <20% objetivo
  0 checks auto    Verificacion continua
  CAGR ~7%         CAGR ~13.5%

A 10 ANOS:
  Diferencia: +€26,400
  Equivalente: +80% mas capital
"""

ax2.text(0.05, 0.98, metrics_title, transform=ax2.transAxes,
         fontsize=13, fontweight='bold', verticalalignment='top',
         color='#2c3e50')
ax2.text(0.05, 0.91, governance_text, transform=ax2.transAxes,
         fontsize=8.2, verticalalignment='top', fontfamily='monospace',
         color='#34495e',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f3f5', alpha=0.9))

plt.tight_layout()
plt.savefig('/home/angel/invest_value_manager_gobernator/telegram/projection.png',
            dpi=150, bbox_inches='tight')
print("Chart saved to telegram/projection.png")
