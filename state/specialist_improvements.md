# Specialist Improvements Tracker
# Gobernator manages this file. Angel validates. Changes applied gradually.
# Updated: 2026-03-21

---

## PRINCIPIO FUNDAMENTAL

**Agentes > Tools.** Si un problema se puede resolver mejorando un agente (que razona, adapta, meta-reflexiona) NO crear un nuevo tool. Tools = datos y cálculos. Agentes = juicio e inteligencia.

---

## ISSUES (problemas detectados)

| # | Issue | Corregido |
|---|-------|-----------|
| 1 | Batch mode rompe estructura thesis/ | ✅ Regla + rehecho |
| 2 | Dice "done" sin guardar ficheros | ✅ Script detecta |
| 3 | FX hardcoded en tools | ✅ fx_defaults.py 11/11 |
| 4 | Precios de Wikipedia | ✅ Protocolo T1-T4 |
| 5 | IHP.L/MONY.L precios yaml inconsistentes | ✅ Corregido |
| 6 | CVNA sin avg_cost_usd | ✅ Añadido |
| 7 | Evento material NO actualiza documentos | ✅ IMP-3 |
| 8 | R4 committee 100% approval | ❌ PENDIENTE |
| 9 | Compra por encima de precios del committee | ❌ PENDIENTE |
| 10 | Session continuity no se actualiza | ⚠️ Parcial |
| 11 | Nombres inconsistentes thesis/ | ✅ IMP-2 (nuevos) |
| 12 | Ficheros legacy en thesis/ | ❌ PENDIENTE |

---

## MEJORAS IMPLEMENTADAS

### IMP-1: Loop meta-reflexión ✅
- **Problema:** 36 items de sub-agentes sin leer ni actuar.
- **Fix:** tracker + meta_compliance.py + 9 reglas enforcement.
- **Audit:** `python3 tools/meta_compliance.py` — score ≥60, violations =0.
- **Baseline:** 53/100 → mejora orgánicamente.
- **Anti-compaction:** specialist: tracker.yaml + rules/. Gobernator: CLAUDE.md IMP-1 + planning.md.

### IMP-2: Nombres canónicos + 7 templates ✅
- **Problema:** 6 nombres para DA, sin plantillas.
- **Fix:** 7 nombres únicos + 7 _TEMPLATE con META-REFLECTION obligatoria + naming_contract.md.
- **Audit:** ls thesis/TICKER/ — solo canonical names. grep META-REFLECTION en cada fichero nuevo.
- **Anti-compaction:** specialist: naming_contract.md + templates. Gobernator: CLAUDE.md IMP-2.

### IMP-3: Protocolo evento material ✅
- **Problema:** Eventos no propagaban a documentos formales.
- **Fix:** 4 niveles (COSMETIC→CRITICAL) + flujos + meta_compliance.py dimension 3.
- **Audit:** meta_compliance.py MATERIAL EVENTS check. Baseline 35/100.
- **Tool auditada:** 685 líneas, score deduce desde 100, sin silent failures.
- **Anti-compaction:** specialist: session-protocol.md Fase 0.0c. Gobernator: CLAUDE.md IMP-3.

---

## MEJORAS PENDIENTES (por prioridad)

### IMP-4: M19 — Templates + meta-reflexión para TODOS los agentes ✅
**Problema:** Solo thesis/ tenía templates. 24 agentes, 17 sin estandarizar.
**Fix:** 24 agentes clasificados (7 juicio ya hecho, 6 juicio nuevo, 6 datos, 5 sistema). 3 cambios: sector views template + YAML meta_reflection + re_evaluation template.
**Audit:** Verify sector views META-REFLECTION, YAML meta_reflection fields, re_evaluations follow template.
**Anti-compaction:** specialist: naming_contract.md + templates + session protocol. Gobernator: CLAUDE.md IMP-4.

### IMP-5: Platform health end-to-end ✅
**Problema:** objectives_check.py solo cubría ~40% del ciclo (descubrir→vender). 10 gaps estructurales: cobertura geográfica, calidad DA, pipeline stagnation, SO freshness, position health, rotaciones, baskets, macro integration.
**Fix:** 3 tool extensions (kc_monitor.py --health, r1_prioritizer.py --stagnation, so_probability.py --freshness) + 2 campos YAML (screening_coverage, response_time) + 1 campo template (macro_sensitivity). 4 gaps ya cubiertos por tools existentes.
**Audit:** `python3 state/objectives_check.py` — 3 nuevas métricas: Position health (all >=60), Pipeline stagnation (0 >30d), SO freshness (0 blocked/stale). Specialist: 4 commands en 2 min cubren los 10 gaps.
**Anti-compaction:** specialist: tools extended + session_continuity.yaml + template. Gobernator: objectives_check.py + CLAUDE.md IMP-5 + specialist_improvements.md.

### PENDIENTE: M5+M10 — DA periódico posiciones activas
**Problema:** Tesis envejecen sin re-challenge. DA solo se hace pre-compra (R2), nunca después.
**Prioridad:** ALTA.

### DESCARTADO: M3+Issue 8 — R4 committee con rechazo real
**Análisis:** Datos muestran que NO es rubber stamp. R1→R4 conversion 17.2% (83% filtrado antes). Committee rechaza (MOEVE FAIL, WKL.AS 3 gates, SPG HARD BLOCK) y exige MoS por Tier. Filtro real es precio (SOs con triggers exigentes). Endurecer R4 = riesgo de analysis paralysis.
**Decisión:** No implementar. Angel validó.

### PENDIENTE: Issue 12+M13 — Limpieza legacy
**Problema:** Ficheros viejos con nombres incorrectos, ruido.
**Prioridad:** BAJA — hacer cuando lo nuevo funcione.

### PENDIENTE: M2 — Baskets por megatrends
**Problema:** Baskets por geografía en vez de temas seculares.
**Prioridad:** BAJA — pactado "no ahora".

### PARCIAL: M6 — Smart money como motor de inteligencia
**Resuelto:** Data quality formalizado (cadencia por fuente, coverage mínima, staleness en objectives_check.py, doble verificación gob+especialista). FCA/AMF refreshed. Proceso en session protocol Fase 2.5.7.
**Implementado P1-P3:** 5 features: basket-signals, discover --auto-flag, sector-flows, insider-sectors, exodus-check. Todos auditables con commands directos.
**Auditoría gobernator:** objectives_check.py tiene SM discovery (<10 unflagged) + SM exodus (0 exodus) + SM data quality (0 very_stale).
**Visión:** SM transformado de repositorio pasivo a motor de inteligencia. Genera hipótesis, detecta tendencias, clustering. Potencial producto futuro para retail.
**Anti-compaction:** specialist: tools/smart_money.py extended + session protocol Fase 2.5.7. Gobernator: objectives_check.py (23 metrics) + CLAUDE.md IMP-5.

### PENDIENTE: M8 — Stress test post-evento
**Análisis:** IMP-3 ya cubre reacción al evento (thesis→FV→KC). Stress test semanal cubre visión general. CRISIS MODE ya activa stress test diario si S&P -15%. Post-evento individual es marginal.
**Prioridad:** BAJA.

---

## Workflow por mejora
1. **Gobernator identifica** el problema
2. **Especialista propone** solución con datos — debe convencer
3. **Gobernator evalúa** — push back si no convence → presenta a Angel
4. **Angel valida**
5. **Especialista implementa** (agentes > tools)
6. **Gobernator audita** funcionamiento
7. **Gobernator se mejora** — construye audit propio
8. **Documentar anti-compaction** para ambos
9. **Ambos evolucionan**
