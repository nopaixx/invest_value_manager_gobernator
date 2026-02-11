# Adversarial Review — Consolidación Final

> **Fecha:** 2026-02-09
> **Ejecutado por:** Especialista (invest_value_manager) via pipeline adversarial (3 agentes independientes)
> **Gobernado por:** Gobernator (verificación de principios en cada resultado)
> **Posiciones revisadas:** 11 (todo el portfolio activo)

---

## Tabla de Resultados

| Ticker | Veredicto | FV Thesis | FV Adversarial | Delta | MoS Real | Counter | QS Thesis→Adv |
|--------|-----------|-----------|----------------|-------|----------|---------|---------------|
| **HRB** | **SELL** | $59.58 | $33.94 | **-43%** | 3% | 18/24 | — |
| **NVO** | **SELL/REDUCE** | DKK 491 | DKK 280 | **-43%** | **-15%** | ~22/24 | 82→70 (Tier B) |
| BME.L | CANCELAR ORDER | 321p | 258p | -19.6% | — | 14/24 | — |
| UTG.L | CANCELAR ORDER | 745p | 615p | -17.4% | 12% | 13/24 | Tier D(27)/C(adj) |
| LULU | HOLD PROBATION | $261 | $207 | -21% | 16% | ~15/24 | 82→72 (Tier B) |
| DOM.L | HOLD PROBATION LOW | 294p | 235p | -20% | — | 18/24 | 61 |
| BYIT.L | HOLD PROBATION LOW | 455p | 340-370p | -20% | 10-17% | 18/24 | 81→68-72 (Tier B) |
| AUTO.L | HOLD PROBATION LOW | 688p | 550-580p | -16% | 12-16% | 17/24 | 79→68 (Tier B) |
| SAN.PA | HOLD PROBATION LOW | EUR 127 | EUR 115 | -9.8% | 30% | 16/24 | 9/10→59 (Tier B) |
| ADBE | HOLD MED | $394 | $340 | -14% | 21% | 18/24 | 76→76 (frontera A/B) |

**Ya vendidas (fases 1-2):** A2A.MI, VNA.DE, TATE.L

---

## Acciones para eToro

### Inmediatas
1. **SELL HRB** — moat invalidado (Intuit 600 oficinas), FV real $33.94, MoS 3%
2. **CANCELAR standing order BME.L** — FV -19.6%, governance rota, ROIC 30→12%
3. **CANCELAR standing order UTG.L** — FV -17.4%, QS Tier D, MoS insuficiente

### Decisión de Angel
4. **NVO: SELL o esperar CagriSema (marzo 2026)?** — FV -43%, MoS negativo (-15%), kill condition ~39% market share. Pérdida si vendes ahora: ~$4. CagriSema es binario (30-35% positivo, 25-30% negativo).

### FREEZE ADD Triggers
5. **LULU** — $160 y $145 triggers suspendidos. Next review: post Q4 (31 Mar)
6. **AUTO.L** — 450p trigger suspendido. Test: April 2026 pricing event
7. **BYIT.L** — 260p trigger suspendido. Next review: FY2026 results (~May 2026)

### Reclasificaciones
8. **De Tier A a Tier B:** NVO, LULU, AUTO.L, BYIT.L, SAN.PA
9. **ADBE** se mantiene en frontera A/B (QS 76 confirmado por tool, pero decelerando)

---

## Hallazgos Clave por Posición

### HRB — SELL (mayor discrepancia junto con NVO)
- Moat "red de oficinas irreplicable" → Intuit replicó 600 oficinas en un trimestre
- Management destruyó $413M en buybacks a $51 avg (acción a $33)
- Net debt estacional: $2.59B en diciembre vs ~$1.7B normalizada. Si normalizada, FV ~$41 (MoS ~20%)

### NVO — SELL/REDUCE (el más crítico)
- FCF thesis DKK 87B "normalizado" vs DKK 28.3B real reportado (3x inflado)
- CEO forzado a salir, 6 board members reemplazados, 9,000 despidos — NO mencionado en thesis
- Kill condition market share <40% posiblemente incumplida (~39%)
- CagriSema: cross-trial 22.7% vs Zepbound 25.3% — gap desfavorable
- 13 riesgos no documentados (2 CRITICAL, 5 HIGH)

