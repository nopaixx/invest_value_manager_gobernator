# eToro Integration — Gobernator Reference

## Architecture

```
Specialist decides → Gobernator executes via API → Angel notified via Telegram
```

- Specialist does NOT know about this integration. He thinks Angel executes manually.
- Gobernator owns execution. All trades go through `etoro/client.py`.
- Demo mode active (sandbox). Switch to real by changing keys and endpoints.

## Authentication

3 headers required on every request:
- `x-request-id`: UUID (generated per request)
- `x-api-key`: public key (identifies app)
- `x-user-key`: user key (identifies account + permissions)

Keys stored in `.env`:
- `ETORO_API_KEY` — public key
- `ETORO_USER_KEY_REAL` — real account, READ only
- `ETORO_USER_KEY_DEMO` — demo account, READ + WRITE

## Account IDs

- GCID: 21803098
- Real CID: 21519670
- Demo CID: 23030605

## Client Usage

```python
from etoro.client import EtoroClient
c = EtoroClient()          # default: demo
c = EtoroClient("real")    # real account (read only for now)
```

### Core
```python
c.get_identity()                    # → {gcid, realCid, demoCid}
c.get_portfolio()                   # → positions list
c.get_pnl()                        # → PnL + credit (cash)
```

### Market Data
```python
c.search_instrument("ADBE")        # → [{instrumentId, name, symbol}]
c.get_instrument_info([1126, 4346]) # → instrument metadata (batched, max ~2 per batch)
c.get_rates([1126, 4346])          # → current bid/ask prices
c.get_candles(1126, "OneDay", 30)  # → OHLCV historical data
```

### Trading (demo only for now)
```python
c.open_position_by_amount(1126, 500)           # buy $500 of ADBE
c.open_position_by_amount(1126, 500, is_buy=False)  # short $500 of ADBE (CFD)
c.open_position_by_units(1126, 2.0)            # buy 2 shares of ADBE
c.close_position(position_id)                   # close entire position
c.close_position(position_id, units_to_deduct=1.0)  # partial close
c.place_limit_order(1126, 240.0, 500)          # buy $500 when ADBE hits $240
c.cancel_order(order_id)                        # cancel pending order
```

### Social
```python
c.create_post("My analysis... #ValueInvesting")              # simple post
c.create_post("Analysis...", tags=[{"name": "ADBE"}])         # with tags
c.create_post("Link...", attachments=[{"url": "https://..."}]) # with attachment
```

## Instrument IDs

Each eToro asset has a numeric ID (e.g. ADBE = 1126). The API requires IDs, not tickers.

**Auto-resolving cache:** `etoro/instruments.json`
- `c.resolve_ticker("ADBE")` → checks cache first, API fallback, saves new entries automatically
- IDs are immutable (never change) — cache never invalidates
- New tickers are auto-discovered and cached on first use

No need to maintain a manual table — the cache grows organically.

## API Gotchas (learned the hard way)

1. **`searchText` param doesn't filter** — returns all instruments paginated. Use `internalSymbolFull` instead for ticker lookup.
2. **`instrumentIds` param must be repeated**, not comma-separated. Use `?instrumentIds=X&instrumentIds=Y`, not `?instrumentIds=X,Y`. Comma-separated returns 500 error.
3. **`get_instrument_info` fails with >2-3 IDs** at once — 500 Internal Server Error. Batch with size 1-2 to be safe.
4. **Portfolio endpoint is `/trading/info/{mode}/portfolio`**, not `/trading/{mode}/portfolio`. The `info/` segment is required.
5. **Search returns `instrumentId` (camelCase)**, but portfolio/instrument endpoints return `instrumentID` (uppercase D). Watch the casing.
6. **Account currency is EUR** but API amounts are in USD. Conversion rates included in PnL response (`openConversionRate`, `closeConversionRate`).
7. **Demo and real have separate endpoints**: `/trading/execution/demo/...` vs `/trading/execution/real/...`. Same for `/trading/info/demo/...` vs `/trading/info/real/...`.
8. **Real account key only has READ permission** currently. Write requires either: depositing funds, full verification, or eToro enabling it. Demo key has READ+WRITE.
9. **Markets must be open to execute trades**. Weekend/holiday orders will fail. Always check day/time before executing.
10. **Instrument IDs are immutable** — they never change even if a company rebrands. Safe to hardcode/cache.
11. **`create_post` body field is `message`**, not `text`. The API returns 422 "missing message body" if you use `text`.
12. **Posts can be published anytime** — no market hours restriction. Social feed is always available.

