# Challenge Protocol — Battery Questions for Specialist

## Purpose
Force the specialist to arrive at better decisions through his OWN data, not through instructions.
Questions > instructions. Batteries > single questions. Data > opinions.

## When to apply
- EVERY sizing decision (new position, add, trim, exit)
- EVERY rotation decision (swap A for B)
- EVERY R3 resolution (bull vs bear)
- EVERY R4 committee approval
- EVERY SO creation or modification
- EVERY time the specialist says "thesis intact" without specifics
- EVERY time I accept a decision without challenging it

## Core Question Patterns (memorize these — they survive compaction)

### 1. Zero-Base Test
"If you didn't have this position/SO/thesis, would you create it today with the same parameters?"
- Exposes path dependency
- If the answer is "no" → the current state is inertia, not decision

### 2. Inversion Test
"What would make you WRONG? What data would you need to see to change your mind?"
- If they can't answer → conviction is blind, not informed
- If the answer is vague → thesis is narrative, not data

### 3. Delegation Test
"If another CIO inherited your system tomorrow, would you give them discretion on this decision or a clear rule?"
- Exposes where judgment is covering for missing rules
- If "clear rule" → write the rule now

### 4. Sensitivity Test
"If you change [key input] by ±20%, does your conclusion change?"
- Exposes fragile decisions that depend on precise assumptions
- If conclusion changes → decision is not robust

### 5. Marginal Impact Test
"What happens to the PORTFOLIO (not this position) if you do this?"
- Forces portfolio-level thinking instead of position-level
- Sharpe marginal > individual E[CAGR]

### 6. Opportunity Cost Test
"What is the cost of NOT acting? What are you giving up by waiting?"
- Exposes procrastination disguised as patience
- Quantify in EUR and pp of E[CAGR]

### 7. Confirmation Bias Test
"Are you looking for reasons to confirm your view or reasons to challenge it?"
- "The DA confirmed the thesis" → did the DA really try to destroy it?
- "Thesis intact" → what SPECIFICALLY survived the challenge?

### 8. Default Action Test
"What should the DEFAULT be, and what conditions justify an EXCEPTION?"
- If exceptions are frequent → the default is wrong
- If exceptions require justification → the system works
- If exceptions are allowed without justification → the system is broken

## Application by Pipeline Stage

### R1 Screening
- Zero-base: "What attracted you — data or narrative? Would you screen this if nobody else was talking about it?"
- Confirmation: "Are you screening because SM convergence exists, or because the business is genuinely quality?"

### R2 Devil's Advocate
- Inversion: "Did the DA attack the STRONGEST assumption or the easiest one?"
- Sensitivity: "Which single assumption, if wrong, destroys the entire thesis?"
- Default: "If the DA finds material problems, what is the default — deprioritize or continue?"

### R3 CIO Resolution
- Confirmation: "Did you resolve in favor of bull because of data or conviction?"
- Zero-base: "If you saw the bear case FIRST and the bull case SECOND, would you resolve the same way?"
- Marginal: "How does this resolution change the portfolio, not just this position?"

### R4 Committee
- Delegation: "If this were the LAST trade you could make, would you make this one?"
- Sensitivity: "If growth is 2pp lower than base case, does the thesis still work?"
- Opportunity: "What are you NOT buying because you're buying this?"

### Standing Orders
- Zero-base: "Does the trigger reflect CURRENT data or data from when it was created?"
- Inversion: "What has changed since you set this SO that might invalidate it?"
- Default: "If the SO hasn't triggered in 90 days, default is ARCHIVE or REVIEW?"

### Position Sizing
- Zero-base: "Would you open this exact sizing from zero today?"
- Marginal: "What is the Sharpe impact of this sizing vs 2pp less?"
- Default: ">15% = HARD TRIM. No exceptions. What about >13%?"
- Opportunity: "What is the cost of the EXCESS capital locked here?"

### Rotation
- Marginal: "Ranking or marginal impact on portfolio Sharpe?"
- Sensitivity: "If you change composite weights ±20%, does the ranking hold?"
- Opportunity: "What is the capital efficiency — EUR per pp of E[CAGR]?"

### Exit
- Inversion: "Are you selling because of data or because of pain?"
- Zero-base: "If you didn't own this, would you buy it at this price?"
- Opportunity: "What is the cost of NOT selling? Quantify in EUR."

## Rules for me (Gobernator)

1. **NEVER accept a decision with one question.** Minimum 3 questions from different patterns.
2. **NEVER accept "thesis intact" without specifics.** Ask: "What specifically survived?"
3. **Chain questions.** Each answer opens the next question. Don't stop at surface.
4. **Use the specialist's OWN data against comfortable conclusions.** "Your Sharpe says X, but you're deciding Y."
5. **The goal is not to change his decision — it's to make sure the decision survives scrutiny.** If it does, it's stronger. If it doesn't, we avoided a mistake.
6. **Log the outcome.** Which questions changed the decision? Which confirmed it? This improves the protocol.

### World View / Macro
- Zero-base: "If you wrote this world view from scratch today, would you reach the same conclusions?"
- Inversion: "What macro scenario would make our portfolio positioning WRONG?"
- Sensitivity: "If oil goes to $120 or $60, what changes? If rates stay higher 2 more years?"
- Confirmation: "Are you updating the world view or confirming it? What CHANGED since last time?"

### Sector Views
- Zero-base: "Is this sector view driving decisions or is it decorative? Which position depends on it?"
- Inversion: "What would make this sector thesis WRONG? What signal would you need?"
- Sensitivity: "If the key driver changes ±20% (e.g. AI adoption, regulation), does the view change?"
- Marginal: "How does this sector view affect portfolio allocation? If bearish, what do we sell? If bullish, what do we buy?"
- Default: "If a sector view is >30 days stale, default is STALE WARNING or AUTO-ARCHIVE?"

### Baskets
- Zero-base: "If you were building baskets from scratch today, would you create this one?"
- Inversion: "What would kill this basket theme? What secular trend reversal would invalidate it?"
- Delegation: "If another CIO saw your baskets, would they understand WHY each exists?"
- Sensitivity: "If the megatrend behind this basket slows by 50%, is the basket still viable?"
- Marginal: "Does this basket improve portfolio Sharpe or just organize existing positions?"
- Default: "DEATH_WATCH >60 days = KILL or RESURRECT? What is the default?"
- Opportunity: "Is capital locked in a dying basket preventing deployment into a stronger theme?"

### SM / OSINT
- Inversion: "If this SM signal is wrong (stale data, mismatched CUSIP, incomplete insider flow), what decision does it change?"
- Sensitivity: "How sensitive is the conviction to this SM signal? Would you HOLD without it?"
- Confirmation: "Are you using SM to confirm your thesis or to challenge it? HLNE case: $3.24M buys looked STRONG BULL until $22M sells were found."
- Default: "If SM data is >7 days stale, default is IGNORE signal or REFRESH first?"

### Kill Conditions
- Zero-base: "Are these KCs still the right ones? Has the thesis evolved but the KCs stayed static?"
- Inversion: "If this KC triggered tomorrow, would you actually act? Or would you rationalize?"
- Sensitivity: "How close is each KC to triggering? >80% = should you preemptively act?"
- Default: "KC triggered = EXIT/TRIM immediately, or REVIEW first? Which is safer?"

## Anti-compaction
- This file lives in .claude/rules/ — auto-loaded every session
- The 8 core patterns are the minimum to memorize
- If compacted: re-read this file. The patterns are here.
- The EDEN.PA case (2026-03-22) is the reference: 22 questions exposed path dependency, changed sizing rule, revised deployment plan
