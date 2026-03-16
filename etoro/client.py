"""eToro API client."""

import json
import logging
import uuid
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTRUMENT_CACHE = Path(__file__).resolve().parent / "instruments.json"
load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = "https://public-api.etoro.com/api/v1"


class EtoroClient:
    """Simple eToro API client."""

    def __init__(self, mode: str = "demo") -> None:
        self.mode = mode
        self.api_key = os.environ["ETORO_API_KEY"]
        self.user_key_real = os.environ["ETORO_USER_KEY_REAL"]
        self.user_key_demo = os.environ["ETORO_USER_KEY_DEMO"]
        self.session = requests.Session()

    def _user_key(self, mode: Optional[str] = None) -> str:
        m = mode or self.mode
        return self.user_key_real if m == "real" else self.user_key_demo

    def _headers(self, mode: Optional[str] = None) -> dict[str, str]:
        return {
            "x-request-id": str(uuid.uuid4()),
            "x-api-key": self.api_key,
            "x-user-key": self._user_key(mode),
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        path: str,
        mode: Optional[str] = None,
        **kwargs,
    ) -> dict:
        url = f"{BASE_URL}{path}"
        headers = self._headers(mode)
        resp = self.session.request(method, url, headers=headers, **kwargs)
        logger.info("%s %s -> %s", method.upper(), url, resp.status_code)
        if not resp.ok:
            logger.error("Response body: %s", resp.text)
            resp.raise_for_status()
        return resp.json()

    # ── Core ──────────────────────────────────────────────────────────

    def get_identity(self) -> dict:
        """GET /api/v1/me"""
        return self._request("GET", "/me")

    def get_portfolio(self, mode: Optional[str] = None) -> dict:
        """GET /api/v1/trading/info/{mode}/portfolio"""
        m = mode or self.mode
        return self._request("GET", f"/trading/info/{m}/portfolio", mode=m)

    def get_pnl(self, mode: Optional[str] = None) -> dict:
        """GET /api/v1/trading/info/{mode}/pnl"""
        m = mode or self.mode
        return self._request("GET", f"/trading/info/{m}/pnl", mode=m)

    # ── Market Data ───────────────────────────────────────────────────

    def _load_cache(self) -> dict[str, int]:
        if INSTRUMENT_CACHE.exists():
            return json.loads(INSTRUMENT_CACHE.read_text())
        return {}

    def _save_cache(self, cache: dict[str, int]) -> None:
        INSTRUMENT_CACHE.write_text(json.dumps(cache, indent=2, sort_keys=True))

    def resolve_ticker(self, ticker: str) -> int:
        """Resolve ticker to eToro instrument ID. Cache first, API fallback."""
        cache = self._load_cache()
        if ticker in cache:
            return cache[ticker]
        results = self.search_instrument(ticker)
        for r in results:
            if r["symbol"].upper() == ticker.upper():
                cache[ticker] = r["instrumentId"]
                self._save_cache(cache)
                logger.info("Cached new instrument: %s -> %d", ticker, r["instrumentId"])
                return r["instrumentId"]
        raise ValueError(f"Instrument not found: {ticker}")

    def search_instrument(self, query: str) -> list[dict]:
        """Search instruments by ticker/symbol. Uses internalSymbolFull param."""
        data = self._request(
            "GET",
            "/market-data/search",
            params={"internalSymbolFull": query, "pageSize": 20},
        )
        q = query.upper()
        results = []
        for item in data.get("items", []):
            symbol = item.get("internalSymbolFull", "")
            name = item.get("internalInstrumentDisplayName", "")
            iid = item.get("instrumentId", 0)
            if iid > 0 and (q in symbol.upper() or q in name.upper()):
                results.append({"instrumentId": iid, "name": name, "symbol": symbol})
        return results

    def get_instrument_info(self, instrument_ids: list[int], batch_size: int = 3) -> dict:
        """GET /api/v1/market-data/instruments — batched to avoid 500 errors."""
        all_data = []
        for i in range(0, len(instrument_ids), batch_size):
            batch = instrument_ids[i : i + batch_size]
            params = [("instrumentIds", str(x)) for x in batch]
            data = self._request("GET", "/market-data/instruments", params=params)
            all_data.extend(data.get("instrumentDisplayDatas", []))
        return {"instrumentDisplayDatas": all_data}

    def get_rates(self, instrument_ids: list[int]) -> dict:
        """GET /api/v1/market-data/instruments/rates?instrumentIds=X&instrumentIds=Y"""
        params = [("instrumentIds", str(i)) for i in instrument_ids]
        return self._request("GET", "/market-data/instruments/rates", params=params)

    def get_candles(
        self,
        instrument_id: int,
        interval: str = "OneDay",
        count: int = 30,
        direction: str = "Descending",
    ) -> dict:
        """GET /api/v1/market-data/instruments/{id}/history/candles/{direction}/{interval}/{count}"""
        path = f"/market-data/instruments/{instrument_id}/history/candles/{direction}/{interval}/{count}"
        return self._request("GET", path)

    # ── Trading ───────────────────────────────────────────────────────

    def open_position_by_amount(
        self,
        instrument_id: int,
        amount: float,
        is_buy: bool = True,
        mode: Optional[str] = None,
    ) -> dict:
        """POST /api/v1/trading/execution/{mode}/market-open-orders/by-amount"""
        m = mode or self.mode
        body = {
            "InstrumentID": instrument_id,
            "Amount": amount,
            "IsBuy": is_buy,
            "Leverage": 1,
        }
        return self._request("POST", f"/trading/execution/{m}/market-open-orders/by-amount", mode=m, json=body)

    def open_position_by_units(
        self,
        instrument_id: int,
        units: float,
        is_buy: bool = True,
        mode: Optional[str] = None,
    ) -> dict:
        """POST /api/v1/trading/execution/{mode}/market-open-orders/by-units"""
        m = mode or self.mode
        body = {
            "InstrumentID": instrument_id,
            "Units": units,
            "IsBuy": is_buy,
            "Leverage": 1,
        }
        return self._request("POST", f"/trading/execution/{m}/market-open-orders/by-units", mode=m, json=body)

    def close_position(
        self,
        position_id: int,
        instrument_id: Optional[int] = None,
        units_to_deduct: Optional[float] = None,
        mode: Optional[str] = None,
    ) -> dict:
        """POST /api/v1/trading/execution/{mode}/market-close-orders/positions/{positionId}"""
        m = mode or self.mode
        body: dict = {}
        if instrument_id is not None:
            body["instrumentID"] = instrument_id
        if units_to_deduct is not None:
            body["UnitsToDeduct"] = units_to_deduct
        return self._request(
            "POST",
            f"/trading/execution/{m}/market-close-orders/positions/{position_id}",
            mode=m,
            json=body,
        )

    def place_limit_order(
        self,
        instrument_id: int,
        rate: float,
        amount: float,
        is_buy: bool = True,
        mode: Optional[str] = None,
    ) -> dict:
        """POST /api/v1/trading/execution/{mode}/limit-orders"""
        m = mode or self.mode
        body = {
            "InstrumentID": instrument_id,
            "Rate": rate,
            "Amount": amount,
            "IsBuy": is_buy,
            "Leverage": 1,
        }
        return self._request("POST", f"/trading/execution/{m}/limit-orders", mode=m, json=body)

    def cancel_order(self, order_id: int, mode: Optional[str] = None) -> dict:
        """DELETE /api/v1/trading/execution/{mode}/limit-orders/{orderId}"""
        m = mode or self.mode
        return self._request("DELETE", f"/trading/execution/{m}/limit-orders/{order_id}", mode=m)

    # ── Social ────────────────────────────────────────────────────────

    def create_post(
        self,
        message: str,
        tags: Optional[list[dict]] = None,
        attachments: Optional[list[dict]] = None,
    ) -> dict:
        """POST /api/v1/feeds/post. Body: {message, tags?, attachments?}"""
        body: dict = {"message": message}
        if tags:
            body["tags"] = {"tags": tags}
        if attachments:
            body["attachments"] = attachments
        return self._request("POST", "/feeds/post", json=body)
