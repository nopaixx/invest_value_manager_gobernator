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

### PRÓXIMA: M19 — Templates + meta-reflexión para TODOS los agentes
**Problema:** Solo thesis/ (R1-R4) tiene templates y nombres canónicos. Pero hay 24 agentes que generan outputs en world/sectors/, reports/, state/. Sector views, smart money, stress tests — sin template, sin meta-reflexión, sin nombres estándar. Caos potencial fuera de thesis/.
**Prioridad:** CRÍTICA — es la extensión natural de IMP-2.
**Enfoque:** El especialista identifica todos los outputs de sus 24 agentes, define canonical names + templates + meta-reflexión donde haya juicio. Gobernator audita.

### PENDIENTE: M5+M10 — DA periódico posiciones activas
**Problema:** Tesis envejecen sin re-challenge. DA solo se hace pre-compra (R2), nunca después.
**Prioridad:** ALTA.

### PENDIENTE: M3+Issue 8 — R4 committee con rechazo real
**Problema:** 100% approval rate = rubber stamp.
**Prioridad:** MEDIA.

### PENDIENTE: Issue 12+M13 — Limpieza legacy
**Problema:** Ficheros viejos con nombres incorrectos, ruido.
**Prioridad:** BAJA — hacer cuando lo nuevo funcione.

### PENDIENTE: M2 — Baskets por megatrends
**Problema:** Baskets por geografía en vez de temas seculares.
**Prioridad:** BAJA — pactado "no ahora".

### PENDIENTE: M6 — Smart money alerts automáticos
**Prioridad:** MEDIA.

### PENDIENTE: M8 — Stress test post-evento
**Prioridad:** MEDIA.

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
