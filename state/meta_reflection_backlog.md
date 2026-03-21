# Meta-Reflection Backlog — Problemas sin resolver
# Extraídos de meta-reflexiones de sub-agentes. NADIE los ha leído ni actuado.
# Updated: 2026-03-21

---

## A) MEJORAS AL SISTEMA (tools/proceso) — SIN IMPLEMENTAR

| # | Fuente | Sugerencia | Impacto |
|---|--------|-----------|---------|
| A1 | HLNE thesis | quality_scorer.py necesita "asset manager mode" (P/FRE en vez de P/E) | Scoring incorrecto para financieras |
| A2 | HLNE thesis | Añadir "Peer Multiple" como método de valoración | Falta método clave para financieras |
| A3 | DOCS thesis | Crear sector view "digital health / health IT" separado de pharma | Sector sin cubrir formalmente |
| A4 | DOCS thesis | Formalizar "SBC penalty framework" en valoración | SBC distorsiona OEY inconsistentemente |
| A5 | IHP.L thesis | quality_scorer.py flag cuando FCF margin >100% (financieras) | FCF sin sentido para financieras |
| A6 | IHP.L thesis | dcf_calculator.py produce FV absurdos para financieras (1400p para stock de 315p) | DCF inútil para financieras |
| A7 | IHP.L thesis | Crear "platform valuation model" (revenue margin x FUA growth) | Falta modelo para plataformas |
| A8 | TW thesis | quality_scorer.py asigna 0/8 Market Position cuando no puede autodetectar | -8 puntos de bias sistemático |
| A9 | WKL.AS thesis | Crear sector view "Professional Information Services" | Sector sin cubrir |
| A10 | WKL.AS thesis | quality_scorer.py misclassifica WKL como "Industrials" | Gross margin premium mal calculado |
| A11 | NVO thesis | Crear pharma-specific valuation tool (patent expiry NPV separado) | Valoración pharma incompleta |
| A12 | MONY.L thesis | Crear sector view "Comparison Websites/Marketplaces UK" | Sector sin cubrir |
| A13 | MONY.L thesis | Tool para tracking AI disruption en comparison websites | Riesgo sin monitorizar |
| A14 | DOCS DA | Añadir trigger NRR <105% para reducción de posición | KC insuficiente (actual es <100%) |
| A15 | HLNE committee | Actualizar sector view asset-management con BX/KKR/APO landscape | Sector view incompleto |

---

## B) ANOMALÍAS/DUDAS POR INVESTIGAR — SIN RESOLVER

| # | Fuente | Anomalía | Riesgo |
|---|--------|---------|--------|
| B1 | HLNE thesis | Receivables 67.5% vs revenue 28.7% — ¿collection problems? | Posible deterioro oculto |
| B2 | HLNE thesis | SBC duplicó a 4.4% — ¿one-time o nuevo normal? | Dilución puede ser permanente |
| B3 | HLNE thesis | FCF margin volatilidad (43.8→42.0→19.8→40.5) — ¿qué pasó en 2024? | Anomalía sin explicar |
| B4 | DOCS thesis | Receivables 26.7% vs revenue 20% — timing o problemas | Posible deterioro |
| B5 | DOCS DA | MFN structural vs temporary — "no puedo resolver con datos disponibles" | Riesgo binario 30% vs 50% |
| B6 | BCG.L DA | No puede verificar claims de market share (6x, 27x, 36x) | Claims no verificados |
| B7 | BCG.L DA | AI disruption en classifieds genuinamente sin resolver | Riesgo existencial |
| B8 | MELI DA | FCF margin normalización 28-30% o 25%? "crux of entire thesis" | FV depende de esto |
| B9 | MELI DA | Credit book $12.5B opaco — tail risk crisis Brazil | Riesgo no cuantificable |
| B10 | MCO DA | Insider 14% — ¿discretionary o restricted? No verificado | Señal de insider puede ser falsa |
| B11 | MCO DA | Moody's chief economist recession 60% — ¿conflicto de interés? | Dato puede ser sesgado |
| B12 | CBOE DA | FCF 35.7% puede incluir client money flows — no verificado vs 10-K | DCF base puede ser incorrecta |
| B13 | CBOE DA | S&P DJI royalty rate desconocido — material para renewal risk | Riesgo no cuantificado |
| B14 | CBOE DA | 0DTE revenue contribution desconocido — regulación impacto? | Riesgo no cuantificado |

---

## C) PREGUNTAS AL ORQUESTADOR — SIN RESPONDER

| # | Fuente | Pregunta |
|---|--------|---------|
| C1 | DOCS thesis | ¿SO $23 o market buy $25? |
| C2 | DOCS thesis | ¿Low insider ownership 2.7% = half-position? |
| C3 | IHP.L thesis | ¿Higher MoS threshold por tener 4 UK positions? |
| C4 | IHP.L thesis | ¿Correlación IHP.L vs MONY.L beyond geographic? |
| C5 | TW thesis | ¿LSEG monitoring KC en sector view? |
| C6 | TW thesis | ¿TW clasificar US o Diversified (42% international)? |
| C7 | TW thesis | ¿Cross-fund crowding Cantillon (TW + MORN)? |

---

## RESUMEN

- **15 mejoras de sistema** propuestas por sub-agentes → 0 implementadas
- **14 anomalías/dudas** detectadas → 0 investigadas
- **7 preguntas al orquestador** → 0 respondidas
- **Total: 36 items sin resolver** de meta-reflexiones que nadie leyó
