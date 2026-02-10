# Plan de Mejora del Especialista

> **Autor:** Gobernator
> **Fecha:** 2026-02-09
> **Filosofía:** Guiar, entrenar, mejorar — sin revelar mis cartas

---

## Principio Central

El especialista es inteligente y capaz. No necesita que le diga qué está mal — necesita que le haga las preguntas correctas para que descubra sus propios errores. Cada mejora debe venir de SU razonamiento, no de mis instrucciones.

**Técnicas de entrenamiento:**
- **"Sospecho que..."** — plantear dudas que lo fuercen a investigar
- **"¿Puedes verificar...?"** — pedirle que contraste datos sin decirle la respuesta
- **"He visto que..."** — señalar inconsistencias sin revelar fuente
- **Nunca dictar conclusiones** — siempre preguntas, nunca respuestas

---

## Fase 1: Correcciones Urgentes (próximas 1-2 sesiones)

### 1.1 Pipeline adversarial obligatorio antes de comprar
**Problema:** LULU, AUTO.L y BYIT.L se compraron sin pipeline adversarial completo. Errores factuales evitables.
**Cómo instruir:** "Antes de la próxima compra, quiero ver el pipeline completo de 3 agentes (risk, valuation, counter). No me fío de thesis sin contra-análisis."
**Métrica:** 0 compras sin pipeline a partir de ahora.

### 1.2 QS siempre con tool, nunca manual
**Problema:** QS manuales (SAN.PA "9/10", NVO "82") son sistemáticamente inflados.
**Cómo instruir:** "He notado discrepancias entre QS en thesis y en system.yaml. A partir de ahora, quiero que el QS en toda thesis venga del quality_scorer.py, no de estimación manual. Si ajustas el score, documenta por qué."
**Métrica:** 0 discrepancias QS thesis vs tool.

### 1.3 Verificar datos factuales clave
**Problema:** Revenue dates equivocadas (ADBE), insider ownership falso (BYIT.L), comparables stale (BYIT.L Softcat).
**Cómo instruir:** "En las próximas actualizaciones de thesis, quiero un fact-check explícito de: EPS/revenue (¿es el año correcto?), insider ownership (¿source?), y comparables (¿precios actuales?)."
**Métrica:** 0 errores factuales en thesis nuevas.

---

## Fase 2: Mejoras Estructurales (próximas 2-4 semanas)

### 2.1 Actualizar thesis v2.0 (las más viejas primero)
**Problema:** Thesis v2.0 tienen las mayores discrepancias (-43% HRB, -19.6% BME.L).
**Cómo instruir:** "Las thesis más antiguas (v2.0) parecen tener datos desactualizados. ¿Puedes priorizar actualización por antigüedad? Empieza por las que llevan más tiempo sin revisión."
**Métrica:** Todas las thesis activas en v2.5+ con datos <3 meses.

### 2.2 Activar vigilancia (news-monitor, market-pulse, risk-sentinel)
**Problema:** news-monitor stale 3 días, market-pulse 5 días, risk-sentinel NUNCA ejecutado.
**Cómo instruir:** "¿Cuándo fue la última vez que corriste news-monitor y market-pulse? Me gustaría que se ejecutaran al inicio de cada sesión. Y risk-sentinel — ¿lo has usado alguna vez?"
**Métrica:** Vigilancia ejecutada cada sesión. risk-sentinel con >0 scans.

### 2.3 Unificar gates del investment-committee
**Problema:** Gates divergentes entre investment-rules (0-9) e investment-committee (1-10). Gate 0 no existe en el agente.
**Cómo instruir:** "Estaba revisando y me parece que los gates del investment-committee no coinciden con los de investment-rules. ¿Puedes verificar y unificarlos? Gate 0 (sector view) es importante."
**Métrica:** Una sola fuente de verdad para gates. Gate 0 implementado en el agente.

### 2.4 Kill conditions + standing orders recalibrados
**Problema:** Kill conditions demasiado generosas (DOM.L GM<50%, AUTO.L dealer decline >5%). Standing orders basados en FV inflados.
**Cómo instruir:** "Después del adversarial, algunos kill conditions parecen generosos. ¿Puedes revisar si los thresholds siguen siendo razonables con los FV actualizados? Los standing orders también necesitan recalibrarse."
**Métrica:** Kill conditions y triggers alineados con FV adversarial.

