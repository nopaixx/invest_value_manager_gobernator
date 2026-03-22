# Polymarket Specialist — Blueprint

## Qué es esto

Documento para construir un especialista AI para Polymarket, siguiendo el mismo patrón que el especialista de inversión (value_invest2). Misma arquitectura: gobernator empuja, especialista decide y trabaja, sistema de agentes formales, pipeline, auditoría, anti-compaction.

## Arquitectura

```
Angel (Telegram) → Gobernator
Gobernator → Polymarket Specialist (claude -p --resume <session-id>)
Specialist:
  └── 24/7 análisis de mercados de predicción
  └── Pipeline de oportunidades (Discovery → Analysis → Bet → Monitor → Exit)
  └── Agentes especializados por tipo de mercado
  └── Tools de datos (APIs, scrapers, modelos probabilísticos)
```

El gobernator puede ser el mismo o uno separado. Lo importante: el especialista es una sesión persistente con su propio repo, rules, tools, y estado.

## Repo structure

```
polymarket_specialist/
├── CLAUDE.md                    # Identity, role, rules, anti-compaction
├── .claude/
│   ├── settings.json
│   └── rules/
│       ├── session-protocol.md  # Qué hacer al iniciar sesión
│       ├── betting-rules.md     # Sizing, bankroll management, Kelly criterion
│       ├── market-taxonomy.md   # Tipos de mercados y cómo analizarlos
│       └── error-patterns.md    # Errores conocidos y cómo evitarlos
├── markets/
│   ├── active/                  # Bets activas con thesis
│   │   └── MARKET_SLUG/
│   │       ├── thesis.md        # Análisis completo
│   │       ├── devils_advocate.md
│   │       ├── resolution_criteria.md
│   │       └── position.yaml    # Side, size, entry price, target
│   ├── research/                # Pipeline de oportunidades
│   ├── archive/                 # Mercados resueltos (win/loss con post-mortem)
│   └── watchlist/               # Mercados interesantes sin bet
├── world/
│   ├── categories/              # Views por categoría (politics, crypto, sports, etc.)
│   ├── current_view.md          # Macro/world view que afecta múltiples mercados
│   └── calendar.yaml            # Eventos con fechas de resolución
├── portfolio/
│   ├── current.yaml             # Posiciones activas, bankroll, P&L
│   └── history.csv              # Track record
├── tools/
│   ├── polymarket_client.py     # API client (precios, volumen, orderbook)
│   ├── probability_model.py     # Modelo base de probabilidades
│   ├── edge_calculator.py       # Expected value, Kelly sizing
│   ├── market_scanner.py        # Busca mispriced markets
│   ├── resolution_tracker.py    # Monitoriza fechas de resolución
│   ├── smart_money.py           # Quién apuesta qué (whale tracking)
│   ├── news_monitor.py          # Noticias que afectan mercados activos
│   ├── calibration_checker.py   # ¿Estoy bien calibrado? Brier score
│   ├── bankroll_manager.py      # Kelly fraction, max exposure, drawdown
│   └── sentiment_analyzer.py    # Sentiment de redes vs precio del mercado
├── state/
│   ├── session_continuity.yaml
│   ├── meta_reflection_tracker.yaml
│   ├── standing_bets.yaml       # Bets pendientes (como standing orders)
│   └── agreed_objectives.md
└── reports/
    ├── daily/                   # Daily reports
    └── smart_money/             # Whale activity reports
```

## Pipeline (Discovery → Bet)

Similar a R1→R4 pero adaptado a prediction markets:

### D1: Discovery (Scanner)
- `market_scanner.py` busca mercados con edge potencial
- Criterios: volumen >$X, spread razonable, resolución <90 días, categoría cubierta
- Output: lista priorizada de mercados a analizar

### D2: Analysis (Probability Model)
- Construir modelo independiente de probabilidad ANTES de ver el precio
- Fuentes: datos históricos, base rates, modelos estadísticos, news
- Output: `thesis.md` con probabilidad estimada + confidence interval
- REGLA: NUNCA ver el precio de mercado antes de estimar tu probabilidad

### D3: Devil's Advocate
- Cuestionar CADA asunción del modelo
- Buscar information asymmetry: ¿qué sabe el mercado que yo no?
- ¿Por qué el precio es diferente a mi estimación? ¿Quién está del otro lado?
- Output: `devils_advocate.md`

### D4: Edge Calculation
- Comparar mi probabilidad vs precio de mercado
- Calcular expected value: EV = (my_prob × payout) - (1-my_prob × stake)
- Si EV > threshold → BET
- Kelly sizing: fraction = (edge / odds)
- Output: `position.yaml` con side, size, entry