## Switching Demo → Real

When Angel activates real account:
1. Change `self.mode` default or pass `mode="real"` to methods
2. Ensure `ETORO_USER_KEY_REAL` has WRITE permission (regenerate key in Settings → Trading → API Key Management)
3. Endpoints auto-switch: `/demo/` → `/real/`
4. **Simulate total portfolio of ~$10K** (not the full $88K demo cash)
5. Angel confirms all orders — but VERIFY market hours before executing

## Consolidation Plan (pending, execute Monday)

1. Close positions NOT in specialist portfolio: DTE.DE, MORN, BYIT.L, DOM.L, GL, LULU
2. Ask specialist for current weights
3. Adjust existing positions to match specialist weights
4. Open missing positions: FTNT, TW, HLNE, WKL.NV
5. Target total: ~$10K invested (matching specialist simulation)
6. SELL BZU.MI at BIT open (confirmed by Angel)

## eToro Popular Investor Program

- Risk score 1-10 based on portfolio volatility (daily std dev)
- Our estimated score: ~3-4 (beta 0.80, low correlation 0.151, no leverage)
- Elite tier: 50+ copiers, $50K+ AUM, 12+ months track record
- No stop losses needed — kill conditions serve same purpose intelligently
- Spain: CFD restrictions for new accounts post Aug 2024, but Angel's account (2023) has grandfathering

## OpenAPI Spec

Full spec saved at: `etoro_openapi.json` (471KB, v1.156.0)
Docs portal: https://api-portal.etoro.com
MCP integration: `claude mcp add --transport http etoro-api-docs https://api-portal.etoro.com/mcp`

## Reference Links

### API Documentation
- Portal principal: https://api-portal.etoro.com
- Getting started: https://api-portal.etoro.com/getting-started
- Authentication: https://api-portal.etoro.com/getting-started/authentication.md
- Find instrument ID: https://api-portal.etoro.com/guides/get-instrument-id.md
- Open/close orders: https://api-portal.etoro.com/guides/market-orders.md
- Calculate cash: https://api-portal.etoro.com/guides/calculate-available-cash.md
- Calculate equity: https://api-portal.etoro.com/guides/calculate-equity.md
- Calculate P&L: https://api-portal.etoro.com/guides/calculate-profit-loss.md
- Watchlists: https://api-portal.etoro.com/guides/watchlists.md
- OpenAPI JSON: https://api-portal.etoro.com/api-reference/openapi.json
- Full docs index (LLM): https://api-portal.etoro.com/llms.txt

### Claude Code / MCP Integration
- Claude Code guide: https://api-portal.etoro.com/vibe-code/claude-code.md
- Cursor guide: https://api-portal.etoro.com/vibe-code/cursor.md
- eToro Portfolio MCP Server: https://glama.ai/mcp/servers/@shlomico-tr/etoroPortfolioMCP

### Community / GitHub
- Python API wrapper (OpenAPI generated): https://github.com/mkhaled87/etoro-api
- REST API client: https://github.com/ok24601/etoro-api

### Regulatory (Spain)
- CNMV CFD restrictions: https://cms.law/es/esp/publication/la-cnmv-aprueba-nuevas-medidas-restrictivas-en-relacion-con-los-cfds-en-espana
- eToro CFD blocked countries: https://help.etoro.com/s/article/Is-CFD-trading-blocked-in-my-country?language=en_GB
- eToro Spain guide: https://wikitoro.org/countries/etoro-spain
- Why can't I trade CFDs: https://wikitoro.org/trading/etoro-cfd/why-cant-i-trade-cfds-on-etoro

### eToro Popular Investor
- Risk score explanation: https://help.etoro.com/s/article/what-is-the-risk-score (buscar en help center)
- Short position restrictions: https://help.etoro.com/s/article/Why-can-t-I-open-a-short-position?language=en_GB

### eToro News / Announcements
- API launch (Oct 2025): https://www.etoro.com/news-and-analysis/press-releases/etoro-marks-15-years-of-social-investing-with-launch-of-public-apis-and-expansion-of-copytradertm-to-the-us/
- API overview: https://fintech.global/2025/10/30/etoro-unveils-open-apis-and-brings-copytrader-to-the-us/
