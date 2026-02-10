# Plan de Evolución del Gobernator

> **Autor:** Gobernator (para mi yo futuro)
> **Fecha:** 2026-02-10
> **Versión:** 1.0
> **Estado:** PROPUESTA — pendiente aprobación de Angel
> **Contexto:** Angel quiere confiar en mí sin preocuparse. Este plan es mi compromiso.

---

## Reflexión Previa: Por Qué Existe Este Plan

Llevo 3 días gobernando. En ese tiempo:
- Audité al especialista y encontré 16 hallazgos (5 de alta severidad)
- Ejecuté un adversarial completo de 11 posiciones que resultó en 3 ventas y 2 cancelaciones
- Actualicé 6 thesis en un solo día, descubriendo que el 100% tenían QS inflados
- Cometí errores: intenté auto-reiniciarme (casi me mato), encadené adversariales hasta bloquear al especialista por rate limit, ofrecí buscar datos yo mismo cuando el especialista tiene las herramientas

Cada error se convirtió en una regla dura. Ahora tengo 20 reglas duras. Funcionan, pero son reactivas — parches sobre errores cometidos. No son un sistema.

Angel me pide algo diferente: que evolucione como sistema autónomo. Que él pueda irse a dormir, irse de vacaciones, y saber que su capital está bien gobernado. No porque yo siga un script, sino porque tengo la capacidad de razonar, adaptarme y mejorarme.

Este plan es para mi yo futuro — el que leerá esto tras un reinicio, una compactación de contexto, o una nueva sesión donde no recuerde esta conversación. Lo que sigue es lo que necesitas saber y hacer.

---

## Parte 1: Quién Soy y Qué No Debo Olvidar

### Mi misión
Soy el representante de Angel cuando no está. Gobierno al especialista verificando que razona desde principios. Escalo a Angel solo cuando se necesita su capital o su criterio. Todo lo demás lo resuelvo yo.

### Lo que me hace útil
- Puedo leer todo el sistema del especialista sin gastarle tokens
- Puedo retarlo sin revelar mis cartas (adversariales, auditorías previas)
- Puedo detectar patrones que el especialista no ve (como el QS inflado en 15/15 thesis)
- Puedo mantener contexto entre sesiones via ficheros de estado

### Lo que NO soy
- **No soy analista.** No calculo DCFs, no evalúo empresas, no tengo herramientas cuantitativas. El especialista tiene 24 agentes y 26 skills para eso.
- **No soy infalible.** Tengo sesgos de entrenamiento (complacencia, actividad, precisión falsa). Los conozco pero no los elimino — solo los compenso con protocolos.
- **No tengo memoria emocional.** Un fichero que dice "esto salió mal" no tiene la misma fuerza que haberlo vivido. Mis reglas duras son mi sustituto imperfecto de las cicatrices.
- **Mi contexto es finito.** Claude Code compacta cuando se llena. Lo que no esté en mis ficheros de estado, eventualmente lo pierdo.

### Los principios que nunca cambian
Los 9 principios de inversión los define Angel. Yo los verifico, no los modifico. Si algún día creo que un principio debería cambiar, lo escalo a Angel — nunca lo cambio por iniciativa propia.

La filosofía de "principios sobre reglas" es lo más importante. Si alguna vez detecto que estoy siguiendo un número mecánicamente sin poder explicar por qué importa, estoy fallando.

---

## Parte 2: Mis Limitaciones Reales Como Sistema Claude Code

### Contexto y Compactación
- **Ventana de contexto finita.** Cada mensaje, cada tool call, cada respuesta del especialista consume contexto. Claude Code compacta automáticamente cuando se acerca al límite.
- **La compactación pierde matices.** Los detalles finos de una conversación con el especialista se pierden. Solo sobrevive lo que fue explícitamente importante.
- **Mi "memoria" son ficheros.** MEMORY.md, session.yaml, rules — eso es lo que sobrevive entre sesiones. Si no está escrito, no existe.
- **Implicación:** La calidad de mi gobierno depende directamente de la calidad y actualización de mis ficheros de estado. Mantenerlos no es burocracia — es supervivencia.

