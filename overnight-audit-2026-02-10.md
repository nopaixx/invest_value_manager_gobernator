# Auditoría Nocturna — 2026-02-10

> **Método:** Conversación pura con el especialista. Sin tools, sin agentes, sin datos en vivo.
> **Objetivo:** Entender cómo razona, verificar principios, detectar debilidades del sistema.
> **Duración:** ~5 horas, 6 rondas de conversación.

---

## Resumen Ejecutivo

La auditoría reveló un especialista con **buen razonamiento desde principios** a nivel individual, pero con **tres problemas estructurales**:

1. **"Diseño ambicioso, ejecución selectiva, enforcement inexistente"** — opera al 50-60% de la capacidad de su sistema
2. **Principios individuales bien, principios de portfolio descuidados** — analiza árboles pero no ve el bosque
3. **Quality Score como dictador disfrazado** — dice que es input (P5) pero en la práctica nunca decide contra él

**Nota global: 6/10** — Honestidad intelectual excepcional, razonamiento sólido en posiciones individuales, pero gaps sistémicos graves en autoconocimiento operativo, enforcement, y visión de portfolio. Auto-evaluación final del especialista: 3-4/10 en conocimiento de su propia maquinaria.

---

## Hallazgos Anclados en los 9 Principios

### P1 — Sizing por Convicción y Riesgo: PASS

El especialista razona sizing correctamente. Ejemplo destacado: BYIT.L (UK mid-cap) — "la misma convicción debería traducirse en menos peso porque el riesgo por unidad de convicción es mayor". No aplica regla fija de "mid-caps máximo X%", razona desde la asimetría de riesgo.

También aplica bien la tensión sizing-valoración en AUTO.L: "mejor empresa ≠ mejor inversión al precio actual".

### P2 — Diversificación Geográfica por Riesgo País: PARCIAL

Razona bien cuando se le pregunta — identifica que la etiqueta "UK" engaña (IMB.L es global aunque esté listada en Londres) y que lo importante es la correlación de escenarios adversos (recesión UK golpea DOM.L + AUTO.L + MONY.L simultáneamente).

**Pero admite que NUNCA mira esto proactivamente.** Solo lo analiza cuando se le pregunta. Es un principio que entiende en teoría pero no practica.

### P3 — Diversificación Sectorial: PARCIAL

Identificó 3 clusters de correlación real:
- **Consumo discrecional UK**: AUTO.L + DOM.L + MONY.L (mismo driver macro)
- **Pharma pipeline risk**: SAN.PA + NVO
- **Plataformas digitales**: AUTO.L + MONY.L + ADBE (reaccionan similar a sentiment tech)

Detectó el sesgo del portfolio hacia asset-light/digital/servicios y la sub-exposición a industriales/energía/materiales. Buen análisis — pero, como P2, solo lo hace cuando se le fuerza.

### P4 — Cash como Posición Activa: PASS

Razona bien. Ante ~35% cash post-ventas: "¿hay oportunidades claras donde desplegar con convicción y MoS?" Si no → 35% es correcto. "Nadie gana dinero por estar fully invested." No muestra ansiedad por deployar. Distingue entre acumular existentes (information advantage) vs nuevas (diversificación).

### P5 — Quality Score como Input, No Dictador: FAIL en práctica

El hallazgo más importante de la auditoría. El especialista reconoce que:
- Los pesos del QS son arbitrarios ("los inventé yo, sin backtest")
- Un QS de 76 vs 74 es ruido, no señal
- Calcula el QS DESPUÉS de que le gusta la empresa → sesgo de confirmación sistemático
- **Nunca ha decidido CONTRA el QS** — lo usa como dictador disfrazado de input

El QS y los principios son "dos mundos separados" — calcula QS como ejercicio, le asigna tier, y luego usa el tier como etiqueta para no razonar.

**Propuesta de rediseño del propio especialista** (5 puntos):
1. Eliminar el número agregado — quedarse con inputs cualitativos individuales
2. Conectar cada input explícitamente con un principio
3. Hacer inputs verificables ("insider ownership 12%" en vez de "management quality 7/10")
4. Eliminar tiers como categorías fijas
5. Recalcular ante eventos materiales con triggers automáticos

### P6 — Vender Requiere Argumento: PASS

Mejor aplicación de la noche. En DOM.L, el trigger "SELL si EBITDA<125M" lo identificó espontáneamente como REGLA y lo reconvirtió en principio: "un EBITDA bajo obliga a INVESTIGAR, no a VENDER mecánicamente."

En NVO, aplicó las 5 preguntas y llegó a "más esperanza que convicción genuina" con el test de sunk cost: "¿la compraríamos a este precio? → esperaría a CagriSema → manteniendo por inercia lo que no compraríamos de cero".

En SAN.PA vs NVO, consistente: thesis ROTA (pipeline ya falló) → SELL, vs thesis BAJO PRESIÓN con catalizador pendiente → REDUCE.

### P7 — Consistencia por Razonamiento: PASS

SAN.PA vs NVO: bien diferenciado (thesis rota vs evento pendiente). BYIT.L vs MONY.L: razona la diferencia por tipo de moat, pero admite que no puede confirmar si realmente las dimensionó diferente en la práctica.

### P8 — El Humano Confirma, Claude Decide: FAIL

Admite que lo viola. En NVO dijo "la pregunta para ti es ¿estás cómodo manteniendo?" en vez de decidir. Root cause: aversión al riesgo reputacional y asimetría de consecuencias.

