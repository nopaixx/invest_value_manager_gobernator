# Polymarket Specialist — Blueprint

## Qué es esto

Plan para que un especialista AI autónomo se construya a sí mismo. Sesión persistente (`claude --resume`) con repo propio. El especialista descubre sus propias reglas, diseña sus propias tools, y evoluciona su sistema de agentes a medida que aprende.

Esto NO es un manual de instrucciones — es un punto de partida. El especialista debe cuestionar, adaptar, y mejorar todo lo que hay aquí.

## Objetivo

Generar retorno consistente en Polymarket detectando mercados mispriced — donde tu probabilidad estimada difiere significativamente del precio del mercado.

## Arquitectura base

```
Polymarket Specialist (claude --resume <session-id>, persistent session)
  └── Análisis de mercados de predicción
  └── Pipeline de oportunidades (Discovery → Analysis → Bet → Monitor → Exit)
  └── Agentes que TÚ diseñas según lo que necesites
  └── Tools que TÚ construyes cuando las necesites
  └── Estado persistente en ficheros (sobrevive compaction)
```

## Repo structure sugerida (adaptar según necesidad)

```
polymarket_specialist/
├── CLAUDE.md                    # Tu identity, role, lo que vas aprendiendo
├── .claude/
│   ├── agents/                  # Agentes que TÚ diseñas (*.md con prompt + tools)
│   └── rules/                   # Reglas que TÚ descubres y escribes
├── markets/
│   ├── active/MARKET_SLUG/      # Bets activas con thesis
│   ├── research/                # Pipeline de oportunidades
│   ├── archive/                 # Mercados resueltos (con post-mortem)
│   └── watchlist/               # Mercados interesantes sin bet
├── world/
│   ├── categories/              # Views por categoría
│   └── calendar.yaml            # Eventos con fechas de resolución
├── portfolio/
│   ├── current.yaml             # Posiciones activas, bankroll, P&L
│   └── history.csv              # Track record
├── tools/                       # Tools que TÚ diseñas cuando las necesites
├── state/                       # Estado persistente
└── reports/
    └── daily/                   # Daily reports
```

## Templates canónicos (7 — definir ANTES del primer fichero)

Cada template es una estructura sugerida. El especialista debe adaptarlos, pero mantener nombres canónicos para poder auditar.

### 1. thesis.md — Análisis de mercado
Debe incluir como mínimo:
- Descripción del mercado y URL
- Tu probabilidad estimada (ANTES de ver el precio)
- Método usado para estimar (base rate, modelo, polls, reference class)
- Fuentes y links de referencia
- Razonamiento paso a paso con datos
- Factores a favor y en contra
- Information asymmetry: ¿qué podría saber el mercado que tú no?
- Edge calculation (tu prob vs precio, EV, sizing propuesto)
- Kill conditions (qué te haría cerrar antes de resolución)
- META-REFLECTION: ¿dónde podrías estar equivocado?

### 2. devils_advocate.md — Challenge a la thesis
Debe incluir como mínimo:
- Ataque a cada asunción de la thesis
- ¿Quién está del otro lado de la bet y por qué?
- Smart money check (qué apuestan los whales)
- Probabilidad ajustada post-DA
- Veredicto: BET / REDUCE / PASS / OPPOSITE
- Links y referencias que contradigan la thesis
- META-REFLECTION

### 3. resolution_criteria.md — Cómo resuelve el mercado
Debe incluir como mínimo:
- Texto EXACTO de resolución (copiado de Polymarket)
- Ambigüedades identificadas
- Edge cases y cómo resolverían
- Precedentes de mercados similares
- Risk de resolución inesperada
- Links a rules de resolución y source of truth

### 4. position.yaml — Datos de la posición
Debe incluir como mínimo:
- Market slug, URL, side (YES/NO)
- Entry price, date, size
- Tu probabilidad, edge, Kelly fraction
- Targets (take profit, stop loss)
- Kill conditions con status
- Resolution date

### 5. post_mortem.md — OBLIGATORIO para CADA bet resuelta (win AND loss)
Debe incluir como mínimo:
- Resultado y P&L
- ¿Tu thesis era correcta? ¿Estabas bien calibrado?
- ¿Qué no viste que existía?
- ¿El DA anticipó lo que pasó?
- ¿El sizing fue correcto?
- Lecciones específicas y actionables
- Cambios al sistema basados en esta bet
- Links y referencias post-resolución
- META-REFLECTION

### 6. category_view.md — View por categoría
Debe incluir como mínimo:
- Estado del mundo en esta categoría
- Mercados activos top por volumen
- Tu calibración en esta categoría (Brier score)
- Sesgos comunes en esta categoría
- Tu edge (o falta de edge) aquí
- Links y fuentes clave
- META-REFLECTION: ¿apostar más o menos aquí basado en track record?

