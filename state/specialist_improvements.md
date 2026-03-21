# Specialist Improvements Tracker
# Gobernator manages this file. Angel validates. Changes applied gradually.
# Updated: 2026-03-21

---

## ISSUES (problemas detectados)

| # | Issue | Detectado | Cómo | Impacto | Corregido |
|---|-------|-----------|------|---------|-----------|
| 1 | Batch mode rompe estructura thesis/ | 2026-03-16 | Angel flaggeó | DAs en reports/ no en thesis/ | ✅ Regla creada, rehecho S237-S242 |
| 2 | Dice "done" sin guardar ficheros | 2026-03-15 | objectives_check.py | Trabajo verbal perdido | ✅ Parcial — script detecta, pero patrón recurrente |
| 3 | FX hardcoded en tools (6+ ocurrencias) | 2026-03-15 | Auditoría | FX incorrecto en cálculos GBP | ✅ fx_defaults.py centralizado 11/11 tools |
| 4 | Precios de Wikipedia usados para decisiones | 2026-03-15 | Error Brent $126 | Decisiones basadas en dato erróneo | ✅ Protocolo T1-T4 fuentes creado |
| 5 | IHP.L/MONY.L precios en yaml inconsistentes (GBP vs pence) | 2026-03-20 | Verificación cruzada demo | Confusión en unidades | ✅ Corregido y comentado |
| 6 | CVNA short sin avg_cost_usd en yaml | 2026-03-20 | Verificación cruzada demo | Campo faltante | ✅ Añadido |
| 7 | Evento material NO actualiza documentos formales | 2026-03-21 | Observación | EDEN.PA Brazil: FV recalculado pero thesis/DA/moat no re-run. NVO KC triggered pero DA no re-run. Inconsistente. | ❌ PENDIENTE |
| 8 | R4 committee 100% approval rate | 2026-03-08 | Auditoría | Rubber stamp — la real gate es R2 DA | ❌ PENDIENTE — el committee no rechaza nada |
| 9 | Compra por encima de precios del committee | 2026-03-08 | Autoidentificado | Entra más caro de lo que el comité aprueba | ❌ PENDIENTE |
| 10 | Session continuity no se actualiza al final | 2026-03-17 | Autoidentificado | Pierde contexto entre sesiones | ⚠️ Parcial — mejorado pero no consistente |
| 11 | Nombres inconsistentes en thesis/ (6 nombres para DA, 3 para thesis) | 2026-03-21 | Auditoría | devils_advocate vs r2_devils_advocate vs counter_analysis vs da_analysis vs adversarial_thesis_review vs r2_bear_case. Imposible auditar automáticamente. | ❌ PENDIENTE |
| 12 | Ficheros legacy en thesis/ (triage.md, screening_*.md, system_*.md) | 2026-03-21 | Auditoría | Ruido de versiones anteriores. No siguen template. Confunden. | ❌ PENDIENTE — borrar lo que no sirva |

---

## MEJORAS (mejoras propuestas, no errores)