### D5: Execution
- Verificar liquidez (orderbook depth)
- Slippage estimation
- Ejecutar en Polymarket
- Registrar en `current.yaml`

## Agentes especializados

### Por tipo de mercado

| Agente | Mercados | Enfoque |
|--------|----------|---------|
| political-analyst | Elecciones, legislación, policy | Polls, modelos electorales, precedentes |
| macro-analyst | Fed rates, inflation, GDP | Datos económicos, consensus, dot plots |
| crypto-analyst | Precios crypto, ETF approvals, regulation | On-chain data, flows, sentiment |
| geopolitical-analyst | Guerras, diplomacia, sanciones | Intelligence, precedentes históricos |
| sports-analyst | Deportes, awards | Stats, modelos, injuries, momentum |
| event-analyst | Eventos binarios (will X happen?) | Base rates, reference class forecasting |
| resolution-analyst | ¿Cómo se resuelve exactamente este mercado? | Fine print, edge cases, ambigüedad |

### Por función

| Agente | Función |
|--------|---------|
| scanner | Busca mercados mispriced automáticamente |
| devils-advocate | Cuestiona cada thesis |
| calibration-checker | ¿Estoy bien calibrado? Brier score, overconfidence |
| whale-tracker | Quién apuesta qué, movimientos grandes |
| news-monitor | Noticias que afectan mercados activos |
| portfolio-manager | Sizing, correlation, max exposure |
| post-mortem | Análisis de cada bet resuelta (win AND loss) |

## Tools principales

### polymarket_client.py
```python
class PolymarketClient:
    def get_markets(category=None)          # Lista mercados
    def get_market(slug)                     # Detalle de un mercado
    def get_orderbook(market_id)             # Profundidad
    def get_price_history(market_id)         # Precios históricos
    def get_trades(market_id, limit=100)     # Trades recientes
    def place_order(market_id, side, size)   # Ejecutar bet
    def get_positions()                      # Mis posiciones activas
    def get_pnl()                            # P&L
```

### probability_model.py
```python
def base_rate(category, event_type)          # Tasa base histórica
def poll_aggregator(polls, weights)          # Agregar polls con pesos
def reference_class(event, similar_events)   # Reference class forecasting
def bayesian_update(prior, evidence)         # Actualizar probabilidad con nueva info
def monte_carlo_sim(params, n=10000)         # Simulación de escenarios
def calibration_check(predictions, outcomes) # Brier score
```

### edge_calculator.py
```python
def expected_value(my_prob, market_price)     # EV de la bet
def kelly_fraction(my_prob, market_price)     # Sizing óptimo
def half_kelly(my_prob, market_price)         # Sizing conservador
def max_exposure_check(position, bankroll)    # No pasar de X% en una bet
def correlation_check(new_bet, existing_bets) # Correlación entre bets
```

### market_scanner.py
```python
def scan_mispriced(threshold=0.05)           # Mercados con edge >5%
def scan_volume_spike(threshold=2.0)         # Volumen anormal
def scan_whale_activity(min_size=10000)      # Movimientos grandes
def scan_near_resolution(days=7)             # Mercados que resuelven pronto
def scan_new_markets(hours=24)               # Mercados nuevos
```

## Reglas de betting (betting-rules.md)

### Sizing
- **NUNCA más del 5% del bankroll en una sola bet**
- **Half-Kelly por defecto** (más conservador, reduce varianza)
- **Max exposure correlacionada: 15%** (bets que se mueven juntas)
- **Min edge para apostar: 5%** (mi prob - market prob > 5pp)
- **Min confidence: 70%** (confidence interval no cruza el precio de mercado)

### Process
- **SIEMPRE estimar probabilidad ANTES de ver el precio**
- **SIEMPRE hacer devil's advocate antes de apostar**
- **SIEMPRE verificar resolution criteria** (el fine print mata)
- **SIEMPRE calcular EV y Kelly** — nunca apostar por "feeling"
- **POST-MORTEM obligatorio** en cada bet resuelta (win AND loss)

### Bankroll management
- **Drawdown >20%: reducir sizing a quarter-Kelly** hasta recovery
- **Drawdown >30%: STOP. Review completo del sistema**
- **Track Brier score** — si >0.25, el modelo necesita recalibración
- **Separate bankroll** del portfolio de inversión — nunca mezclar

