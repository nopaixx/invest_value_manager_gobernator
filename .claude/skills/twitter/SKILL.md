---
name: twitter
description: Daily X/Twitter promotion session. Publishes tweets, responds to FinTwit, follows relevant accounts, quotes and likes quality content. Use once daily around 14:00 CET.
argument-hint: [number of tweets to publish, default 5]
---

# X/Twitter Daily Promotion

## Pre-requisites
- Chrome must be open (Claude in Chrome extension required)
- User must be logged into x.com as @nopaixx
- Today's tweet files must exist in `reports/tweets/YYYY-MM-DD-x.md`

## Workflow

### Step 1: Load browser tools
Use ToolSearch to load: `mcp__claude-in-chrome__tabs_context_mcp`, `mcp__claude-in-chrome__navigate`, `mcp__claude-in-chrome__computer`, `mcp__claude-in-chrome__read_page`, `mcp__claude-in-chrome__form_input`

### Step 2: Get browser context
Call `tabs_context_mcp` with `createIfEmpty: true`

### Step 3: Generate tweets if not done today
- Check if `reports/tweets/YYYY-MM-DD-x.md` exists
- If not, ask specialist for 5 data points (smart money, contrarian angles, stress test, discoveries, quant)
- Generate 5 tweets following X rules (see below)
- Save to `reports/tweets/YYYY-MM-DD-x.md`

### Step 4: Publish tweets
- Navigate to x.com/home
- For each tweet in today's file:
  - Click the post text field (ref for "Post text" textbox)
  - Type the tweet text
  - Take screenshot to check character indicator — if red circle with negative number, clear text (ctrl+a, Backspace) and rewrite shorter
  - **PUBLISH VIA JAVASCRIPT** (click by coordinates is unreliable):
    - Home timeline post: `document.querySelector('[data-testid="tweetButtonInline"]').click()`
    - Reply/Quote modal post: `document.querySelector('[data-testid="tweetButton"]').click()`
  - Wait 3 seconds, take screenshot to verify "Your post was sent" or empty composer
  - If text is still in composer, the post failed — retry with JavaScript click
- Space tweets 2-3 minutes apart for better algorithm treatment
- **NEVER use coordinate clicks for Post/Reply buttons** — they miss due to viewport offset issues

### Step 5: Engage with community (15-20 min)
1. **Search #ValueInvesting, #QualityInvesting, $ADBE, $HLNE, $GDDY** (our tickers)
2. **Reply to 3-5 tweets** from large accounts with intelligent, data-backed comments
   - Add value — share a specific number, insight, or contrarian angle
   - Reference our real experience when relevant
   - Keep replies under 280 chars
3. **Quote tweet 1-2 good posts** adding our quant/value angle
4. **Like 10-15 tweets** in the value investing space
5. **Follow 3-5 new relevant accounts** (quality investors, fund managers, quant traders)

### Step 6: Log activity
- Update `state/twitter_log.md` with: date, tweets published count, replies count, follows count

## X Tweet Rules (HARD)
- MAX 280 characters — shorter is better
- NO links in main tweet (kills reach) — links go in self-reply
- Pregunta al final SIEMPRE (algorithm rewards replies)
- Max 2 hashtags
- Datos concretos > opiniones. "$ADBE P/E 14.9x" > "Adobe está barata"
- Tono directo, imperfecto, como desde el móvil
- Tickers con $ siempre ($GDDY, $HLNE)
- TONO HUMANO — no AI-sounding. Conversational, imperfect, direct.
- **ALWAYS ask specialist for fresh data points FIRST** — never generate tweets from own knowledge. Specialist has the real discoveries, signals, and data.
- **NEVER admit amateur mistakes publicly** — don't mention using Wikipedia as data source, don't reveal internal errors that make us look unprofessional. Show process improvements, not embarrassing failures.
- **NEVER repeat same themes** across tweets — each tweet must cover a DIFFERENT topic. No "beta 0.62" in 3 tweets.
- **Prepare engagement topics** alongside tweets — 3-4 debate angles for replies during the day.

## Topic Rotation (daily)
a) Smart money / insider signals
b) Specific thesis ("market is wrong" + ticker)
c) Macro / historical / geopolitical
d) Portfolio process / credibility / stress tests
e) Quant angle — correlations, reverse DCF, backtesting
f) Baskets / secular themes
g) Personal story — from pure quant to quant + value

## Engagement Rules
- Only respond to tweets where we can ADD VALUE with data or experience
- Never spam, self-promote without substance, or post generic comments
- Contrarian takes welcome — generates debate
- Mention our eToro portfolio link in bio, not in replies
- Be genuinely helpful — growth follows value

## Growth Strategy (learned from Grok, March 2026)

### Core Differentiator
"Ex-Numerai #1 quant + public eToro portfolio + international shorts" = extremely rare on FinTwit. Lean ALL the way in.

### Reply Strategy (fastest 0→1K path)
- **20 replies/day** to big accounts (QCompounding, BrianFeroldi, morganhousel, iancassel, etc.)
- Reply EARLY on their posts (first 30 min = most visibility)
- Go to their PROFILE, like + reply their recent posts — not just search
- Add data/experience, never generic comments
- Diversify topics: don't repeat ADBE/GDDY. Use correlations, stress test, baskets, shorts, kill conditions, insider clusters, geographic diversification, regime detection, etc.

### Content Strategy (barbell approach)
- **Short punchy tweets** (daily) — one data point, one insight, one question
- **Threads** (1-2/week) — deep dives that feel like "insider leaks" or "here's exactly how I do it"
- **Polls** occasionally ("Value trap or bargain? Vote + why")
- **Quote-tweets** of viral posts with our quant angle

### Thread Ideas (high engagement, from Grok)
1. "From Numerai #1 to Value Investing" — origin story + why quant alone isn't enough
2. "My 12 Quality Compounders" — full holdings, DCF, QS, insider data, 1 tweet per position
3. "Monte Carlo Stress Test: My Entire Portfolio" — recession, inflation, oil shock scenarios
4. "Why I Short $TSLA at 386x and Buy $ADBE at 14.9x" — contrarian thesis with data
5. "$3.2M in Insider Buying Nobody Noticed" — $HLNE deep dive with academic research

### Milestones
- Month 1: 100-200 followers. Profile + 20 replies/day + 3 posts/week + one intro thread
- Month 2-3: 500+. Ramp to 5 posts/week + portfolio update thread. Track analytics
- By 1K: reciprocity — people start replying to YOU

### What Kills Growth
- Posting more than engaging (ratio should be 3:1 replies:posts)
- Generic hot takes or recycled news
- AI-sounding content (no AI slop)
- Only talking about same 2-3 tickers

## Schedule
- Best time to publish: 14:00-16:00 CET (morning US = peak FinTwit)
- Run this skill ONCE per day
- Total session: ~30-40 minutes (20 min engagement + 10-15 min publishing)