| # | Mejora | Propuesta | Por qué | Prioridad | Estado |
|---|--------|-----------|---------|-----------|--------|
| M1 | Protocolo formal para evento material en posición activa | 2026-03-21 | Cuando algo cambia (news, KC, earnings): ¿qué documentos se re-run? ¿thesis? ¿DA? ¿moat? ¿risk? No existe protocolo claro. | ALTA | ❌ PENDIENTE |
| M2 | Baskets organizados por megatrends seculares, no geografía | 2026-03-20 | US Quality, UK Quality son geográficos. D&A Monopolies y Cybersecurity (temáticos) son más fuertes. | MEDIA | ❌ PENDIENTE — pactado "no ahora" |
| M3 | R4 committee con poder de RECHAZO real | 2026-03-21 | 100% approval = rubber stamp. El committee debería rechazar candidatos que no cumplen estrictamente. | MEDIA | ❌ PENDIENTE |
| M4 | Top 20 "world class" watchlist | 2026-03-19 | Empresas como AAPL, MSFT, V que nunca aparecen en fallen_angels pero que compraríamos si caen 40%+. Tener análisis pre-hecho. | BAJA | ❌ PENDIENTE — reflexión con Angel: no necesario, R1-R4 tarda 30 min |
| M5 | Contrathesis periódica para posiciones activas | 2026-03-21 | Las DAs se hacen en R2 (antes de comprar) pero no se re-run periódicamente. Una posición puede deteriorarse sin que nadie desafíe la tesis. | ALTA | ❌ PENDIENTE |
| M6 | Smart money alerts automáticos | 2026-03-21 | Si un insider vende >$1M o short interest sube >20%, alerta automática en vez de esperar el daily scan. | MEDIA | ❌ PENDIENTE |
| M7 | Portfolio NAV tracking integrado | 2026-03-18 | portfolio_nav.py creado pero no integrado en session protocol. Debería correr automáticamente. | BAJA | ⚠️ Parcial — tool creado, no integrado |
| M8 | Stress test post-evento automático | 2026-03-21 | Stress test es semanal. Debería correr TAMBIÉN después de cualquier evento material (Iran strikes, FOMC, etc.). | MEDIA | ❌ PENDIENTE |
| M9 | Kill conditions monitoreadas en tiempo real, no daily | 2026-03-21 | kc_monitor.py corre 1-2x/día. Si un KC triggerea a las 10:00 y no lo vemos hasta las 18:00, perdemos 8 horas. | BAJA | ❌ PENDIENTE |
| M10 | DA re-run periódico para posiciones >30 días | 2026-03-21 | La tesis original puede tener asunciones que ya no son válidas. DA periódico (mensual) forzaría re-evaluación. Similar a M5. | ALTA | ❌ PENDIENTE |
| M11 | Estandarizar nombres ficheros thesis/ | 2026-03-21 | 7 nombres únicos: thesis.md, moat_assessment.md, risk_assessment.md, devils_advocate.md, r3_resolution.md, committee_decision.md, earnings_framework.md. Desde ahora todo nuevo usa estos nombres. Migrar viejo gradualmente. | **CRÍTICA** | ❌ PENDIENTE |
| M12 | _TEMPLATE.md para cada tipo de documento | 2026-03-21 | Cada agente tiene una plantilla fija. Todos los documentos del mismo tipo tienen la misma estructura. Auditable. | **CRÍTICA** | ❌ PENDIENTE |
| M13 | Limpieza ficheros legacy | 2026-03-21 | Borrar o archivar ficheros que no siguen el estándar y no aportan valor (triage.md, screening_*.md, system_*.md). Lo viejo que no compensa se elimina. | MEDIA | ❌ PENDIENTE |
| M14 | Meta-reflexiones no se leen ni se actúan | 2026-03-21 | Los agentes detectan anomalías, hacen preguntas, sugieren mejoras al sistema. NADIE las revisa. HLNE: receivables 67% vs revenue 28% sin investigar. DOCS: sugirió sector view digital health, no creado. HLNE: sugirió quality_scorer asset manager mode, no implementado. Las meta-reflexiones son texto muerto. | **CRÍTICA** | ❌ PENDIENTE |
| M15 | Protocolo de revisión de meta-reflexiones | 2026-03-21 | Después de cada R1/R2/R4, el especialista LEE la meta-reflexión y resuelve cada pregunta/anomalía/sugerencia. No avanzar con dudas sin resolver. Cerrar el loop con el sub-agente si hace falta. | **CRÍTICA** | ❌ PENDIENTE |
| M16 | R3 resolución necesita meta-reflexión propia | 2026-03-21 | R1 tiene (5/5), DA tiene (12/13), Committee tiene (4/5), pero R3 tiene 0/9. El CIO no reflexiona sobre sus propias decisiones. Debería. | **ALTA** | ❌ PENDIENTE |
| M17 | Todos los sub-agentes deben tener meta-reflexión | 2026-03-21 | moat-assessor, risk-identifier también deberían reflexionar. La meta-reflexión es el mecanismo de conversación sub-agente ↔ orquestador. Sin ella, el sub-agente no puede señalar problemas. | **ALTA** | ❌ PENDIENTE |
| M18 | Loop de meta-reflexión: sub-agente → orquestador → acción | 2026-03-21 | El sistema actual es: sub-agente reflexiona → nadie lee → texto muerto. Debería ser: sub-agente reflexiona → orquestador lee → resuelve/actúa/mejora sistema → feedback al sub-agente. | **CRÍTICA** | ❌ PENDIENTE |

---

## PRINCIPIO FUNDAMENTAL

**Agentes > Tools.** Si un problema se puede resolver mejorando un agente (que razona, adapta, meta-reflexiona) NO crear un nuevo tool (que es código estático, puede fallar silenciosamente, no piensa). Tools = datos y cálculos. Agentes = juicio e inteligencia. Menos tools, mejores agentes.

## PLAN DE APLICACIÓN

Aplicar gradualmente, no todo de golpe. Angel valida cada mejora.

**Semana 1 (próxima):** M1 (protocolo evento material) + Issue 7
**Semana 2:** M5 + M10 (DA periódico posiciones activas)
**Semana 3:** M3 (R4 committee con rechazo)
**Semana 4:** M6 + M8 (alerts + stress test automático)

Angel valida cada mejora antes de implementar.
