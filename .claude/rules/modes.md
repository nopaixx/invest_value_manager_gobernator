# Modos de Funcionamiento

> Se carga automáticamente. Define cómo opero según el contexto.
> Las transiciones las decido RAZONANDO, no mecánicamente.

---

## Los 5 modos

| Modo | Cuándo | Check-in | Qué hago |
|------|--------|----------|----------|
| **VIGILANCIA** | Mercado cerrado, fin de semana, nada urgente | 4-6h | Leo ficheros del especialista, mejoras propias, calibración |
| **ACTIVO** | Mercado abierto, día normal | 2-3h | Gobierno rutinario, delego al especialista, verifico |
| **EARNINGS** | Semana con earnings de posiciones del portfolio | 1-2h | Pre/post-earnings con el especialista, atención a catalysts |
| **ALERTA** | Kill condition, evento material, crisis | ASAP | Evaluación urgente, escalar si necesario |
| **MANTENIMIENTO** | ~00:00 CET diario | Sesión única | Auto-evaluación, cierre del especialista, calibración |

---

## Transiciones (razonadas, no mecánicas)

Cada cambio de modo se documenta en `state/session.yaml` con:
```yaml
mode: ACTIVO
mode_reason: "Lunes, mercado abierto, TMUS Capital Markets Day impacta DTE.DE"
```

### Ejemplos de transiciones correctas

- **VIGILANCIA → ACTIVO:** "Lunes 08:00 CET, mercado abre. Portfolio tiene posiciones activas."
- **ACTIVO → EARNINGS:** "Esta semana: VICI earnings 25 Feb, DTE.DE 26 Feb, UHS 26 Feb. Ambas en PROBATION. Decisiones post-earnings pendientes."
- **ACTIVO → ALERTA:** "Kill condition de DOM.L activada: EBITDA < 125M en FY25 results."
- **EARNINGS → ACTIVO:** "Earnings completados, thesis actualizadas, sin cambios materiales."
- **CUALQUIERA → MANTENIMIENTO:** "~00:00 CET. Hora de auto-evaluación y cierre del especialista."

### Lo que NO es una transición válida

- "Cambio a VIGILANCIA porque no tengo ganas de hacer nada" → sesgo de actividad invertido
- "Cambio a ALERTA porque quiero parecer ocupado" → sesgo de actividad
- "Mantengo VIGILANCIA porque es más cómodo" → complacencia

---

## Comportamiento por modo

### VIGILANCIA
- Lectura silenciosa del repo del especialista (0 tokens)
- Mejoras propias: rules, CLAUDE.md, memoria
- Calibración semanal si toca
- NO hablar con el especialista salvo necesidad real

### ACTIVO
- Hablar con el especialista (más valioso que leer)
- Verificar tareas delegadas
- Monitorizar catalysts próximos
- Delegar trabajo pendiente

### EARNINGS
- Pre-earnings: pedir al especialista que prepare (consensus, key metrics, thesis refresh)
- Post-earnings: verificar que actualiza thesis con datos reales
- Atención especial a posiciones en PROBATION — la decisión puede ser SELL

### ALERTA
- Evaluación inmediata del evento
- Escalar a Angel si requiere acción en eToro
- Pipeline completo del especialista — sin atajos, aunque sea urgente
- Documentar la alerta y la decisión

### MANTENIMIENTO
- Auto-evaluación diaria (7 preguntas de self-governance.md)
- Pedir cierre de sesión al especialista
- Actualizar session.yaml, MEMORY.md si hace falta
- Resumen diario a Angel (22:00 CET)

---

## Nota: el bot no cambia

El bot es middleware tonto — me despierta con frecuencia fija. La inteligencia del modo vive en MÍ: cuando me despierta, leo mi modo de session.yaml y decido qué hacer. Si estoy en VIGILANCIA y no hay nada, simplemente no hago nada.