### SAN.PA — HOLD PROBATION LOW
- QS thesis "9/10 Tier A" era fabricado (scoring ad-hoc). Tool da 59 Tier B
- ROIC real 8% = WACC (thesis decía 10-12%). Zero economic profit
- Riesgos: Dupixent mass tort (300+ eventos adversos, primera demanda Oct 2025), antitrust UE, pipeline fracasos
- SELL si: black box warning Dupixent, dividend cut, precio >EUR 90

### ADBE — HOLD MEDIUM
- QS 76 Tier A confirmado (único que sobrevive), pero frontera A/B por deceleración ARR (5 trimestres consecutivos)
- Error factual: thesis citaba revenue FY2024 como FY2025
- Riesgos: FTC lawsuit suscripciones, copyright class-action Firefly, Canva/Affinity GRATIS (1M signups en 4 días)
- ADD trigger revisado: $220-230 (antes $250)

### LULU — HOLD PROBATION
- Crisis gobernanza triple: sin CEO (40 días) + Wilson proxy fight + Elliott $1B activismo
- EPS thesis $14.50 vs guidance real $12.92-13.02 (-10%)
- Tariff impact 3x mayor que thesis ($320M vs "~100bp marginal")
- DTC market share cayó de 30% a 24% en 3 meses
- Se compró SIN pipeline adversarial completo

### AUTO.L — HOLD PROBATION LOW
- Deal Builder = single point of failure (5 riesgos correlados: CMA complaint, ARPR deceleration, Facebook Marketplace Pro, multiple compression)
- FV 550-580p (thesis 688p). A 484p, MoS solo 12-16%
- April 2026 pricing event (5.5% increase) es el test decisivo
- Candidata a rotación cuando haya alternativa Tier A

### BYIT.L — HOLD PROBATION LOW
- Microsoft eliminando canal EA = estructural, no cíclico (68% del GII es Microsoft)
- Insider ownership thesis 9.6% es FALSO (real 0.5-1.5%)
- Comparable central incorrecto: Softcat a 17.7x, no 25x
- FV 340-370p (thesis 455p), MoS 10-17%

### DOM.L — HOLD PROBATION LOW
- FV 294→235p (-20%). Conviction LOW
- SELL si: FY25 EBITDA<125M o no CEO Sep 2026
- FY25 results: 5 Mar 2026

### BME.L — CANCELAR ORDER
- Governance rota: sin CFO, 3 profit warnings, EY review pendiente
- ROIC colapsado 30%→12%
- Thesis incompleta (sin sector view, sin kill conditions)

### UTG.L — CANCELAR ORDER
- QS real: Tier D(27 raw) / Tier C(REIT-adjusted). Thesis decía Tier B
- Triple-hit inmigración: visa cuts + dependents ban + GBP 925 levy
- Error factual: bond GBP 275M vence Oct 2028, thesis decía "no maturities until 2029"

---

## Patrones Sistémicos Detectados

1. **FV inflado en promedio -25%** — todas las thesis sobreestiman fair value
2. **QS sistemáticamente inflado** — 5 de 6 posiciones bajan de Tier A a Tier B tras adversarial
3. **FCF inflado es el error más destructivo** — NVO (3x inflado), HRB (buybacks no descontados)
4. **Riesgos no documentados** — promedio 8-13 riesgos HIGH/CRITICAL no mencionados por thesis
5. **Thesis sin pipeline adversarial = errores factuales** — EPS incorrectos, insider ownership falso, comparables desactualizados, revenue dates equivocadas
6. **Thesis más viejas = peores discrepancias** — v2.0 tiene los mayores deltas (-43%)
7. **Pipeline adversarial valida su valor** — LULU y AUTO.L compradas sin pipeline = errores que se habrían detectado

---

## Calendario de Catalizadores

| Fecha | Evento | Posición | Impacto |
|-------|--------|----------|---------|
| 23 Feb | MONY.L earnings | — | Info |
| 5 Mar | DOM.L FY25 results | DOM.L | SELL trigger si EBITDA<125M |
| Mar 2026 | CagriSema REDEFINE 4 | NVO | Kill-or-cure |
| 31 Mar | LULU Q4 earnings | LULU | CEO + product refresh test |
| 1 Apr | AUTO.L pricing event | AUTO.L | Deal Builder friction test |
| May 2026 | BYIT.L FY2026 results | BYIT.L | H2 performance |