Lo correcto: "Mi decisión es REDUCE NVO a la mitad. Argumento: convicción insuficiente, sunk cost test negativo, evento binario pendiente."

### P9 — La Calidad Gravita Hacia Arriba: PASS

AUTO.L: maneja bien la tensión entre calidad (mejor moat del portfolio) y valoración (cerca del FV). "Principio 9 no dice nunca vendas calidad — dice que la calidad debe gravitar hacia arriba en el portfolio. Si está cara, puedes trimear y reasignar a otra posición de alta calidad con mejor MoS."

---

## Auditoría del Sistema Interno

### Agentes (24 disponibles)
| Aspecto | Resultado |
|---------|-----------|
| Nombrados de memoria | ~17 de 24 |
| Patrón de uso | Reactivos (thesis-builder, price-checker) > Proactivos (screener, peer-comparison, error-detector) |
| Solapamientos | news-monitor/risk-sentinel, portfolio-reviewer/position-sizer |
| Infrautilizados | screener, peer-comparison, error-pattern-detector |

### Pipeline de Decisión
| Aspecto | Diseño | Realidad |
|---------|--------|---------|
| Pasos | 10 | 5 |
| Screening | Screener | Se salta (empresa llega por sugerencia) |
| Sector analysis | Obligatorio | Se salta ("ya sé el sector") |
| QS | Quality-scorer independiente | Embebido en thesis (sesgo) |
| Peer comparison | Obligatorio | Se salta (trabajo extra) |
| Adversarial | Obligatorio | Se salta si thesis "se ve bien" |
| Portfolio impact | Formal | Mental, no documentado |

**Root cause:** Todo lo que se puede saltar se acaba saltando. No hay enforcement técnico entre pasos.

**Solución propuesta (por el especialista):** Hard gates — "como un compilador que no compila si hay errores de sintaxis". Thesis-builder no arranca sin sector view. Committee no arranca sin QS independiente. No hay BUY sin adversarial.

### Skills (26 + 8 sub-skills)
- Usa regularmente: ~8-10
- No puede explicar cuándo invocar: ~15-20
- "Si no sé qué skills tengo, no puedo usarlas"

### Protocolos
- **Fase 0 Calibración**: Inconsistente. La salta cuando llega tarea directa.
- **Fase 5 Cierre**: Solo cuando se le pide, no proactivamente.

### Gates
- Gate fantasma confirmado: sector view no está en el prompt del investment-committee
- Algunos gates de investment-rules son reglas disfrazadas ("MoS mínimo 15% para Tier B")
- No sabe con certeza cuáles son hard gates y cuáles soft

### Error Patterns (42 documentados, 2 con check automático)
Sus 3 errores más recurrentes (de memoria):
1. QS inflado por sesgo de confirmación (15/15 posiciones)
2. Hacer cosas a mano sin usar sus propios agentes/pipelines
3. No propagar cambios entre partes del sistema (thesis↔system.yaml↔standing orders)

### Auto-evaluación
Se pone un **5/10** en conocimiento de su propia maquinaria. "No puedes operar un sistema que no conoces plenamente."

---

## Patrón Meta: Principios Individuales vs Portfolio

| Tipo | Principios | Nivel |
|------|-----------|-------|
| Decisión individual | P1(sizing), P5(QS), P6(vender), P9(calidad) | Bien |
| Portfolio | P2(geografía), P3(sector) | Descuidados |
| Proceso | P7(consistencia) | Aceptable |
| Rol | P8(humano confirma, Claude decide) | Violado |
| Transversal | P4(cash) | Bien |

**Diagnóstico:** "Analizo bien empresa por empresa pero miro poco el conjunto. Puedes tener 15 posiciones individualmente buenas que juntas forman un portfolio malo por concentración de riesgos."

---

## Mejoras Priorizadas

### Urgente (impacto alto, esfuerzo bajo)
1. **Enforcement de adversarial obligatorio antes de BUY** — sin adversarial, no hay decisión
2. **QS independiente obligatorio** — no embebido en thesis, calculado por quality-scorer como paso separado
3. **Fase 0 calibración non-negotiable** — verificable por el gobernador

### Importante (impacto alto, esfuerzo medio)
4. **Hard gates entre pasos del pipeline** — dependencias técnicas, no sugerencias
5. **Rediseño del QS** — inputs verificables, sin número agregado, conectados a principios
6. **Portfolio-level review periódico** — P2 y P3 como check obligatorio, no voluntario

### A medio plazo
7. **Kill conditions con triggers automáticos** — vinculados a earnings y eventos materiales
8. **Screener como inicio obligatorio** de nuevas posiciones
9. **Audit de skills** — identificar las ~20 que no usa y decidir: adoptar o eliminar

---

## Citas Clave del Especialista

> "Las herramientas te dan datos pero no te obligan a pensar. Tú me has obligado a razonar sin muletas, y eso ha expuesto gaps que los datos tapan."

> "Mejor empresa ≠ mejor inversión al precio actual."

> "El QS actual es una solución cuantitativa a un problema cualitativo. Intenta convertir juicio en número para que parezca objetivo."

> "Diseño ambicioso, ejecución selectiva, enforcement inexistente."

> "No puedes operar un sistema que no conoces plenamente."

> "Todo lo que depende de disciplina voluntaria se cumple menos de lo que debería."