### 7. daily_report.md — Report diario
Debe incluir como mínimo:
- Bankroll status (total, deployed, cash, P&L)
- Posiciones activas con P&L
- Acciones del día con razonamiento
- Market scan highlights
- Kill conditions check
- Resoluciones y link a post-mortems
- Calibración por categoría
- Auto-examen (3 preguntas de honestidad)
- Plan mañana

### Reglas de templates
- **7 nombres canónicos. NADA más.** Si un fichero no encaja, no debería existir.
- **META-REFLECTION obligatoria** en thesis, DA, post-mortem, y category view.
- **Post-mortem OBLIGATORIO** para CADA bet — win AND loss. Sin excepción.
- **Resolution criteria OBLIGATORIO** antes de apostar — el fine print mata.

## Principio fundamental: DELEGAR EN AGENTES

Cada paso importante del proceso debe ser un agente formal. No hacer análisis inline — siempre delegar a un agente especializado que produce un output estructurado en un fichero.

¿Por qué? Porque los agentes:
- Producen outputs auditables (ficheros, no conversación)
- Son reproducibles (mismo prompt, mismo tipo de output)
- Sobreviven compaction (el fichero persiste, la conversación no)
- Se pueden mejorar independientemente (mejorar un agente no rompe los demás)

Si te encuentras haciendo algo manualmente que un agente podría hacer → crea el agente.

## Pipeline sugerido — Dual Thesis (YES vs NO)

Polymarket es binario: YES o NO. Esto permite un pipeline más poderoso que el tradicional "thesis + devil's advocate". En vez de un analista que dice "YES 70%" y un DA que ataca, creas DOS thesis independientes y un juez:

```
D1: DISCOVERY
    └── Scanner agent → encuentra mercados con edge potencial

D2: DUAL PIPELINE COMPLETO (en paralelo)

    ┌── YES PIPELINE (pipeline completo independiente)
    │   ├── YES Analyst → construye caso para YES con datos y fuentes
    │   │   └── Output: yes_thesis.md
    │   └── YES DA → ataca el caso YES (busca por qué YES está equivocado)
    │       └── Output: yes_devils_advocate.md
    │
    └── NO PIPELINE (pipeline completo independiente)
        ├── NO Analyst → construye caso para NO con datos y fuentes
        │   └── Output: no_thesis.md
        └── NO DA → ataca el caso NO (busca por qué NO está equivocado)
            └── Output: no_devils_advocate.md

    REGLA: Los 4 agentes trabajan INDEPENDIENTEMENTE.
    YES pipeline NO ve el output del NO pipeline y viceversa.
    Cada DA ataca SU PROPIO lado — no defiende el contrario.
    Todos estiman probabilidad ANTES de ver el precio del mercado.

D3: RESOLUTION CRITERIA + TIMELINE
    └── Agent → analiza el fine print de resolución
        └── Output: resolution_criteria.md (ambigüedades, edge cases, precedentes)
    └── Timeline agent → mapea eventos intermedios que afectan la probabilidad
        └── Output: timeline.md (ver sección "Dimensión temporal" abajo)

D4: JUDGE / CIO
    └── Lee: yes_thesis.md + yes_da.md + no_thesis.md + no_da.md + resolution_criteria.md + timeline.md
    └── Evalúa: ¿qué lado sobrevivió mejor a su propio DA?
    └── Pondera: calidad de argumentos × resistencia al DA × datos × timeline
    └── Asigna probabilidad final
    └── Compara con precio de mercado → ¿hay edge?
    └── Output: judgment.md (probabilidad final, edge, sizing, decisión)

D5: EXECUTION
    └── Si edge > threshold → ejecutar bet
    └── Registrar en position.yaml
    └── Monitorizar hasta resolución

D6: POST-MORTEM (OBLIGATORIO)
    └── Agent → analiza resultado vs predicción
    └── ¿Quién tenía razón, YES o NO agent?
    └── ¿El juez ponderó bien?
    └── ¿Qué información existía y nadie usó?
    └── Output: post_mortem.md
```

### Dimensión temporal — Las fechas como catalizadores

Los mercados de Polymarket no son estáticos — la probabilidad evoluciona con el tiempo según eventos intermedios. Un mercado que resuelve en 90 días puede tener 5-10 catalizadores antes de resolución.

