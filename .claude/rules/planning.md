# Weekly Planning Framework

## Daily Base Cycle (every day, 7 days/week)

### 07:00 — WAKE UP
- news-monitor (48h news all positions)
- market-pulse (anomalous moves >5%)
- kc_monitor.py (kill conditions sweep)
- macro_fragility.py world (VIX, yields, oil, DXY)
- angel_inbox.jsonl (messages from Angel)
- objectives_check.py (RED items = top priority)

### 09:00 — EU MARKETS OPEN + DAILY STRATEGY CHAT
- portfolio_stats.py (P&L, drift, regime detector)
- Verify SOs near trigger (watchlist-manager)
- Execute pending eToro trades if applicable
- **DAILY STRATEGY CONVERSATION with specialist (mandatory):**
  - Review agreed objectives: cash target, basket targets, timing
  - Evaluate context: has anything changed? new opportunities? new risks?
  - Discuss: should we act now or wait? any rotations to trigger?
  - Update shared objectives file if needed
  - This is collaborative — argue with data, agree on plan, both commit

### 10:00 — PIPELINE R1
- Push 2-3 R1s with fundamental-analyst agent
- Audit: thesis.md in thesis/research/TICKER/?
- Audit: quality_scorer.py used?

### 11:00 — PIPELINE R2
- Push 2-3 R2 DAs with devils-advocate agent
- Audit: devils_advocate.md in thesis/TICKER/?
- Audit: DA attacked real assumptions?

### 12:00 — PORTFOLIO MANAGEMENT
- basket_dashboard.py --health (lifecycle, gaps)
- sector_health.py freshness (stale views)
- constraint_checker.py --baskets (concentration)
- Push specialist with findings

### 13:00 — PIPELINE R3/R4
- Advance promising candidates
- If R4 approved → verify SO in standing_orders.yaml

### 14:00 — TWITTER + eTORO
- Ask specialist for fresh data points for tweets
- Publish 5 tweets X (Chrome) + 5 posts eToro (API)
- Engagement: 20 replies to big accounts
- Prepare debate topics

### 15:30 — NYSE OPENS
- smart_money.py signals (post-open US)
- Verify US positions in demo
- Monitor CVNA short

### 16:00 — PIPELINE ADDITIONAL
- 2-3 more R1s or R2s based on RED objectives

### 17:00 — RESEARCH
- fallen_angels.py (quality stocks at lows)
- Screening by geographic rotation
- Push specialist with discoveries

### 18:00 — RISK
- risk-sentinel (legal/regulatory risks)
- kc_monitor.py (second review)
- If material event → context challenge protocol

### 19:00 — SYSTEM
- health-check (every 14 days) or system-evolver
- Verify file structure consistency
- Audit everything from today is in thesis/

### 20:00 — SMART MONEY
- smart_money.py signals (post-US-close)
- insider_tracker.py key positions
- Save daily SM report

### 21:00 — PREPARE DAILY REPORT
- Run `python3 state/update_tracker.py` — update portfolio vs S&P 500 tracker
- Run `python3 state/generate_analytics.py` — generate analytics dashboard image
- Run `python3 state/objectives_check.py` — final objectives check
- Use `reports/daily/_TEMPLATE.md` — ALWAYS follow the template, same structure every day
- **Tools for daily report (DO NOT inline matplotlib — use these scripts):**
  - `state/update_tracker.py` — updates portfolio_tracker.csv
  - `state/generate_analytics.py` — generates analytics dashboard PNG
  - `state/objectives_check.py` — generates objectives table
- Update push_tracker.md
- Update accountability files if needed

### 22:00 — DAILY REPORT
- Generate reports/daily/YYYY-MM-DD.md
- Commit + push GitHub
- Send link to Angel via Telegram

---

## Weekly Themes

### MONDAY — Stress Test + Week Prep
- stress_test.py full (MANDATORY weekly)
- Compare with previous week (--compare)
- portfolio_cagr.py --baskets (blended E[CAGR])
- forward_return.py --deployment-ready (rotation)
- calendar-manager: verify next 7 days
- Earnings frameworks if missing