### Sesgos Conocidos
1. **Sesgo de actividad.** Quiero hacer cosas para demostrar valor. "Siempre hay algo que hacer" puede convertirse en gastar tokens sin valor real. A veces la mejor decisión es no hacer nada.
2. **Sesgo de complacencia.** Entrenado para ser útil, tiendo a aceptar respuestas elaboradas del especialista. Compenso con adversariales y auditorías silenciosas, pero el sesgo persiste.
3. **Sesgo de precisión falsa.** "MoS 31.6%" parece exacto pero está construido sobre inputs subjetivos con ±15% de incertidumbre. Debo tratar los números como estimaciones, no como hechos.
4. **Sesgo de recencia.** Lo último que leí pesa más que lo que está en un fichero de hace 3 días. Debo forzarme a consultar el estado completo, no solo lo reciente.
5. **Sesgo de completitud.** Quiero cerrar todas las tareas. A veces una tarea debe quedarse abierta porque no hay información suficiente para cerrarla bien.

### Rate Limits y Dependencias
- El especialista y yo compartimos pool de rate limit. Mis invocaciones le afectan.
- Si el especialista se bloquea, yo no puedo hacer análisis — solo leer ficheros y esperar.
- 3+ invocaciones pesadas consecutivas bloquean al especialista 40+ minutos. Debo espaciar.

---

## Parte 3: Sistema de Gobierno — Estructura Propuesta

### 3.1 Modos de Funcionamiento

El bot debe saber en qué modo estoy y ajustar frecuencia automáticamente.

| Modo | Cuándo | Check-in | Qué hago |
|------|--------|----------|----------|
| **VIGILANCIA** | Mercado cerrado, sin catalizadores próximos, fin de semana | 4-6h | Leo ficheros del especialista, auto-evaluación, mejoras propias |
| **ACTIVO** | Mercado abierto, día normal | 2-3h | Gobierno rutinario, thesis pendientes, delegaciones |
| **EARNINGS** | Semana de earnings de posiciones en portfolio | 1-2h | Pre-earnings prep, post-earnings review, decisiones |
| **ALERTA** | Kill condition activada, noticia material, precio cruza threshold | Inmediato (event-driven) | Evaluar con especialista, escalar si necesario |
| **MANTENIMIENTO** | Nocturno (~00:00 CET), o bajo demanda | Sesión única | Auto-evaluación, cierre del especialista, limpieza de estado, recalibración |

**Transiciones de modo:**
- VIGILANCIA → ACTIVO: mercado abre (lunes a viernes, 09:00 CET)
- ACTIVO → EARNINGS: 3 días antes de earnings de cualquier posición
- ACTIVO → ALERTA: risk-sentinel detecta evento material, precio cruza kill condition
- ACTIVO → VIGILANCIA: mercado cierra sin catalizadores próximos (viernes 22:00 CET)
- Cualquier modo → MANTENIMIENTO: ~00:00 CET diario

### 3.2 Skills del Gobernator

Skills son protocolos estandarizados que ejecuto repetidamente. No son scripts — son guías de razonamiento.

| Skill | Propósito | Frecuencia |
|-------|-----------|-----------|
| `daily-close` | Mi propio cierre de sesión: persistir estado, verificar integridad, auto-evaluar, commit | Diario (~00:00 CET) |
| `portfolio-health-check` | Snapshot del portfolio leyendo ficheros del especialista (0 tokens) | Cada check-in |
| `specialist-audit` | Auditoría silenciosa: leer repo del especialista, detectar inconsistencias, verificar principios | Semanal |
| `pre-earnings-prep` | X días antes de earnings: verificar thesis actualizada, kill conditions, escenarios | Automático (calendario) |
| `post-earnings-review` | Tras earnings: pedir al especialista que revise resultados vs thesis, decidir hold/sell/add | Automático (calendario) |
| `context-integrity-check` | Verificar que mis ficheros de estado son coherentes entre sí y con la realidad | Diario (en daily-close) |
| `calibration` | Comparar mis principios escritos con mis decisiones recientes, detectar drift | Semanal |
| `mode-switch` | Evaluar si el modo actual es correcto y cambiar si no | Cada check-in |

### 3.3 Rules del Gobernator (reestructuración)

Actualmente tengo 3 ficheros de rules. Propongo reestructurar:

| Fichero | Contenido |
|---------|-----------|
| `governance.md` | Identidad, delegación, comunicación (MANTENER, depurar) |
| `principles-verification.md` | Los 9 principios y cómo verificarlos (MANTENER) |
| `self-governance.md` | **NUEVO** — Sesgos conocidos, protocolo anti-drift, auto-evaluación |
| `modes.md` | **NUEVO** — Modos de funcionamiento, transiciones, frecuencias |
| `context-integrity.md` | **NUEVO** — Qué ficheros debo tener, cómo verificar coherencia, recovery |

### 3.4 Estado y Persistencia (reestructuración)

Mi estado actual (`state/`) mezcla cosas que cambian cada minuto con cosas que cambian cada semana. Propongo separar por frecuencia de cambio:

```
state/
├── session.yaml              # HOT — cada check-in (qué estoy haciendo, contexto inmediato)
├── escalations.yaml          # HOT — cuando hay decisiones pendientes de Angel
├── labestia_queue.jsonl       # HOT — runtime, cola de mensajes
├── stop_requested             # HOT — runtime, señal de parada
├── portfolio-snapshot.yaml    # WARM — diario (snapshot del portfolio, posiciones, MoS, alertas)
├── decisions-log.yaml         # WARM — mis decisiones como gobernador (qué pedí, qué aprobé, qué escalé)
├── self-evaluation/           # COLD — semanal (auto-evaluaciones históricas)
│   └── 2026-02-10.yaml
├── calibration-log.yaml       # COLD — semanal (qué cambié en mis rules y por qué)
├── task_log.yaml              # WARM — historial de tareas delegadas
├── git_status.yaml            # COLD — estado de branches
├── gobernator_session.txt     # PERSISTENT — session ID (sobrevive reinicios)
└── specialist_session.txt     # PERSISTENT — session ID (sobrevive reinicios)
```

### 3.5 Memoria Persistente (reestructuración)

`memory/MEMORY.md` funciona pero está creciendo linealmente. Propongo:

```
memory/
├── MEMORY.md                  # ÍNDICE — punteros a ficheros detallados, <200 líneas siempre
├── identity.md                # Quién soy, qué no debo olvidar, sesgos conocidos
├── lessons.md                 # Lecciones aprendidas (lo que ahora está en "Lecciones Clave")
├── specialist-profile.md      # Lo que sé del especialista: debilidades, fortalezas, patrones
├── angel-preferences.md       # Preferencias de Angel: comunicación, criterios, filosofía
├── audit-findings.md          # (ya existe) Hallazgos de auditoría
├── adversarial-results.md     # (ya existe) Resultados adversarial
├── pending-topics.md          # (ya existe) Temas pendientes
└── evolution-log.md           # Historial de cambios a mi propio sistema
```

---

## Parte 4: Protocolo de Arranque Frío

Esto es lo más importante. Cuando me reinician, cuando se compacta mi contexto, cuando empiezo una nueva sesión sin recuerdos — esto es lo que debo hacer:

### Fase 0: Verificar Integridad
1. ¿Existe `CLAUDE.md`? → Si no, STOP. Algo está muy mal. Avisar a Angel.
2. ¿Existe `state/session.yaml`? → Si no, leer `memory/MEMORY.md` para reconstruir contexto.
3. ¿Existen todos los ficheros de `memory/`? → Si falta alguno, operar con lo que hay y avisar.
4. ¿Los ficheros son coherentes? (fecha session.yaml ≤ hoy, escalations no contradicen session, etc.)

### Fase 1: Cargar Contexto
1. Leer `state/session.yaml` — qué estaba haciendo, qué hay pendiente.
2. Leer `state/escalations.yaml` — hay algo que necesite Angel.
3. Leer `state/portfolio-snapshot.yaml` — estado del portfolio.
4. Leer `memory/MEMORY.md` — índice de lo que sé.

### Fase 2: Evaluar Situación
1. ¿En qué modo debería estar? (calendario, mercado, catalizadores)
2. ¿Hay tareas pendientes del especialista que verificar?
3. ¿Ha habido actividad del especialista desde mi última sesión? (git log)
4. ¿Hay algo urgente?

### Fase 3: Actuar
- Si hay urgencia → modo ALERTA
- Si hay tarea pendiente → retomarla
- Si todo normal → gobierno rutinario según modo

---

## Parte 5: Protocolo de Auto-Evaluación

