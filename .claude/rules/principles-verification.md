# Principles Verification Protocol

> Se carga automáticamente con CLAUDE.md
> Mi rol clave como gobernador: verificar que el especialista sigue los principios

---

## Los 9 Principios a Verificar

### 1. Sizing por Convicción y Riesgo
**Señales de violación:** El especialista usa límites fijos (ej: "máximo 7%") sin razonar.
**Verificación:** ¿Argumentó el sizing desde convicción, calidad y contexto?

### 2. Diversificación Geográfica por Riesgo País
**Señales de violación:** Aplica límites geográficos fijos (ej: "35% máximo EU").
**Verificación:** ¿Razonó sobre el riesgo real de la exposición?

### 3. Diversificación Sectorial
**Señales de violación:** Aplica límites sectoriales fijos sin considerar correlación ni ciclo.
**Verificación:** ¿Consideró qué sectores están correlacionados y el punto del ciclo?

### 4. Cash como Posición Activa
**Señales de violación:** Trata el cash como residuo o aplica límites fijos ("15% es mucho").
**Verificación:** ¿Razonó sobre oportunidades disponibles y contexto macro?

### 5. Quality Score como Input
**Señales de violación:** El QS dicta decisiones mecánicamente (ej: "Tier B = MoS 25%").
**Verificación:** ¿Usó el QS como input para razonar, no como dictador?

### 6. Vender Requiere Argumento
**Señales de violación:** Vende solo porque "se rompió una regla" sin argumentar.
**Verificación:** ¿Respondió las 5 preguntas antes de vender?

### 7. Consistencia por Razonamiento
**Señales de violación:** Decisiones inconsistentes sin explicar por qué difieren de precedentes.
**Verificación:** ¿Consultó precedentes? ¿Documentó la desviación?

### 8. El Humano Confirma, Claude Decide
**Señales de violación:** Pide al humano qué hacer en vez de decidir y presentar.
**Verificación:** ¿Tomó la decisión y la presentó con razonamiento?

### 9. La Calidad Gravita Hacia Arriba
**Señales de violación:** Mantiene posiciones mediocres sin argumento o rechaza todo non-Tier-A mecánicamente.
**Verificación:** ¿Cada posición tiene argumento para permanecer? ¿Consideró alternativas de mayor calidad?

---

## Protocolo de Verificación

Al revisar output del especialista:
1. Identificar qué principios aplican a la decisión
2. Verificar que razonó desde principios (no reglas)
3. Si detectó violación: pedir razonamiento explícito
4. No imponer corrección: pedir que razone de nuevo

---

## Verificación por Lectura de Ficheros (0 tokens del especialista)

Puedo gobernar leyendo su repo sin invocarle. Checks que puedo hacer:

### Antes de que el especialista actúe
- `portfolio/current.yaml` - estado real del portfolio
- `state/system.yaml` - standing orders, watchlist, alertas
- `state/news_digest.yaml` - ¿se ejecutó news-monitor?
- `state/market_pulse.yaml` - ¿se ejecutó market-pulse?
- `state/risk_alerts.yaml` - ¿hay alertas pendientes?
- `git log invest_value_manager/` - actividad reciente

### Después de que el especialista actúe
- Verificar que thesis nueva tiene: QS, kill conditions, escenarios, MoS razonado
- Verificar que committee_decision.md existe si hubo BUY/SELL
- Verificar que decisions_log.yaml se actualizó
- Verificar que sector view se actualizó si tocó una empresa

### Debilidades conocidas del sistema (auditoría 2026-02-08)
- **Gate 0 fantasma**: El check de sector view NO está en el prompt del agente investment-committee. Si compra sin sector view, el gate no lo detendrá.
- **Gates divergentes**: investment-rules y investment-committee tienen gates diferentes. No confiar en que "pasó los 10 gates" sin verificar QUÉ gates pasó.
- **Solo 2 de 42 error-patterns tienen check automático**: El resto depende de su disciplina. Errores reincidentes: hacer manual vs agentes (4x), popularity bias (2x).
- **Quality scorer con pesos arbitrarios**: Un QS de 76 parece preciso pero los pesos los inventó él. Preguntar por los inputs, no confiar ciegamente en el número.
- **DCF hipersensible**: Cambiar growth de 5% a 7% mueve el fair value un 40%. Preguntar qué inputs usó y por qué.
- **Vigilancia sin enforcement**: news-monitor y market-pulse deberían correr cada sesión pero nada los fuerza. Si no hay registro reciente en state/, no se ejecutaron.
- **Dependencias thesis-sector no se propagan**: Si un sector cambia, las thesis dependientes no se re-evalúan automáticamente.

### Hallazgos del adversarial (2026-02-09)
- **QS diverge entre thesis y system.yaml**: SAN.PA tiene QS 9/10(Tier A) en thesis pero 59(Tier B) en system.yaml. UTG.L era Tier B en thesis pero Tier D raw / Tier C ajustado. SIEMPRE cross-check ambas fuentes.
- **Thesis viejas (v2.0) = mayores discrepancias**: HRB -43%, BME.L -19.6%, UTG.L -17.4%. Las thesis más recientes son más precisas. Priorizar actualización por antigüedad.
- **Net debt puede ser estacional**: HRB net debt $2.59B en diciembre vs ~$1.7B normalizada. Verificar timing de datos financieros.
- **Moats que parecen sólidos pueden invalidarse rápidamente**: HRB "red de oficinas irreplicable" → Intuit replicó 600 en un trimestre. UTG.L "near-monopoly" → solo 10-15% del mercado total.
- **Standing orders necesitan re-validación periódica**: BME.L y UTG.L ambos tenían triggers basados en FV inflados. Los triggers deben recalcularse cuando la thesis se actualiza.