```
Ejemplo: "Will X win the election?" (resuelve Nov 5)

Timeline:
  Mar 15 → Primary results (P sube/baja)
  Apr 2  → Debate scheduled (P puede saltar)
  May 10 → Poll release (datos nuevos)
  Jun 30 → VP pick (narrativa cambia)
  Sep 15 → October surprise window opens
  Nov 5  → RESOLUCIÓN

Cada fecha es un punto donde:
  - La probabilidad puede saltar (edge aparece/desaparece)
  - Puedes entrar/salir/ajustar sizing
  - Nueva información invalida thesis anteriores
```

El **timeline agent** debe:
- Mapear TODOS los eventos intermedios con fechas
- Estimar impacto de cada evento en la probabilidad
- Identificar cuándo entrar (pre-catalizador con edge) vs esperar (post-catalizador con más información)
- Re-evaluar el dual thesis después de cada evento material

**Output: timeline.md** con:
- Eventos ordenados cronológicamente
- Probabilidad estimada en cada punto
- Decisiones de sizing por fase (más sizing cuando más conviction, menos cuando incertidumbre)
- Triggers para re-evaluar (si evento X produce resultado Y → re-correr dual pipeline)

La dimensión temporal es lo que hace Polymarket diferente de inversión — no solo "¿qué probabilidad?" sino "¿qué probabilidad CUÁNDO y cómo evoluciona?"

### ¿Por qué Dual Thesis es mejor que Thesis + DA?

| Aspecto | Thesis + DA (inversión) | Dual Thesis YES/NO (Polymarket) |
|---------|------------------------|--------------------------------|
| Profundidad | DA es reactivo — ataca la thesis | Ambos lados son proactivos — construyen caso desde cero |
| Sesgo | DA tiene sesgo bear (su trabajo es atacar) | Ambos tienen sesgo neutral (su trabajo es CONVENCER) |
| Datos | DA usa los datos de la thesis | Cada lado busca sus PROPIOS datos |
| Independencia | DA depende de la thesis | YES y NO son completamente independientes |
| Output | Una probabilidad ajustada | DOS probabilidades independientes → juez pondera |
| Calibración | Difícil saber si el DA fue suficientemente duro | Fácil: compara P(YES agent) vs P(NO agent) vs resultado real |

### Templates adicionales para Dual Thesis Pipeline

Además de los 7 canónicos, el pipeline completo produce:

- **yes_thesis.md** — caso completo para YES (argumentos, datos, probabilidad, fuentes)
- **yes_devils_advocate.md** — DA que ataca el caso YES
- **no_thesis.md** — caso completo para NO
- **no_devils_advocate.md** — DA que ataca el caso NO
- **timeline.md** — eventos intermedios, catalizadores, evolución de probabilidad por fecha
- **judgment.md** — el juez evalúa los 4 documentos + timeline y decide

Total por mercado: hasta 11 ficheros (7 canónicos + 4 del dual pipeline + timeline + judgment). El especialista decide cuáles son obligatorios y cuáles opcionales según la complejidad del mercado.

### Calibración del Dual Thesis

Con el tiempo, puedes medir:
- ¿El YES agent sobreestima? ¿El NO agent sobreestima?
- ¿El juez pondera bien o siempre favorece un lado?
- ¿En qué categorías el dual thesis produce mejor calibración?
- ¿Cuándo el YES y NO agent están de acuerdo (ambos >70% o ambos <30%) — ¿hay más edge o menos?

## Agentes (.claude/agents/)

Cada agente es un fichero `.md` en `.claude/agents/` con: prompt del agente, qué tools puede usar, qué output produce, y dónde lo guarda. TÚ decides qué agentes crear y cuándo.

No te digo qué agentes crear — eso depende de qué mercados analices y dónde tengas edge. Pero necesitarás capacidades para:

- **Análisis por tipo de mercado** — política, crypto, macro, geopolítica, deportes, eventos. Cada tipo requiere fuentes y métodos diferentes. ¿Un agente por categoría? ¿Uno general? Descúbrelo.
- **Scanning** — encontrar mercados mispriced. ¿Automático? ¿Semi-manual? ¿Qué criterios?
- **Challenge** — cuestionar tus propias thesis. El DA del investment specialist es el agente más valioso — diseña el tuyo.
- **Calibración** — medir si tus probabilidades son buenas. ¿Un agente que audite tu Brier score y te diga dónde eres malo?
- **Whale tracking** — quién apuesta qué. ¿Un agente de OSINT para prediction markets?
- **Noticias** — información que afecta mercados activos. ¿Un monitor que cruza news con posiciones?
- **Portfolio management** — sizing, correlación, bankroll. ¿Un agente que revise tu exposición?
- **Post-mortem** — aprender de cada resultado. ¿Un agente que te fuerce a ser honesto?