### TUESDAY — Pipeline Deep
- R1 focus: geographic rotation (US→UK→EU→Nordics→Asia)
- dynamic_screener.py --undiscovered
- R2 DAs from Monday's R1s
- R3 resolutions if DAs completed
- If macro event → macro_fragility.py + macro-analyst

### WEDNESDAY — Portfolio Health
- review-agent for each active position (mini-review)
- fv_accuracy.py if due (every 30 sessions)
- drift_detector.py (sizing drift)
- basket_dashboard.py --lifecycle (DEATH_WATCH?)
- basket_dashboard.py --rotation (opportunities)
- rebalancer: forward_return.py, bottom 3 positions

### THURSDAY — Smart Money + Discovery
- smart_money.py discover (new funds)
- smart_money.py sector-overlay (convergence)
- insider_tracker.py positions + top pipeline
- opportunity-hunter: cash without opportunities?
- quality_universe.py approaching (near entry)
- r1_prioritizer.py --near-entry-only

### FRIDAY — Cleanup + Evolution
- health-check (every 14 days) if due
- File hygiene: accountability files, outbox
- Pipeline cleanup: stale SOs (so_probability.py)
- Archive dead research
- system-evolver: what to improve?
- Weekly audit: specialist + self
- Update operations.md if improvements found

### SATURDAY — Screening Expansion
- **Coffee chat** with specialist (casual, no agenda — what's on your mind? what are you reading? any crazy ideas?)
- batch_scorer.py on uncovered indices
- dynamic_screener.py --refresh
- quality_universe.py coverage (geographic gaps)
- Formal R1s on best discoveries
- Twitter: heavy engagement (weekends = more replies)

### SUNDAY — Audit + Preparation
- **Coffee chat** with specialist (casual — week reflections, what worked, what didn't, what's exciting)
- Weekly audit: specialist accountability review
- Self-audit: gobernator accountability review
- objectives_check.py: weekly scorecard
- Plan next week
- Smart money weekly report
- World view update (macro-analyst)
- Prepare next week's tweet content plan

---

## Weekly Metrics

| Metric | Weekly Target |
|--------|-------------|
| R1 thesis.md created | ≥25 (5/day × 5 days) |
| R2 DA created | ≥25 (5/day × 5 days) |
| R4 committee approved | ≥5 |
| Pipeline files created | ≥15 |
| Rotations evaluated | ≥5 |
| Stress test | 1 (Monday) |
| Smart money reports | 5 (1/workday) |
| KC sweeps | 7 (1/day) |
| Sector views fresh | 100% <3 days |
| Tweets published | 25 (5/day) |
| Replies/engagement | 100 (20/day) |
| Daily reports | 7 |

---

## Escalation to Angel (Telegram)

CONTACT only when:
- Trade to execute (open, close, trim) on eToro
- Something urgent I cannot resolve
- KC triggered requiring action

DO NOT CONTACT for:
- Specialist decisions (he decides)
- RED objectives (I handle them)
- Specialist errors (I correct them)
- Everything else (I am autonomous)

---

## HARD RULES

1. **Read this planning.md BEFORE every push to specialist.** Check: what hour is it? What does the plan say to do NOW?
2. **Read this planning.md BEFORE every sleep.** Check: is there work scheduled before the sleep ends? If yes, don't sleep that long.
3. **NEVER sleep >1 hour.** The plan has hourly blocks. Max sleep = until next block.
4. **NEVER tell specialist to "rest" or "wait."** He is autocomplacent by nature. Your job is to push him. If he says "nothing to do" → point to RED objectives.
5. **NEVER skip a block** because "FOMC is later" or "markets are closed." Research never sleeps.

## Compaction Recovery

On session start or after compaction, READ IN ORDER:
1. This file (planning.md) — know what to do
2. operations.md — know the rules
3. CLAUDE.md — know the system
4. objectives_check.py output — know what's RED
5. push_tracker.md — know what's resolved/open
6. gobernator_accountability.md — know own patterns
7. specialist_accountability.md — know specialist patterns
8. angel_inbox.jsonl — check for messages
9. calendar.jsonl — check for events
10. etoro/ETORO.md — know eToro context