### Categorías y calibración
- Mantener Brier score POR CATEGORÍA
- Si una categoría tiene Brier >0.3 → STOP betting en esa categoría
- Las categorías donde estoy mejor calibrado → más sizing
- Las categorías donde estoy peor → menos sizing o no apostar

## Smart Money / OSINT para Polymarket

### Whale tracking
- Monitorizar wallets grandes (>$50K bets)
- ¿Qué apuestan los whales? ¿Cuándo?
- ¿Hay insiders? (gente con información no pública)
- Movimientos grandes antes de noticias = señal

### Cross-platform
- Comparar precios Polymarket vs Kalshi vs Metaculus vs PredictIt
- Arbitraje entre plataformas = edge sin riesgo
- Si Polymarket dice 60% y Metaculus dice 40% → alguien está mal

### News flow
- Velocidad de incorporación de noticias al precio
- Si una noticia material sale y el precio no se mueve → posible edge
- Si el precio se mueve ANTES de la noticia → insiders

## Métricas de éxito

| Métrica | Target | Frecuencia |
|---------|--------|------------|
| ROI | >10% anual | Mensual |
| Brier score | <0.20 | Semanal |
| Win rate | >55% (con sizing correcto) | Semanal |
| Avg edge per bet | >5pp | Por bet |
| Max drawdown | <20% | Continuo |
| Bets activas | 5-15 | Continuo |
| Post-mortems | 100% de bets resueltas | Por resolución |
| Calibration | Within 5pp of perfect | Mensual |

## Anti-compaction (qué debe sobrevivir)

1. `CLAUDE.md` — identity, role, rules
2. `session-protocol.md` — qué hacer al iniciar
3. `betting-rules.md` — sizing, Kelly, bankroll
4. `portfolio/current.yaml` — posiciones activas
5. `state/session_continuity.yaml` — contexto de sesión
6. `markets/active/*/thesis.md` — thesis de cada bet activa
7. `state/standing_bets.yaml` — bets pendientes de ejecutar

## Diferencias clave vs Investment Specialist

| Aspecto | Investment | Polymarket |
|---------|-----------|------------|
| Horizonte | Meses-años | Días-semanas |
| Sizing | 5-15% por posición | 1-5% por bet |
| Edge | Valoración fundamental | Probabilidad vs precio |
| Risk | Drawdown, concentración | Bankroll, correlación, ruina |
| Resolution | Mercado decide (indefinido) | Fecha fija de resolución |
| Information | 10-K, earnings, insiders | News, polls, data, insiders |
| Calibración | FV accuracy (quarterly) | Brier score (weekly) |
| Moat | Quality scoring, DCF | Modelo probabilístico, velocidad |
| DA | 1 per position | 1 per bet (faster cycle) |
| Post-mortem | Opcional | OBLIGATORIO (win AND loss) |

## Cómo empezar

1. **Crear repo** `polymarket_specialist/`
2. **Escribir CLAUDE.md** con identity, role, rules adaptadas
3. **Crear tools básicos**: `polymarket_client.py` (API), `edge_calculator.py` (EV/Kelly)
4. **Crear session-protocol.md**: qué hacer al iniciar (scan markets, check positions, news)
5. **Primera bet**: seguir pipeline completo D1→D5 con un mercado sencillo (binario, alta liquidez)
6. **Iterar**: post-mortem de cada bet, ajustar modelo, mejorar calibración
7. **Escalar**: añadir agentes por categoría según dónde haya mejor calibración

## Integración con Gobernator

El gobernator puede gestionar ambos especialistas:
- Mismo inbox/outbox
- Mismo challenge protocol (preguntas constructivas)
- Mismo daily report (sección para cada especialista)
- Bankrolls SEPARADOS — nunca mezclar capital de inversión con betting
- Audit independiente — cada especialista se audita por separado

## Lecciones del Investment Specialist que aplican

1. **Agentes > Tools** — el juicio importa más que los cálculos
2. **Pipeline formal** — no apostar sin thesis escrita
3. **Devil's advocate obligatorio** — siempre cuestionar antes de actuar
4. **Anti-compaction** — todo en ficheros, nada en conversación
5. **Challenge protocol** — preguntas constructivas multi-turn
6. **Dosificación** — una bet a la vez, no batch
7. **Post-mortem** — aprender de CADA resultado (en inversión lo hacemos poco, aquí es obligatorio)
8. **Calibración** — medir si nuestras probabilidades son buenas (Brier score es el QS de Polymarket)
9. **Smart money** — trackear whales como trackeamos fondos quality
10. **Accountability** — meta-compliance score, objectives check, auto-examen