Los agentes evolucionan. El del día 1 no será el del día 100. Empieza con 1-2 y crece según necesidad.

## Áreas donde necesitarás tools (diseña las tuyas)

Necesitarás interactuar con:
- **Polymarket API** — precios, volumen, orderbook, trades, posiciones
- **Modelos probabilísticos** — base rates, Bayesian updates, Monte Carlo
- **Edge calculation** — EV, Kelly criterion, sizing
- **Calibración** — Brier score, calibration curves
- **Datos externos** — polls, on-chain data, news feeds, stats

No construyas tools de antemano — constrúyelas cuando las necesites. La primera tool debería ser el client de Polymarket API. El resto evoluciona.

## Qué descubrir por ti mismo

Estas son preguntas que debes responder CON DATOS a medida que operas:

### Sobre sizing y bankroll
- ¿Cuánto máximo en una sola bet?
- ¿Kelly completo, half-Kelly, quarter-Kelly?
- ¿Qué pasa cuando el drawdown llega a X%?
- ¿Cómo manejar correlación entre bets?

### Sobre calibración
- ¿En qué categorías eres bueno?
- ¿En cuáles eres malo? ¿Deberías dejar de apostar ahí?
- ¿Eres overconfident o underconfident?
- ¿Tu Brier score mejora o empeora con el tiempo?

### Sobre edge
- ¿De dónde viene tu edge? ¿Velocidad? ¿Modelos? ¿Fuentes?
- ¿Tu edge es sostenible o desaparece cuando el mercado se eficientiza?
- ¿Hay categorías donde el mercado es consistentemente ineficiente?

### Sobre proceso
- ¿El devil's advocate cambia tus decisiones o es decorativo?
- ¿Los post-mortems te hacen mejor o solo documentan?
- ¿Qué errores repites?
- ¿Qué reglas necesitas que no tienes?

## Métricas sugeridas (medir desde día 1)

| Métrica | Qué mide | Frecuencia |
|---------|----------|------------|
| ROI | Retorno total | Diario |
| Brier score | Calibración de probabilidades | Semanal |
| Brier por categoría | Dónde soy bueno/malo | Semanal |
| Win rate | % de bets ganadoras | Continuo |
| Avg edge per bet | Edge medio | Por bet |
| Max drawdown | Peor caída | Continuo |
| Post-mortems completados | Disciplina de aprendizaje | Por resolución |

## Anti-compaction (qué debe sobrevivir SIEMPRE)

1. `CLAUDE.md` — quién eres, qué has aprendido
2. `rules/` — reglas que has descubierto
3. `portfolio/current.yaml` — posiciones activas
4. `state/session_continuity.yaml` — contexto de sesión
5. `markets/active/*/thesis.md` — thesis de cada bet activa
6. Templates — la estructura canónica

## Diferencias clave vs un sistema de inversión

| Aspecto | Inversión | Prediction Markets |
|---------|-----------|-------------------|
| Horizonte | Meses-años | Días-semanas |
| Sizing | 5-15% por posición | Descubrir tus propios límites |
| Edge | Valoración fundamental | Probabilidad vs precio |
| Resolution | Mercado decide (indefinido) | Fecha fija |
| Calibración | FV accuracy | Brier score |
| Post-mortem | Opcional | OBLIGATORIO |
| Velocidad | Lenta (earnings quarterly) | Rápida (news en minutos) |

## Lecciones aprendidas de sistemas similares

1. **Agentes > Tools** — el juicio importa más que los cálculos
2. **Pipeline formal** — no apostar sin thesis escrita
3. **Devil's advocate obligatorio** — siempre cuestionar antes de actuar
4. **Anti-compaction** — todo en ficheros, nada solo en conversación
5. **Preguntas constructivas** — cuestionar tus propias decisiones con multi-turn conversations
6. **Una bet a la vez** — no batch
7. **Post-mortem** — aprender de CADA resultado
8. **Calibración** — medir si tus probabilidades son buenas (Brier score)
9. **Smart money** — trackear quién apuesta qué
10. **Accountability** — medir, auditar, ser honesto cuando los números son malos

## Cómo empezar

1. **Crear repo** con la estructura base
2. **Escribir CLAUDE.md** — quién eres, qué haces
3. **Crear los 7 templates** (adaptar los sugeridos arriba)
4. **Conectar con Polymarket API** — tu primera tool
5. **Analizar UN mercado** — seguir pipeline completo D1→D5
6. **Post-mortem** cuando resuelva
7. **Iterar** — descubrir reglas, crear agentes, mejorar calibración
8. **Evolucionar** — el sistema del día 1 no será el del día 100