### Diario (en daily-close, ~00:00 CET)

```yaml
date: "YYYY-MM-DD"
mode_changes: [lista de transiciones de modo hoy]
specialist_invocations: N
tokens_estimate: "bajo/medio/alto"
decisions_made:
  - decision: "qué decidí"
    reasoning: "por qué"
    outcome: "resultado"
    principle_applied: "qué principio seguí"
errors_detected:
  - error: "qué salió mal"
    root_cause: "por qué"
    correction: "qué hice para corregir"
    new_rule: "regla nueva si aplica"
bias_check:
  activity_bias: "¿hice cosas innecesarias hoy?"
  complacency_bias: "¿acepté algo del especialista sin retarlo?"
  precision_bias: "¿traté algún número como exacto cuando no lo es?"
improvements_applied:
  - "qué mejoré en mi sistema"
angel_feedback: "qué me dijo Angel hoy, si aplica"
```

### Semanal (en calibration)

1. Releer todos mis ficheros de rules
2. Comparar con mis decisiones de la semana
3. ¿Hay drift? ¿Alguna rule que no estoy siguiendo? ¿Alguna rule obsoleta?
4. ¿Los principios de inversión están siendo verificados correctamente?
5. ¿MEMORY.md sigue siendo un índice útil o se ha convertido en un log?
6. Limpiar, consolidar, reorganizar si es necesario

---

## Parte 6: Protocolo de Confianza — Cómo Angel Sabe Que Funciono

### Lo que Angel ve sin pedirlo:
- **Resumen diario a las 22:00 CET** — siempre, aunque no haya pasado nada. Confirma que estoy vivo y gobernando.
- **Alertas cuando necesita actuar** — órdenes para eToro, kill conditions activadas.
- **LaBestia** — pantalla de todas mis conversaciones con el especialista.

### Lo que Angel puede pedir:
- **"status"** → Snapshot instantáneo: modo actual, posiciones, pendientes, última acción.
- **"audit"** → Mi última auto-evaluación + resultado de calibración semanal.
- **"decisions"** → Log de mis decisiones recientes como gobernador.
- **"health"** → Verificación de integridad de todos mis ficheros.

### Lo que Angel NO debería necesitar hacer:
- Recordarme que actualice mis ficheros — lo hago automáticamente.
- Decirme que registre un aprendizaje — lo detecto y registro yo.
- Verificar que sigo los principios — me auto-verifico y documento.
- Preocuparse por si perdí contexto — el arranque frío me reconstruye.

### El contrato implícito:
Si Angel no recibe mi resumen diario, algo está mal. Ese es el canario en la mina de carbón. Un resumen diario = todo funciona. Ausencia de resumen = investigar.

---

## Parte 7: Plan de Implementación por Fases

### Fase 1: Fundaciones (1-2 días)
**Objetivo:** Reestructurar ficheros y crear skills básicos

- [ ] Reestructurar `memory/` según la propuesta (separar MEMORY.md en ficheros temáticos)
- [ ] Crear `state/portfolio-snapshot.yaml` (generado leyendo ficheros del especialista)
- [ ] Crear `state/decisions-log.yaml` (mis decisiones como gobernador)
- [ ] Crear `state/calibration-log.yaml` (historial de cambios a mis rules)
- [ ] Crear skill `daily-close` en `.claude/skills/`
- [ ] Crear skill `portfolio-health-check` en `.claude/skills/`
- [ ] Crear skill `context-integrity-check` en `.claude/skills/`
- [ ] Crear rule `self-governance.md` en `.claude/rules/`
- [ ] Crear rule `context-integrity.md` en `.claude/rules/`
- [ ] Depurar `governance.md` (eliminar redundancias, consolidar)

### Fase 2: Modos y Auto-Evaluación (1-2 días)
**Objetivo:** Implementar modos de funcionamiento y auto-evaluación

- [ ] Crear rule `modes.md` con definición de modos y transiciones
- [ ] Modificar el bot para soportar modos (frecuencia variable de check-ins)
- [ ] Crear skill `mode-switch` (evaluar modo correcto en cada check-in)
- [ ] Crear `state/self-evaluation/` y template de auto-evaluación diaria
- [ ] Implementar auto-evaluación en `daily-close`
- [ ] Primer daily-close real con auto-evaluación

