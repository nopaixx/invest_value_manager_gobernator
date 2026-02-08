#!/usr/bin/env python3
"""
Projection charts: Expected returns across 4 scenarios.
Generates 2 images: without contributions and with €1,000/month.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = '/home/angel/invest_value_manager_gobernator/telegram'

# Config
capital = 16700
monthly = 1000
years_points = [0, 1, 3, 5, 10]

scenarios = [
    ('Especialista solo',          0.07,  'o-',  '#e74c3c', 2.5, 8),
    ('MSCI World',                 0.085, 's--', '#7f8c8d', 2.0, 7),
    ('S&P 500',                    0.10,  'D--', '#3498db', 2.0, 7),
    ('Especialista + Gobernator',  0.135, '^-',  '#2ecc71', 2.5, 8),
]

def calc_no_contrib(cagr, years):
    return [capital * (1 + cagr)**y for y in years]

def calc_with_contrib(cagr, years):
    results = []
    monthly_rate = (1 + cagr) ** (1/12) - 1
    for y in years:
        months = y * 12
        val = capital * (1 + monthly_rate) ** months
        for m in range(1, months + 1):
            val += monthly * (1 + monthly_rate) ** (months - m)
        results.append(val)
    return results

def make_chart(title, data_func, filename, subtitle=''):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8),
                                    gridspec_kw={'width_ratios': [3, 1.2]})

    all_vals = {}
    for name, cagr, style, color, lw, ms in scenarios:
        vals = data_func(cagr, years_points)
        all_vals[name] = vals
        pct = f'{cagr*100:.1f}'
        ax1.plot(years_points, vals, style, color=color, linewidth=lw,
                 markersize=ms, label=f'{name} (CAGR ~{pct}%)')

    # Fill between worst and best
    ax1.fill_between(years_points, all_vals[scenarios[0][0]],
                     all_vals[scenarios[-1][0]], alpha=0.08, color='#2ecc71')

    # Annotations at key years
    for i, y in enumerate(years_points):
        if y in [1, 5, 10]:
            # Governed (top)
            gov_val = all_vals[scenarios[-1][0]][i]
            ax1.annotate(f'€{gov_val:,.0f}', (y, gov_val),
                        textcoords="offset points", xytext=(10, 10),
                        ha='left', fontsize=9, color='#27ae60', fontweight='bold')
            # Specialist alone (bottom)
            spec_val = all_vals[scenarios[0][0]][i]
            ax1.annotate(f'€{spec_val:,.0f}', (y, spec_val),
                        textcoords="offset points", xytext=(10, -15),
                        ha='left', fontsize=9, color='#c0392b')
            if y == 10:
                sp_val = all_vals['S&P 500'][i]
                ax1.annotate(f'€{sp_val:,.0f}', (y, sp_val),
                            textcoords="offset points", xytext=(10, 8),
                            ha='left', fontsize=9, color='#2980b9')
                msci_val = all_vals['MSCI World'][i]
                ax1.annotate(f'€{msci_val:,.0f}', (y, msci_val),
                            textcoords="offset points", xytext=(10, -12),
                            ha='left', fontsize=9, color='#7f8c8d')

    ax1.set_xlabel('Anos', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Valor del Portfolio (EUR)', fontsize=12, fontweight='bold')
    ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)
    if subtitle:
        ax1.text(0.5, 1.01, subtitle, transform=ax1.transAxes,
                fontsize=10, ha='center', color='#555555', style='italic')
    ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax1.set_xticks(years_points)
    ax1.set_xticklabels(['Hoy', '1 ano', '3 anos', '5 anos', '10 anos'])
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'€{x:,.0f}'))
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-0.3, 10.8)

    # Right panel: governance metrics
    ax2.axis('off')
    gov_10 = all_vals[scenarios[-1][0]][-1]
    spec_10 = all_vals[scenarios[0][0]][-1]
    sp_10 = all_vals['S&P 500'][-1]
    diff_spec = gov_10 - spec_10
    diff_sp = gov_10 - sp_10

    metrics_title = "Que aporta el Gobernator?"
    governance_text = f"""
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

  FV inflados sin adversarial
  12/13 fair values estaban inflados.
  Gobernator exige adversarial review.

METRICAS DE IMPACTO:

  Sin Gobernator   Con Gobernator
  -------------    --------------
  16 posiciones    5-6 posiciones
  62% error rate   <20% objetivo
  0 checks auto    Verificacion continua
  CAGR ~7%         CAGR ~13.5%

A 10 ANOS:
  vs Especialista solo: +€{diff_spec:,.0f}
  vs S&P 500:           +€{diff_sp:,.0f}
"""

    ax2.text(0.05, 0.98, metrics_title, transform=ax2.transAxes,
             fontsize=13, fontweight='bold', verticalalignment='top',
             color='#2c3e50')
    ax2.text(0.05, 0.91, governance_text, transform=ax2.transAxes,
             fontsize=8.2, verticalalignment='top', fontfamily='monospace',
             color='#34495e',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f3f5', alpha=0.9))

    plt.tight_layout()
    path = f'{OUT_DIR}/{filename}'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {path}')

# Generate both charts
make_chart(
    'Proyeccion de Rentabilidad Comparativa',
    calc_no_contrib,
    'projection.png',
    subtitle=f'Capital inicial: €{capital:,} | Sin aportaciones adicionales'
)

make_chart(
    'Proyeccion con Aportaciones de €1,000/mes',
    calc_with_contrib,
    'projection_contributions.png',
    subtitle=f'Capital inicial: €{capital:,} + €{monthly:,}/mes (€{monthly*12:,}/ano)'
)

print('Done - both charts generated.')