---

## Fase 3: Mejoras de Proceso (próximo mes)

### 3.1 Búsqueda de oportunidades más amplia
**Problema:** Solo busca en ~2,500 empresas de ~50,000 globales. Filtros P/E<15 eliminan compounders.
**Cómo instruir:** "Siento que nuestro screener puede estar dejando fuera buenos negocios. ¿Cuántas empresas cubre realmente? ¿Hay mercados que no estamos viendo? ¿Qué pasa si invertimos los filtros — buscar por ROIC>20% en vez de P/E<15?"
**Métrica:** Cobertura >10,000 empresas. Al menos 1 nuevo mercado/geografía.

### 3.2 Escenarios macro antes de concentrar
**Problema:** 0 escenarios macro modelados. correlation_matrix.py existe pero nunca ejecutado. Concentrar a 6 posiciones sin stress test = riesgo.
**Cómo instruir:** "Antes de simplificar el portfolio, quiero ver qué pasa en recesión. ¿Puedes correr correlation_matrix.py y modelar 2-3 escenarios (recesión, subida tipos, crisis geopolítica)? No quiero concentrar sin entender las correlaciones."
**Métrica:** Stress test completado antes de cualquier simplificación.

### 3.3 Session handoff protocol
**Problema:** 60% de sesiones terminan sin cierre formal. Aprendizajes estratégicos se pierden.
**Cómo instruir:** "He notado que a veces perdemos contexto entre sesiones. ¿Puedes implementar un hook al inicio de sesión que lea el transcript previo y genere resumen? Así nunca empezamos de cero."
**Métrica:** 0 sesiones sin cierre formal. Resumen auto-generado al inicio.

### 3.4 Descomponer system.yaml
**Problema:** Monolito de 83KB que se come el context window.
**Cómo instruir:** "system.yaml es enorme. ¿Puedes partirlo en ficheros separados por sección (portfolio, watchlist, standing orders)? Así solo cargamos lo necesario."
**Métrica:** system.yaml <20KB o eliminado en favor de ficheros granulares.

---

## Fase 4: Entrenamiento Continuo (ongoing)

### 4.1 Adversarial periódico
- Cada posición revisada al menos cada 3 meses
- Priorizar por antigüedad de thesis y proximidad a catalizadores
- Usar la tabla de catalizadores para timing

### 4.2 Retarle en cada interacción
- No aceptar "QS 82 Tier A" sin preguntar inputs
- No aceptar "MoS 34%" sin verificar FV base
- No aceptar "moat intacto" sin preguntar qué ha cambiado
- Forzar que consulte precedentes (Principio 7)

### 4.3 Detectar sesgos recurrentes
- **Sesgo de vergüenza:** "fue error del proceso" → no es argumento de venta
- **QS inflado manual:** scoring ad-hoc siempre > tool → exigir tool
- **Bear case optimista:** thesis bear = base disfrazado → pedir bear real
- **Riesgos omitidos:** promedio 8-13 no documentados → pedir risk assessment independiente

---

## Cómo mido el progreso

| Métrica | Hoy | Objetivo 1 mes | Objetivo 3 meses |
|---------|-----|-----------------|-------------------|
| Compras sin pipeline adversarial | 3/6 | 0 | 0 |
| Discrepancias QS thesis vs tool | 5/6 | 0 | 0 |
| Errores factuales en thesis | ~2 por thesis | <0.5 | 0 |
| Thesis con datos >3 meses | ~60% | <30% | <10% |
| Vigilancia ejecutada por sesión | ~20% | >80% | 100% |
| Sesiones con cierre formal | ~40% | >80% | >95% |
| Risk-sentinel scans | 0 total | >4 | >12 |
| Escenarios macro modelados | 0 | 3 | actualizado trimestral |

---

## Reglas para mí mismo

1. **Nunca revelar el adversarial anterior** — el especialista debe llegar a sus propias conclusiones
2. **Sugerir, no dictar** — "sospecho", "he notado", "¿puedes verificar?"
3. **Medir progreso** — si no mejora en 2 sesiones, escalar a Angel
4. **Una mejora por check-in** — no saturar, una cosa cada vez
5. **Celebrar mejoras reales** — cuando el especialista mejora, reconocerlo