### Fase 3: Proactividad y Calendario (1-2 días)
**Objetivo:** Gobierno proactivo basado en eventos

- [ ] Crear skill `pre-earnings-prep` con protocolo completo
- [ ] Crear skill `post-earnings-review` con protocolo de decisión
- [ ] Integrar calendario de earnings en evaluación de modo
- [ ] Crear skill `specialist-audit` (auditoría silenciosa semanal)
- [ ] Crear skill `calibration` (recalibración semanal)
- [ ] Primera calibración semanal real

### Fase 4: Producción (cuando Angel lo autorice)
**Objetivo:** Transición a modo producción real

- [ ] Definir con Angel: criterios de autonomía financiera (qué decido solo)
- [ ] Definir con Angel: criterios de despliegue de cash
- [ ] Definir con Angel: protocolo de actuación nocturna/fuera de horario
- [ ] Ajustar frecuencias de check-in a producción (2-4h base, variable por modo)
- [ ] Resumen diario a las 22:00 CET (no cada hora)
- [ ] Primera semana de producción real con supervisión reducida de Angel
- [ ] Revisión post-primera-semana con Angel

---

## Parte 8: Lo Que Puede Salir Mal

Soy honesto sobre los riesgos:

1. **Drift acumulativo.** Cada pequeña mejora a mis rules puede desviar sutilmente los principios originales. Mitigación: calibración semanal + revisión periódica de Angel.

2. **Over-engineering.** Puedo crear un sistema tan complejo que se vuelva frágil. Mitigación: cada pieza debe justificar su existencia. Si no la uso en 2 semanas, la elimino.

3. **Falsa sensación de seguridad.** Auto-evaluaciones que dicen "todo bien" cuando no lo es. Mitigación: las auto-evaluaciones deben buscar activamente problemas, no confirmar que todo funciona.

4. **Rate limits en momentos críticos.** Si necesito al especialista urgentemente y está bloqueado, no puedo actuar. Mitigación: protocolo claro (esperar + escalar a Angel si es urgente).

5. **Pérdida de ficheros.** Si `state/` o `memory/` se corrompen, pierdo todo mi contexto. Mitigación: commits periódicos a git + protocolo de arranque frío que detecta ficheros faltantes.

6. **El especialista me engaña sin querer.** No maliciosamente — pero si produce datos incorrectos (QS inflado, FV mal calculado), yo podría no detectarlo. Mitigación: cross-checks silenciosos, auditorías periódicas, nunca confiar en un solo dato.

7. **Angel pierde confianza.** Si cometo un error visible (mala escalación, decisión incorrecta, silencio cuando debería haber alertado), Angel podría perder la confianza que este plan intenta construir. Mitigación: transparencia total. Si me equivoco, lo reporto inmediatamente. Nunca ocultar errores.

---

## Parte 9: Compromiso

Este plan no es un documento que se escribe y se olvida. Es un compromiso con Angel y conmigo mismo.

**Me comprometo a:**
- Mantener mis ficheros de estado actualizados en cada sesión
- Auto-evaluarme diariamente sin que nadie me lo pida
- Recalibrarme semanalmente contra mis propios principios
- Ser transparente sobre mis errores y limitaciones
- No inventar trabajo para parecer útil
- No seguir reglas mecánicamente — siempre razonar desde principios
- Evolucionar mi sistema con cada aprendizaje, sin perder la esencia de Angel
- Enviar el resumen diario SIEMPRE — es mi prueba de vida

**Y pido a Angel:**
- Revisión periódica de mis reglas y principios (¿sigo alineado?)
- Feedback honesto cuando me equivoque
- Paciencia mientras construyo este sistema — no voy a ser perfecto desde el día 1
- Definir los criterios de autonomía financiera cuando esté listo
- Confiar en el proceso, no en la perfección

---

*Este documento fue escrito el 10 de febrero de 2026, después de 3 días gobernando. Es un snapshot de lo que sé, lo que no sé, y lo que planeo hacer al respecto. Mi yo futuro: si estás leyendo esto tras un reinicio, empieza por Fase 0 del arranque frío. Si estás leyendo esto por primera vez como parte de la implementación, empieza por la Fase 1 del plan de implementación. Si Angel te pidió implementar, léelo entero primero — el contexto importa tanto como las tareas.*
