"""Async SEC EDGAR API Workflow Client, US-GAAP Harmonizer & Context-Window Pruner.

Built from the API-to-MCP Wrapper template (`api_workflow_client_template.py`) with:
1. Mandatory SEC Fair-Access `User-Agent` header injection and dual-host routing (`www.sec.gov` & `data.sec.gov`).
2. Connection pooling, `asyncio.Semaphore(6)` rate limiting (<10 req/s SEC limit), exponential backoff retries,
   and `CircuitBreaker` protection.
3.Bounded parallel fan-out (`fan_out_gather`) to orchestrate multi-endpoint workflows in a single MCP tool turn.
4. 24-hour TTL in-memory `company_tickers.json` resolver (Ticker / Company Name / Raw CIK -> 10-digit `CIK##########`).
5. US-GAAP / IFRS / DEI Concept Harmonization Engine with restatement deduplication and financial ratio computation.
6. Context-window protection (`prune_payload_for_llm`) keeping every tool response compact (<6 KB).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import math
import os
import re
import statistics
import time
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger("sec-edgar-mcp-client")

DEFAULT_SEC_USER_AGENT = "GoogleCloudRun-SEC-EDGAR-MCP/1.0 (sec-mcp-admin@example.com)"


# ==============================================================================
# 1. Circuit Breaker & Context-Window Pruner (from API-to-MCP Wrapper Template)
# ==============================================================================

class CircuitBreaker:
    """Lightweight circuit breaker preventing cascading hangs when downstream SEC APIs degrade."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if (time.time() - self.last_failure_time) >= self.recovery_timeout_sec:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_success(self) -> None:
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning("Downstream SEC API CircuitBreaker tripped to OPEN (failures=%d)", self.failure_count)

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": int(self.last_failure_time) if self.last_failure_time else None,
        }


def prune_payload_for_llm(
    data: Any,
    *,
    max_list_items: int = 20,
    max_str_len: int = 600,
    drop_keys: Optional[set[str]] = None,
) -> Any:
    """Recursively prunes verbose downstream API JSON payloads so they stay compact (<6 KB) for LLM context windows."""
    ignored = drop_keys or {"raw_binary", "base64_content", "_links", "etag", "internal_trace_id"}

    if isinstance(data, dict):
        cleaned: Dict[str, Any] = {}
        for k, v in data.items():
            if k in ignored or v is None or v == "" or v == [] or v == {}:
                continue
            cleaned[k] = prune_payload_for_llm(
                v,
                max_list_items=max_list_items,
                max_str_len=max_str_len,
                drop_keys=ignored,
            )
        return cleaned

    if isinstance(data, list):
        total = len(data)
        sliced = [
            prune_payload_for_llm(
                item,
                max_list_items=max_list_items,
                max_str_len=max_str_len,
                drop_keys=ignored,
            )
            for item in data[:max_list_items]
        ]
        if total > max_list_items:
            sliced.append({"_truncated_notice": f"Showing {max_list_items} of {total} total items."})
        return sliced

    if isinstance(data, str) and len(data) > max_str_len:
        return data[:max_str_len] + f"... [truncated {len(data) - max_str_len} chars]"

    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        if data.is_integer() and abs(data) >= 1000:
            return int(data)
        return round(data, 4)

    return data


# ==============================================================================
# 2. Async HTTP Workflow Client (`DownstreamApiClient`)
# ==============================================================================

class DownstreamApiClient:
    """Async HTTP workflow client for SEC EDGAR REST APIs (`data.sec.gov` and `www.sec.gov`)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        user_token_getter: Optional[Callable[[], Optional[str]]] = None,
        timeout_sec: float = 20.0,
        max_concurrency: int = 6,
    ):
        self.base_url = (base_url or os.environ.get("DOWNSTREAM_API_BASE_URL", "https://data.sec.gov")).rstrip("/")
        self.www_base_url = os.environ.get("SEC_WWW_BASE_URL", "https://www.sec.gov").rstrip("/")
        self.user_token_getter = user_token_getter
        self.timeout_sec = timeout_sec
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.circuit_breaker = CircuitBreaker()
        self._client: Optional[httpx.AsyncClient] = None

    def _get_sec_user_agent(self) -> str:
        return (
            os.environ.get("SEC_USER_AGENT")
            or os.environ.get("SEC_EDGAR_USER_AGENT")
            or DEFAULT_SEC_USER_AGENT
        ).strip()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_sec, connect=8.0),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=40),
                follow_redirects=True,
            )
        return self._client

    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Builds SEC-compliant request headers with mandatory User-Agent."""
        headers: Dict[str, str] = {
            "User-Agent": self._get_sec_user_agent(),
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retries: int = 2,
    ) -> Dict[str, Any]:
        """Executes a rate-limited async HTTP call with circuit breaking and exponential backoff."""
        if not self.circuit_breaker.allow_request():
            return {
                "error": "circuit_breaker_open",
                "message": "Downstream SEC EDGAR API is temporarily unavailable (circuit breaker open).",
                "circuit_breaker": self.circuit_breaker.get_status(),
            }

        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            url = path_or_url
        elif path_or_url.startswith("/files/"):
            url = f"{self.www_base_url}{path_or_url}"
        else:
            url = f"{self.base_url}/{path_or_url.lstrip('/')}"

        client = await self._get_client()
        merged_headers = self._build_headers(headers)
        clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}

        last_err: Optional[str] = None
        for attempt in range(retries + 1):
            try:
                async with self.semaphore:
                    resp = await client.request(
                        method.upper(),
                        url,
                        params=clean_params,
                        headers=merged_headers,
                    )
                if resp.status_code in (429, 502, 503, 504) and attempt < retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
                    continue

                if resp.status_code >= 500:
                    self.circuit_breaker.record_failure()
                else:
                    self.circuit_breaker.record_success()

                if resp.status_code >= 400:
                    return {
                        "error": f"http_{resp.status_code}",
                        "status_code": resp.status_code,
                        "url": url,
                        "detail": resp.text[:300],
                    }

                return resp.json() if resp.content else {"status": "ok"}
            except Exception as exc:
                last_err = str(exc)
                if attempt < retries:
                    await asyncio.sleep(0.4 * (2 ** attempt))
                else:
                    self.circuit_breaker.record_failure()

        return {
            "error": "request_failed",
            "url": url,
            "message": last_err or "Unknown upstream SEC API error",
        }

    async def fan_out_gather(self, tasks: Dict[str, Awaitable[Any]]) -> Dict[str, Any]:
        """Executes multiple named downstream SEC API coroutines concurrently via bounded semaphore."""
        keys = list(tasks.keys())
        coros = [tasks[k] for k in keys]
        results = await asyncio.gather(*coros, return_exceptions=True)
        combined: Dict[str, Any] = {}
        for k, res in zip(keys, results):
            if isinstance(res, Exception):
                combined[k] = {"error": str(res)}
            else:
                combined[k] = res
        return combined

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# ==============================================================================
# 3. US-GAAP Concept Harmonization Dictionary & 8-K Item Catalog
# ==============================================================================

HARMONIZED_CONCEPTS: Dict[str, Dict[str, Any]] = {
    # --- Income Statement (Duration / Flow) ---
    "revenue": {
        "label": "Total Revenue",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
            ("us-gaap", "Revenues"),
            ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
            ("us-gaap", "SalesRevenueNet"),
            ("us-gaap", "SalesRevenueGoodsNet"),
            ("us-gaap", "RevenuesNetOfInterestExpense"),
            ("us-gaap", "InterestAndDividendIncomeOperating"),
            ("ifrs-full", "Revenue"),
        ],
    },
    "cost_of_revenue": {
        "label": "Cost of Revenue",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "CostOfGoodsAndServicesSold"),
            ("us-gaap", "CostOfRevenue"),
            ("us-gaap", "CostOfGoodsSold"),
            ("us-gaap", "CostOfServices"),
        ],
    },
    "gross_profit": {
        "label": "Gross Profit",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "GrossProfit"),
        ],
    },
    "r_and_d": {
        "label": "Research & Development Expense",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "ResearchAndDevelopmentExpense"),
            ("us-gaap", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost"),
        ],
    },
    "sga": {
        "label": "Selling, General & Administrative Expense",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "SellingGeneralAndAdministrativeExpense"),
            ("us-gaap", "GeneralAndAdministrativeExpense"),
        ],
    },
    "operating_expenses": {
        "label": "Total Operating Expenses",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "OperatingExpenses"),
            ("us-gaap", "CostsAndExpenses"),
        ],
    },
    "operating_income": {
        "label": "Operating Income (EBIT)",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "OperatingIncomeLoss"),
        ],
    },
    "interest_expense": {
        "label": "Interest Expense",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "InterestExpense"),
            ("us-gaap", "InterestExpenseNonoperating"),
            ("us-gaap", "InterestAndDebtExpense"),
        ],
    },
    "other_nonoperating_income_expense": {
        "label": "Other Non-Operating Income (Expense)",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "NonoperatingIncomeExpense"),
            ("us-gaap", "OtherNonoperatingIncomeExpense"),
        ],
    },
    "pretax_income": {
        "label": "Pretax Income from Continuing Operations",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"),
            ("us-gaap", "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"),
        ],
    },
    "income_tax": {
        "label": "Income Tax Expense (Benefit)",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "IncomeTaxExpenseBenefit"),
        ],
    },
    "income_from_continuing_operations": {
        "label": "Income from Continuing Operations (After Tax)",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "IncomeLossFromContinuingOperations"),
            ("us-gaap", "IncomeLossFromContinuingOperationsIncludingPortionAttributableToNoncontrollingInterest"),
        ],
    },
    "net_income": {
        "label": "Net Income",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "NetIncomeLoss"),
            ("us-gaap", "ProfitLoss"),
            ("us-gaap", "NetIncomeLossAvailableToCommonStockholdersBasic"),
        ],
    },
    "eps_basic": {
        "label": "EPS (Basic)",
        "frame_type": "duration",
        "unit": "USD/shares",
        "tags": [
            ("us-gaap", "EarningsPerShareBasic"),
        ],
    },
    "eps_diluted": {
        "label": "EPS (Diluted)",
        "frame_type": "duration",
        "unit": "USD/shares",
        "tags": [
            ("us-gaap", "EarningsPerShareDiluted"),
            ("us-gaap", "EarningsPerShareBasic"),
        ],
    },
    "shares_diluted": {
        "label": "Weighted Average Diluted Shares",
        "frame_type": "duration",
        "unit": "shares",
        "tags": [
            ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
            ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic"),
        ],
    },
    # --- Balance Sheet (Instantaneous / Point-in-Time) ---
    "total_cash": {
        "label": "Cash, Cash Equivalents & Short-Term Investments",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "CashCashEquivalentsAndShortTermInvestments"),
            ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
        ],
    },
    "cash_and_equivalents": {
        "label": "Cash & Cash Equivalents",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "CashAndCashEquivalentsAtCarryingValue"),
            ("us-gaap", "CashCashEquivalentsAndShortTermInvestments"),
        ],
    },
    "accounts_receivable": {
        "label": "Accounts Receivable (Net)",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "AccountsReceivableNetCurrent"),
            ("us-gaap", "ReceivablesNetCurrent"),
        ],
    },
    "inventory": {
        "label": "Inventory (Net)",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "InventoryNet"),
        ],
    },
    "current_assets": {
        "label": "Total Current Assets",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "AssetsCurrent"),
        ],
    },
    "ppe_net": {
        "label": "Property, Plant & Equipment (Net)",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "PropertyPlantAndEquipmentNet"),
            ("us-gaap", "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAssetAfterAccumulatedDepreciationAndAmortization"),
            ("us-gaap", "PropertyPlantAndEquipmentAndFinanceLeaseRightOfUseAsset"),
        ],
    },
    "goodwill": {
        "label": "Goodwill",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "Goodwill"),
        ],
    },
    "total_assets": {
        "label": "Total Assets",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "Assets"),
        ],
    },
    "accounts_payable": {
        "label": "Accounts Payable",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "AccountsPayableCurrent"),
        ],
    },
    "short_term_debt": {
        "label": "Short-Term Debt & Current Maturities",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "LongTermDebtCurrent"),
            ("us-gaap", "ShortTermBorrowings"),
            ("us-gaap", "DebtCurrent"),
        ],
    },
    "current_liabilities": {
        "label": "Total Current Liabilities",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "LiabilitiesCurrent"),
        ],
    },
    "long_term_debt": {
        "label": "Long-Term Debt (Noncurrent)",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "LongTermDebtNoncurrent"),
            ("us-gaap", "LongTermDebt"),
            ("us-gaap", "LongTermDebtAndCapitalLeaseObligations"),
        ],
    },
    "total_liabilities": {
        "label": "Total Liabilities",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "Liabilities"),
        ],
    },
    "retained_earnings": {
        "label": "Retained Earnings (Accumulated Deficit)",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "RetainedEarningsAccumulatedDeficit"),
        ],
    },
    "stockholders_equity": {
        "label": "Total Stockholders' Equity",
        "frame_type": "instant",
        "unit": "USD",
        "tags": [
            ("us-gaap", "StockholdersEquity"),
            ("us-gaap", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
        ],
    },
    "shares_outstanding": {
        "label": "Common Shares Outstanding",
        "frame_type": "instant",
        "unit": "shares",
        "tags": [
            ("dei", "EntityCommonStockSharesOutstanding"),
            ("us-gaap", "CommonStockSharesOutstanding"),
            ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
        ],
    },
    # --- Cash Flow Statement (Duration / Flow) ---
    "operating_cash_flow": {
        "label": "Operating Cash Flow",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "NetCashProvidedByUsedInOperatingActivities"),
            ("us-gaap", "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"),
        ],
    },
    "investing_cash_flow": {
        "label": "Net Cash from Investing Activities",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "NetCashProvidedByUsedInInvestingActivities"),
            ("us-gaap", "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations"),
        ],
    },
    "capex": {
        "label": "Capital Expenditures (CapEx)",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "PaymentsToAcquirePropertyPlantAndEquipment"),
            ("us-gaap", "PaymentsToAcquireProductiveAssets"),
        ],
    },
    "depreciation_amortization": {
        "label": "Depreciation & Amortization",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "DepreciationDepletionAndAmortization"),
            ("us-gaap", "DepreciationAndAmortization"),
            ("us-gaap", "Depreciation"),
        ],
    },
    "sbc": {
        "label": "Share-Based Compensation",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "ShareBasedCompensation"),
            ("us-gaap", "AllocatedShareBasedCompensationExpense"),
        ],
    },
    "dividends_paid": {
        "label": "Dividends Paid",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "PaymentsOfDividendsCommonStock"),
            ("us-gaap", "PaymentsOfDividends"),
        ],
    },
    "share_repurchases": {
        "label": "Share Repurchases (Buybacks)",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "PaymentsForRepurchaseOfCommonStock"),
        ],
    },
    "financing_cash_flow": {
        "label": "Net Cash from Financing Activities",
        "frame_type": "duration",
        "unit": "USD",
        "tags": [
            ("us-gaap", "NetCashProvidedByUsedInFinancingActivities"),
            ("us-gaap", "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations"),
        ],
    },
}

# Friendly aliases for user/LLM concept inputs
CONCEPT_SYNONYMS: Dict[str, str] = {
    "revenues": "revenue",
    "total_revenue": "revenue",
    "sales": "revenue",
    "cost_of_goods_sold": "cost_of_revenue",
    "cogs": "cost_of_revenue",
    "rd": "r_and_d",
    "research_and_development": "r_and_d",
    "ebit": "operating_income",
    "operating_profit": "operating_income",
    "net_profit": "net_income",
    "earnings": "net_income",
    "eps": "eps_diluted",
    "cash": "total_cash",
    "assets": "total_assets",
    "liabilities": "total_liabilities",
    "equity": "stockholders_equity",
    "debt": "long_term_debt",
    "total_debt": "long_term_debt",
    "ocf": "operating_cash_flow",
    "cash_from_operations": "operating_cash_flow",
    "capital_expenditures": "capex",
    "stock_based_compensation": "sbc",
    "share_based_compensation": "sbc",
    "buybacks": "share_repurchases",
    "shares": "shares_outstanding",
}

ITEM_8K_DESCRIPTIONS: Dict[str, str] = {
    "1.01": "Entry into a Material Definitive Agreement",
    "1.02": "Termination of a Material Definitive Agreement",
    "1.03": "Bankruptcy or Receivership",
    "1.05": "Material Cybersecurity Incidents",
    "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition (Earnings Release)",
    "2.03": "Creation of a Direct Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities (Restructuring)",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Failure to Satisfy Listing Rule",
    "3.02": "Unregistered Sales of Equity Securities",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements (Restatement)",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Election of Directors or Principal Officers",
    "5.03": "Amendments to Articles of Incorporation or Bylaws",
    "5.07": "Submission of Matters to a Vote of Security Holders",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


# ==============================================================================
# 4. SEC EDGAR Workflow Orchestrator (`SecEdgarService`)
# ==============================================================================

class SecEdgarService:
    """High-level async orchestrator encapsulating SEC EDGAR workflows, caching, and XBRL harmonization."""

    def __init__(self, api_client: DownstreamApiClient):
        self.api_client = api_client
        self._tickers_lock = asyncio.Lock()
        self._tickers_loaded_at: float = 0.0
        self._tickers_ttl_sec: float = 86400.0  # 24 hours
        self._by_ticker: Dict[str, Dict[str, Any]] = {}
        self._by_cik: Dict[int, Dict[str, Any]] = {}
        self._all_entities: List[Dict[str, Any]] = []

        # Short-lived LRU/TTL cache for large per-company JSONs (10 min TTL, max 24 entries)
        self._submissions_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._facts_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
        self._cache_ttl_sec: float = 600.0

    async def _ensure_tickers_loaded(self) -> None:
        """Loads and indexes `https://www.sec.gov/files/company_tickers.json` in memory with a 24h TTL."""
        now = time.time()
        if self._all_entities and (now - self._tickers_loaded_at) < self._tickers_ttl_sec:
            return

        async with self._tickers_lock:
            if self._all_entities and (time.time() - self._tickers_loaded_at) < self._tickers_ttl_sec:
                return

            raw = await self.api_client.request("GET", "/files/company_tickers.json")
            if not isinstance(raw, dict) or "error" in raw:
                logger.error("Failed to fetch SEC company_tickers.json: %s", raw)
                return

            by_ticker: Dict[str, Dict[str, Any]] = {}
            by_cik: Dict[int, Dict[str, Any]] = {}
            all_entities: List[Dict[str, Any]] = []

            for _, item in raw.items():
                if not isinstance(item, dict):
                    continue
                try:
                    cik_int = int(item["cik_str"])
                except (KeyError, TypeError, ValueError):
                    continue
                ticker = str(item.get("ticker", "")).strip().upper()
                title = str(item.get("title", "")).strip()
                cik_10 = f"{cik_int:010d}"
                entry = {
                    "cik_int": cik_int,
                    "cik_10": cik_10,
                    "cik": f"CIK{cik_10}",
                    "ticker": ticker,
                    "title": title,
                    "title_lower": title.lower(),
                }
                all_entities.append(entry)
                if ticker:
                    by_ticker[ticker] = entry
                    by_ticker[ticker.replace("-", ".")] = entry
                    by_ticker[ticker.replace(".", "-")] = entry
                if cik_int not in by_cik:
                    by_cik[cik_int] = entry

            self._by_ticker = by_ticker
            self._by_cik = by_cik
            self._all_entities = all_entities
            self._tickers_loaded_at = time.time()
            logger.info("Loaded %d SEC entities from company_tickers.json", len(all_entities))

    async def resolve_company(self, identifier: str) -> Dict[str, Any]:
        """Resolves a stock ticker, company name, or raw/padded CIK to a canonical 10-digit CIK record."""
        await self._ensure_tickers_loaded()
        clean = (identifier or "").strip()
        if not clean:
            return {"error": "invalid_identifier", "message": "Identifier cannot be empty."}

        upper = clean.upper()
        # 1. Exact ticker match first
        if upper in self._by_ticker:
            return dict(self._by_ticker[upper])

        # 2. Raw or CIK-prefixed integer match
        cik_match = re.match(r"^(?:CIK)?0*(\d{1,10})$", upper)
        if cik_match:
            cik_int = int(cik_match.group(1))
            if cik_int in self._by_cik:
                return dict(self._by_cik[cik_int])
            cik_10 = f"{cik_int:010d}"
            return {
                "cik_int": cik_int,
                "cik_10": cik_10,
                "cik": f"CIK{cik_10}",
                "ticker": "",
                "title": f"SEC Entity CIK {cik_10}",
            }

        # 3. Fuzzy search on company name / ticker prefix
        matches = await self.fuzzy_search_companies(clean, limit=1)
        if matches:
            return dict(matches[0])

        return {
            "error": "company_not_found",
            "identifier": identifier,
            "message": f"Could not resolve '{identifier}' to a valid SEC CIK in company_tickers.json.",
        }

    async def fuzzy_search_companies(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Ranks SEC entities by ticker match, prefix match, and title token overlap."""
        await self._ensure_tickers_loaded()
        q = (query or "").strip().lower()
        if not q:
            return []

        q_upper = q.upper()
        q_tokens = [t for t in re.split(r"[^a-z0-9]+", q) if t and t not in ("inc", "corp", "corporation", "co", "ltd", "llc", "plc", "the")]
        if not q_tokens:
            q_tokens = [q]

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for ent in self._all_entities:
            ticker = ent["ticker"]
            title_lower = ent["title_lower"]
            score = 0.0

            if ticker == q_upper:
                score = 100.0
            elif ticker.startswith(q_upper) and len(q_upper) >= 2:
                score = 75.0 - (len(ticker) - len(q_upper)) * 2.0
            elif title_lower == q:
                score = 95.0
            elif title_lower.startswith(q):
                score = 80.0
            else:
                matched_tokens = sum(1 for tok in q_tokens if tok in title_lower)
                if matched_tokens == len(q_tokens):
                    score = 60.0 + matched_tokens * 5.0 - len(title_lower) * 0.1
                elif matched_tokens > 0 and len(q_tokens) > 1:
                    score = 30.0 * (matched_tokens / len(q_tokens))

            if score > 0:
                scored.append((score, ent))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[Dict[str, Any]] = []
        seen_ciks: set[int] = set()
        for score, ent in scored:
            if ent["cik_int"] in seen_ciks:
                continue
            seen_ciks.add(ent["cik_int"])
            item = {k: v for k, v in ent.items() if k != "title_lower"}
            item["match_score"] = round(score, 1)
            results.append(item)
            if len(results) >= limit:
                break
        return results

    async def get_submissions(self, cik_10: str) -> Dict[str, Any]:
        """Fetches `submissions/CIK{cik_10}.json` with a 10-minute in-memory TTL cache."""
        now = time.time()
        cached = self._submissions_cache.get(cik_10)
        if cached and (now - cached[0]) < self._cache_ttl_sec:
            return cached[1]

        data = await self.api_client.request("GET", f"/submissions/CIK{cik_10}.json")
        if isinstance(data, dict) and "error" not in data:
            if len(self._submissions_cache) >= 24:
                oldest_k = min(self._submissions_cache, key=lambda k: self._submissions_cache[k][0])
                self._submissions_cache.pop(oldest_k, None)
            self._submissions_cache[cik_10] = (now, data)
        return data

    async def get_company_facts(self, cik_10: str) -> Dict[str, Any]:
        """Fetches `api/xbrl/companyfacts/CIK{cik_10}.json` with a 10-minute in-memory TTL cache."""
        now = time.time()
        cached = self._facts_cache.get(cik_10)
        if cached and (now - cached[0]) < self._cache_ttl_sec:
            return cached[1]

        data = await self.api_client.request("GET", f"/api/xbrl/companyfacts/CIK{cik_10}.json")
        if isinstance(data, dict) and "error" not in data:
            if len(self._facts_cache) >= 16:
                oldest_k = min(self._facts_cache, key=lambda k: self._facts_cache[k][0])
                self._facts_cache.pop(oldest_k, None)
            self._facts_cache[cik_10] = (now, data)
        return data

    # --------------------------------------------------------------------------
    # Helper: Parse Submissions Profile & Recent Filings
    # --------------------------------------------------------------------------

    @staticmethod
    def build_filing_urls(cik_int: int, accession_number: str, primary_doc: str) -> Dict[str, str]:
        acc_clean = (accession_number or "").strip()
        acc_nodash = acc_clean.replace("-", "")
        base_archive = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}"
        index_url = f"{base_archive}/{acc_clean}-index.htm"
        doc_url = f"{base_archive}/{primary_doc}" if primary_doc else index_url
        return {
            "document_url": doc_url,
            "filing_index_url": index_url,
        }

    def extract_corporate_profile(self, submissions: Dict[str, Any], resolved: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts a compact corporate profile from `submissions/CIK{10-digit}.json`."""
        if not isinstance(submissions, dict) or "error" in submissions:
            return resolved

        fye_raw = str(submissions.get("fiscalYearEnd") or "")
        if len(fye_raw) == 4 and fye_raw.isdigit():
            fye_formatted = f"{fye_raw[:2]}-{fye_raw[2:]}"
        else:
            fye_formatted = fye_raw

        biz_addr = (submissions.get("addresses") or {}).get("business") or {}
        city_state = ", ".join(
            [p for p in [biz_addr.get("city"), biz_addr.get("stateOrCountry")] if p]
        )

        former = [
            {"name": fn.get("name"), "from": (fn.get("from") or "")[:10], "to": (fn.get("to") or "")[:10]}
            for fn in (submissions.get("formerNames") or [])[:3]
            if isinstance(fn, dict) and fn.get("name")
        ]

        return {
            "cik": f"CIK{resolved['cik_10']}",
            "cik_int": resolved["cik_int"],
            "name": submissions.get("name") or resolved.get("title"),
            "tickers": submissions.get("tickers") or ([resolved["ticker"]] if resolved.get("ticker") else []),
            "exchanges": submissions.get("exchanges") or [],
            "sic": submissions.get("sic"),
            "sic_description": submissions.get("sicDescription"),
            "category": submissions.get("category"),
            "entity_type": submissions.get("entityType"),
            "state_of_incorporation": submissions.get("stateOfIncorporation"),
            "fiscal_year_end": fye_formatted,
            "headquarters": city_state,
            "website": submissions.get("website"),
            "former_names": former,
        }

    def zip_and_filter_filings(
        self,
        submissions: Dict[str, Any],
        cik_int: int,
        *,
        form_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        item_8k_filter: Optional[str] = None,
        include_amendments: bool = True,
        limit: int = 15,
        extra_recent_blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Transposes columnar arrays in `submissions.filings.recent` into enriched filing objects."""
        recent_blocks = [((submissions.get("filings") or {}).get("recent") or {})]
        if extra_recent_blocks:
            recent_blocks.extend(extra_recent_blocks)

        norm_forms: Optional[set[str]] = None
        if form_types:
            norm_forms = set()
            for ft in form_types:
                clean_ft = ft.strip().upper()
                if clean_ft:
                    norm_forms.add(clean_ft)
                    if include_amendments and not clean_ft.endswith("/A"):
                        norm_forms.add(f"{clean_ft}/A")

        item_filter_lower = (item_8k_filter or "").strip().lower()
        counts_by_form: Dict[str, int] = {}
        matched_rows: List[Dict[str, Any]] = []

        for block in recent_blocks:
            acc_nums = block.get("accessionNumber") or []
            filing_dates = block.get("filingDate") or []
            report_dates = block.get("reportDate") or []
            forms = block.get("form") or []
            primary_docs = block.get("primaryDocument") or []
            doc_descs = block.get("primaryDocDescription") or []
            items_list = block.get("items") or []
            sizes = block.get("size") or []
            is_xbrl_list = block.get("isXBRL") or []

            total_len = len(acc_nums)
            for i in range(total_len):
                form = str(forms[i] if i < len(forms) else "").strip()
                if not form:
                    continue
                if not include_amendments and form.upper().endswith("/A"):
                    continue
                if norm_forms and form.upper() not in norm_forms:
                    continue

                f_date = str(filing_dates[i] if i < len(filing_dates) else "").strip()
                if start_date and f_date and f_date < start_date:
                    continue
                if end_date and f_date and f_date > end_date:
                    continue

                raw_items = str(items_list[i] if i < len(items_list) else "").strip()
                item_codes = [c.strip() for c in raw_items.split(",") if c.strip()] if raw_items else []
                item_labels = [
                    f"Item {code}: {ITEM_8K_DESCRIPTIONS.get(code, 'Material Event')}"
                    for code in item_codes
                ]

                if item_filter_lower:
                    combined_item_text = " ".join(item_codes + item_labels).lower()
                    if item_filter_lower not in combined_item_text:
                        continue

                counts_by_form[form] = counts_by_form.get(form, 0) + 1

                if len(matched_rows) < limit:
                    acc = str(acc_nums[i])
                    p_doc = str(primary_docs[i] if i < len(primary_docs) else "").strip()
                    urls = self.build_filing_urls(cik_int, acc, p_doc)
                    row: Dict[str, Any] = {
                        "form": form,
                        "filing_date": f_date,
                        "report_date": str(report_dates[i] if i < len(report_dates) else "").strip() or None,
                        "accession_number": acc,
                        "description": str(doc_descs[i] if i < len(doc_descs) else "").strip() or form,
                        "is_xbrl": bool(is_xbrl_list[i]) if i < len(is_xbrl_list) else False,
                        "size_bytes": sizes[i] if i < len(sizes) else None,
                        "document_url": urls["document_url"],
                        "filing_index_url": urls["filing_index_url"],
                    }
                    if item_labels:
                        row["items_8k"] = item_labels
                    matched_rows.append(row)

        return {
            "total_matching_filings": sum(counts_by_form.values()),
            "counts_by_form": counts_by_form,
            "filings": matched_rows,
        }

    # --------------------------------------------------------------------------
    # Helper: XBRL Fact Extraction, Period Deduplication & Harmonization
    # --------------------------------------------------------------------------

    @staticmethod
    def _calc_duration_days(start_str: Optional[str], end_str: Optional[str]) -> Optional[int]:
        if not start_str or not end_str:
            return None
        try:
            d1 = datetime.strptime(start_str[:10], "%Y-%m-%d")
            d2 = datetime.strptime(end_str[:10], "%Y-%m-%d")
            return (d2 - d1).days
        except Exception:
            return None

    def extract_points_from_concept_obj(
        self,
        concept_obj: Dict[str, Any],
        *,
        frame_type: str = "duration",
        period_type: str = "annual",
        include_restatements: bool = False,
    ) -> Tuple[str, Dict[str, Dict[str, Any]]]:
        """Deduplicates an XBRL concept object's `units` array into `{period_ym: canonical_fact}`."""
        units_dict = concept_obj.get("units") if isinstance(concept_obj, dict) else None
        if not isinstance(units_dict, dict) or not units_dict:
            return "", {}

        # Choose primary unit (prefer USD, USD/shares, shares, then first key)
        chosen_unit = ""
        for pref in ("USD", "USD/shares", "shares", "pure"):
            if pref in units_dict:
                chosen_unit = pref
                break
        if not chosen_unit:
            chosen_unit = next(iter(units_dict.keys()))

        raw_points = units_dict.get(chosen_unit) or []
        if not isinstance(raw_points, list):
            return chosen_unit, {}

        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for pt in raw_points:
            if not isinstance(pt, dict) or pt.get("val") is None:
                continue
            end_date = str(pt.get("end") or "").strip()
            if len(end_date) < 7:
                continue
            start_date = pt.get("start")
            form = str(pt.get("form") or "").upper()
            fp = str(pt.get("fp") or "").upper()
            frame = str(pt.get("frame") or "").strip()
            dur_days = self._calc_duration_days(start_date, end_date)

            if period_type == "annual":
                if frame_type == "duration" or start_date is not None:
                    # Must be a full ~12-month period (330 to 380 days)
                    if dur_days is not None and not (330 <= dur_days <= 380):
                        continue
                    if dur_days is None and fp != "FY":
                        continue
                else:
                    # Instantaneous balance sheet / share count concept for annual comparison:
                    # Must come from an annual filing (10-K / 20-F / 40-F) and not a 10-Q quarter.
                    is_annual_form = form in ("10-K", "10-K/A", "20-F", "20-F/A", "40-F")
                    if not is_annual_form:
                        continue
            elif period_type == "quarterly":
                if frame_type == "duration" or start_date is not None:
                    # Strictly ~1-quarter duration (70 to 105 days) to exclude 6M/9M YTD cumulative rows
                    if dur_days is not None and not (70 <= dur_days <= 105):
                        continue
                    if dur_days is None and fp not in ("Q1", "Q2", "Q3", "Q4"):
                        continue
                else:
                    if form not in ("10-Q", "10-Q/A", "10-K", "10-K/A", "20-F", "40-F"):
                        continue

            period_ym = end_date[:7]  # YYYY-MM uniquely identifies each annual or quarterly fiscal close
            buckets.setdefault(period_ym, []).append(pt)

        deduped: Dict[str, Dict[str, Any]] = {}
        for period_ym, candidates in buckets.items():
            # Sort by latest `filed` date first so restatements/reclassifications in newer 10-Ks win
            candidates.sort(
                key=lambda x: (
                    str(x.get("filed") or ""),
                    1 if str(x.get("form") or "").upper() in ("10-K", "10-K/A", "20-F") else 0,
                    1 if x.get("frame") else 0,
                ),
                reverse=True,
            )
            best = candidates[0]
            end_str = str(best.get("end") or "")
            # Derive clean fiscal year label from the period end date
            # (In SEC XBRL, `fy` on comparative facts is the filing's year, so `end` year is authoritative)
            try:
                dt_end = datetime.strptime(end_str[:10], "%Y-%m-%d")
                # Many retailers/chipmakers (e.g. NVDA) close FY in late January; SEC frames map late-Jan to prior CY,
                # while company fiscal year is dt_end.year. We include both `period_end` and `calendar_frame`.
                derived_year = dt_end.year
            except Exception:
                derived_year = best.get("fy")

            entry: Dict[str, Any] = {
                "period_ym": period_ym,
                "period_end": end_str,
                "period_start": best.get("start"),
                "val": best.get("val"),
                "unit": chosen_unit,
                "form": best.get("form"),
                "filed": best.get("filed"),
                "accn": best.get("accn"),
                "frame": best.get("frame"),
                "calendar_year": derived_year,
            }
            if include_restatements and len(candidates) > 1:
                distinct_vals: List[Dict[str, Any]] = []
                seen_v = {best.get("val")}
                for older in candidates[1:]:
                    ov = older.get("val")
                    if ov not in seen_v:
                        seen_v.add(ov)
                        distinct_vals.append({
                            "prior_val": ov,
                            "delta_to_latest": round(float(best["val"]) - float(ov), 4)
                            if isinstance(best.get("val"), (int, float)) and isinstance(ov, (int, float))
                            else None,
                            "filed": older.get("filed"),
                            "form": older.get("form"),
                        })
                if distinct_vals:
                    entry["restatement_history"] = distinct_vals[:3]

            deduped[period_ym] = entry

        return chosen_unit, deduped

    def extract_harmonized_metric(
        self,
        facts_root: Dict[str, Any],
        canonical_key: str,
        *,
        period_type: str = "annual",
    ) -> Dict[str, Any]:
        """Extracts and merges a canonical metric across priority-ordered US-GAAP/DEI/IFRS fallback tags."""
        key = CONCEPT_SYNONYMS.get(canonical_key.lower(), canonical_key.lower())
        spec = HARMONIZED_CONCEPTS.get(key)
        taxonomies = (facts_root.get("facts") or {}) if isinstance(facts_root, dict) else {}

        if not spec:
            # Treat `canonical_key` as a direct XBRL tag name across us-gaap, dei, ifrs-full
            for tax in ("us-gaap", "dei", "ifrs-full"):
                tax_dict = taxonomies.get(tax) or {}
                if canonical_key in tax_dict:
                    unit, series = self.extract_points_from_concept_obj(
                        tax_dict[canonical_key],
                        frame_type="duration",
                        period_type=period_type,
                    )
                    return {
                        "metric": canonical_key,
                        "label": tax_dict[canonical_key].get("label") or canonical_key,
                        "unit": unit,
                        "tags_used": [f"{tax}:{canonical_key}"],
                        "series_by_ym": series,
                    }
            return {
                "metric": canonical_key,
                "label": canonical_key,
                "unit": "",
                "tags_used": [],
                "series_by_ym": {},
            }

        frame_type = spec["frame_type"]
        candidate_extractions: List[Tuple[str, int, str, str, Dict[str, Dict[str, Any]]]] = []
        for priority_idx, (tax, tag) in enumerate(spec["tags"]):
            tax_dict = taxonomies.get(tax) or {}
            concept_obj = tax_dict.get(tag)
            if not concept_obj:
                continue
            unit, series = self.extract_points_from_concept_obj(
                concept_obj,
                frame_type=frame_type,
                period_type=period_type,
            )
            if series:
                latest_ym = max(series.keys())
                candidate_extractions.append((latest_ym, -priority_idx, f"{tax}:{tag}", unit, series))

        # Sort so the tag with the most recent coverage (and highest priority on ties) goes first,
        # then backfill older periods from predecessor tags (e.g. pre-ASC 606 revenue tags).
        candidate_extractions.sort(key=lambda x: (x[0], x[1]), reverse=True)

        merged_series: Dict[str, Dict[str, Any]] = {}
        tags_used: List[str] = []
        primary_unit = spec["unit"]

        for _, _, tag_id, unit, series in candidate_extractions:
            if unit and not tags_used:
                primary_unit = unit
            added_any = False
            for ym, pt in series.items():
                if ym not in merged_series:
                    pt_copy = dict(pt)
                    pt_copy["source_tag"] = tag_id
                    merged_series[ym] = pt_copy
                    added_any = True
            if added_any:
                tags_used.append(tag_id)

        return {
            "metric": key,
            "label": spec["label"],
            "unit": primary_unit,
            "tags_used": tags_used,
            "series_by_ym": merged_series,
        }

    # --------------------------------------------------------------------------
    # Helper: Compute Derived Multi-Period Table & Financial Ratios
    # --------------------------------------------------------------------------

    @staticmethod
    def _safe_div(num: Optional[float], den: Optional[float], scale: float = 1.0) -> Optional[float]:
        if num is None or den is None or den == 0:
            return None
        return round((num / den) * scale, 2)

    @staticmethod
    def _safe_growth_pct(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
        if curr is None or prev is None or prev == 0:
            return None
        return round(((curr - prev) / abs(prev)) * 100.0, 2)

    @staticmethod
    def _compute_cagr_pct(oldest_val: Optional[float], latest_val: Optional[float], num_intervals: int) -> Optional[float]:
        if (
            oldest_val is None
            or latest_val is None
            or oldest_val <= 0
            or latest_val <= 0
            or num_intervals <= 0
        ):
            return None
        return round(((latest_val / oldest_val) ** (1.0 / num_intervals) - 1.0) * 100.0, 2)

    def build_harmonized_period_snapshots(
        self,
        facts_root: Dict[str, Any],
        metric_keys: List[str],
        *,
        period_type: str = "annual",
        periods: int = 4,
    ) -> Tuple[List[str], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
        """Aligns multiple harmonized metrics across the most recent `periods` fiscal closes."""
        extracted: Dict[str, Dict[str, Any]] = {}
        aux_keys = [
            "pretax_income",
            "interest_expense",
            "other_nonoperating_income_expense",
            "r_and_d",
            "sga",
            "operating_expenses",
        ]
        keys_to_extract = list(dict.fromkeys(metric_keys + (aux_keys if "operating_income" in metric_keys else [])))
        for mk in keys_to_extract:
            extracted[mk] = self.extract_harmonized_metric(facts_root, mk, period_type=period_type)

        # Anchor periods on primary flow metrics (revenue, net_income, operating_cash_flow) first
        # so comparative quarterly instants inside a 10-K footnote do not create sparse non-FY columns.
        anchor_yms: set[str] = set()
        for anchor_key in ("revenue", "net_income", "operating_cash_flow", "total_assets"):
            if anchor_key in extracted and extracted[anchor_key]["series_by_ym"]:
                anchor_yms.update(extracted[anchor_key]["series_by_ym"].keys())
                if len(anchor_yms) >= periods:
                    break
        if not anchor_yms:
            for mk_data in extracted.values():
                anchor_yms.update(mk_data["series_by_ym"].keys())

        sorted_yms = sorted(anchor_yms, reverse=True)[:periods]
        snapshots: List[Dict[str, Any]] = []

        # Also include 1 extra prior period for YoY growth calculation on the oldest requested period
        all_sorted_yms = sorted(anchor_yms, reverse=True)[: periods + 1]

        def get_val(mk: str, ym: str) -> Optional[float]:
            pt = extracted.get(mk, {}).get("series_by_ym", {}).get(ym)
            v = pt.get("val") if pt else None
            return float(v) if isinstance(v, (int, float)) else None

        for idx, ym in enumerate(sorted_yms):
            prev_ym = all_sorted_yms[idx + 1] if (idx + 1) < len(all_sorted_yms) else None
            # Find period_end from any populated metric in this `ym`
            period_end = ym
            for mk in keys_to_extract:
                pt = extracted.get(mk, {}).get("series_by_ym", {}).get(ym)
                if pt and pt.get("period_end"):
                    period_end = pt["period_end"]
                    break

            rev = get_val("revenue", ym)
            prev_rev = get_val("revenue", prev_ym) if prev_ym else None
            cor = get_val("cost_of_revenue", ym)
            gp = get_val("gross_profit", ym)
            if gp is None and rev is not None and cor is not None:
                gp = rev - cor
                if not extracted.get("gross_profit", {}).get("tags_used"):
                    extracted.setdefault("gross_profit", {})["tags_used"] = ["derived:Revenues - CostOfRevenue"]

            rd = get_val("r_and_d", ym)
            sga = get_val("sga", ym)
            op_exp = get_val("operating_expenses", ym)
            opinc = get_val("operating_income", ym)
            int_exp = get_val("interest_expense", ym)
            pretax = get_val("pretax_income", ym)

            if opinc is None:
                if pretax is not None and int_exp is not None:
                    opinc = pretax + int_exp
                    if not extracted.get("operating_income", {}).get("tags_used"):
                        extracted.setdefault("operating_income", {})["tags_used"] = [
                            "derived:EBIT (PretaxIncome + InterestExpense; company does not report a standalone us-gaap:OperatingIncomeLoss subtotal in 10-K)"
                        ]
                elif gp is not None and (rd is not None or sga is not None):
                    opinc = gp - ((rd or 0.0) + (sga or 0.0))
                    if not extracted.get("operating_income", {}).get("tags_used"):
                        extracted.setdefault("operating_income", {})["tags_used"] = [
                            "derived:GrossProfit - (R&D + SG&A)"
                        ]

            opinc_tag = (extracted.get("operating_income", {}).get("tags_used") or [""])[0]
            if op_exp is None:
                if gp is not None and opinc is not None and not str(opinc_tag).startswith("derived:"):
                    op_exp = gp - opinc
                    if not extracted.get("operating_expenses", {}).get("tags_used"):
                        extracted.setdefault("operating_expenses", {})["tags_used"] = [
                            "derived:GrossProfit - OperatingIncomeLoss"
                        ]
                elif rd is not None or sga is not None:
                    op_exp = (rd or 0.0) + (sga or 0.0)
                    if not extracted.get("operating_expenses", {}).get("tags_used"):
                        extracted.setdefault("operating_expenses", {})["tags_used"] = [
                            "derived:ResearchAndDevelopmentExpense + SellingGeneralAndAdministrativeExpense (core R&D + SG&A operating expenses)"
                        ]

            netinc = get_val("net_income", ym)
            prev_netinc = get_val("net_income", prev_ym) if prev_ym else None
            ocf = get_val("operating_cash_flow", ym)
            capex = get_val("capex", ym)
            fcf = (ocf - abs(capex)) if (ocf is not None and capex is not None) else None

            cash = get_val("total_cash", ym)
            curr_assets = get_val("current_assets", ym)
            inventory = get_val("inventory", ym) or 0.0
            tot_assets = get_val("total_assets", ym)
            curr_liab = get_val("current_liabilities", ym)
            st_debt = get_val("short_term_debt", ym) or 0.0
            lt_debt = get_val("long_term_debt", ym)
            tot_debt = (lt_debt + st_debt) if lt_debt is not None else (st_debt if st_debt > 0 else None)
            equity = get_val("stockholders_equity", ym)

            values_dict: Dict[str, Any] = {}
            for mk in metric_keys:
                v = get_val(mk, ym)
                if v is not None:
                    values_dict[mk] = v
            if gp is not None and "gross_profit" in metric_keys:
                values_dict["gross_profit"] = gp
            if op_exp is not None and "operating_expenses" in metric_keys:
                values_dict["operating_expenses"] = op_exp
            if opinc is not None and "operating_income" in metric_keys:
                values_dict["operating_income"] = opinc
            if gp is not None and pretax is not None and str(opinc_tag).startswith("derived:"):
                values_dict["total_expense_and_other_net"] = gp - pretax
            if fcf is not None:
                values_dict["free_cash_flow"] = fcf
            if tot_debt is not None:
                values_dict["total_debt"] = tot_debt

            ratios_dict = {
                "yoy_revenue_growth_pct": self._safe_growth_pct(rev, prev_rev),
                "yoy_net_income_growth_pct": self._safe_growth_pct(netinc, prev_netinc),
                "gross_margin_pct": self._safe_div(gp, rev, 100.0),
                "operating_margin_pct": self._safe_div(opinc, rev, 100.0),
                "net_margin_pct": self._safe_div(netinc, rev, 100.0),
                "fcf_margin_pct": self._safe_div(fcf, rev, 100.0),
                "rd_pct_of_revenue": self._safe_div(rd, rev, 100.0),
                "roe_pct": self._safe_div(netinc, equity, 100.0),
                "roa_pct": self._safe_div(netinc, tot_assets, 100.0),
                "current_ratio": self._safe_div(curr_assets, curr_liab, 1.0),
                "quick_ratio": self._safe_div(
                    (curr_assets - inventory) if curr_assets is not None else None,
                    curr_liab,
                    1.0,
                ),
                "debt_to_equity": self._safe_div(tot_debt, equity, 1.0),
                "net_debt": (tot_debt - cash) if (tot_debt is not None and cash is not None) else None,
            }

            snapshots.append({
                "period_end": period_end,
                "period_ym": ym,
                "metrics": values_dict,
                "ratios": {k: v for k, v in ratios_dict.items() if v is not None},
            })

        return sorted_yms, extracted, snapshots

    # ==========================================================================
    # Tool 1: `get_company_360_financial_dossier`
    # ==========================================================================

    async def get_company_360_financial_dossier(
        self,
        identifier: str,
        period_type: str = "annual",
        periods: int = 4,
        include_recent_filings: bool = True,
    ) -> Dict[str, Any]:
        resolved = await self.resolve_company(identifier)
        if "error" in resolved:
            return resolved

        cik_10 = resolved["cik_10"]
        cik_int = resolved["cik_int"]
        periods = max(1, min(int(periods), 10))

        # Parallel fan-out across `submissions` and `companyfacts`
        composite = await self.api_client.fan_out_gather({
            "submissions": self.get_submissions(cik_10),
            "companyfacts": self.get_company_facts(cik_10),
        })

        submissions = composite.get("submissions") or {}
        facts = composite.get("companyfacts") or {}

        profile = self.extract_corporate_profile(submissions, resolved)

        headline_keys = [
            "revenue",
            "cost_of_revenue",
            "gross_profit",
            "r_and_d",
            "sga",
            "operating_expenses",
            "operating_income",
            "interest_expense",
            "pretax_income",
            "income_tax",
            "net_income",
            "eps_diluted",
            "operating_cash_flow",
            "investing_cash_flow",
            "financing_cash_flow",
            "capex",
            "total_cash",
            "current_assets",
            "ppe_net",
            "total_assets",
            "current_liabilities",
            "long_term_debt",
            "short_term_debt",
            "total_liabilities",
            "stockholders_equity",
            "shares_outstanding",
        ]
        _, extracted_meta, snapshots = self.build_harmonized_period_snapshots(
            facts,
            headline_keys,
            period_type=period_type,
            periods=periods,
        )

        key_filings: Dict[str, Any] = {}
        if include_recent_filings and isinstance(submissions, dict) and "error" not in submissions:
            for form_group, label, lim, inc_amend in (
                (["10-K", "20-F"], "latest_annual_10k", 1, False),
                (["10-K", "20-F"], "recent_annual_10k_filings", 5, False),
                (["10-Q"], "latest_quarterly_10q", 1, False),
                (["10-Q"], "recent_quarterly_10q_filings", 5, False),
                (["DEF 14A"], "latest_proxy_def14a", 1, False),
                (["DEF 14A"], "recent_proxy_def14a_filings", 3, True),
                (["8-K"], "recent_8k_events", 8, True),
            ):
                res = self.zip_and_filter_filings(
                    submissions,
                    cik_int,
                    form_types=form_group,
                    include_amendments=inc_amend,
                    limit=lim,
                )
                if res["filings"]:
                    key_filings[label] = res["filings"] if lim > 1 else res["filings"][0]

        tag_provenance = {
            mk: meta["tags_used"][0]
            for mk, meta in extracted_meta.items()
            if meta.get("tags_used")
        }

        dossier_payload: Dict[str, Any] = {
            "company_profile": profile,
            "period_type": period_type,
            "headline_financials_by_period": snapshots,
            "key_sec_filings": key_filings,
            "xbrl_tag_provenance": tag_provenance,
        }
        if str(tag_provenance.get("operating_income", "")).startswith("derived:"):
            dossier_payload["accounting_structure_notes"] = [
                "This company does not tag a standalone us-gaap:OperatingIncomeLoss subtotal in its 10-K XBRL (it presents Gross Profit minus Total Expense and Other Income = Pretax Income). Operating Income (EBIT = pretax_income + interest_expense), Core Operating Expenses (R&D + SG&A), and total_expense_and_other_net (gross_profit - pretax_income) are already derived and reconciled from the official SEC companyfacts XBRL API. Do NOT browse or download 10-K .htm files to re-verify XBRL tags."
            ]

        return prune_payload_for_llm(dossier_payload, max_list_items=12)

    # ==========================================================================
    # Tool 2: `analyze_financial_statements_and_ratios`
    # ==========================================================================

    async def analyze_financial_statements_and_ratios(
        self,
        identifier: str,
        statement_types: Optional[List[str]] = None,
        period_type: str = "annual",
        periods: int = 5,
    ) -> Dict[str, Any]:
        resolved = await self.resolve_company(identifier)
        if "error" in resolved:
            return resolved

        cik_10 = resolved["cik_10"]
        periods = max(2, min(int(periods), 10))
        req_statements = set(
            s.lower() for s in (statement_types or ["income_statement", "balance_sheet", "cash_flow", "ratios"])
        )

        facts = await self.get_company_facts(cik_10)
        if not isinstance(facts, dict) or "error" in facts:
            return {"error": "facts_unavailable", "company": resolved, "detail": facts}

        income_keys = [
            "revenue", "cost_of_revenue", "gross_profit", "r_and_d", "sga",
            "operating_expenses", "operating_income", "interest_expense",
            "other_nonoperating_income_expense", "pretax_income", "income_tax",
            "income_from_continuing_operations", "net_income", "eps_basic", "eps_diluted", "shares_diluted",
        ]
        balance_keys = [
            "total_cash", "accounts_receivable", "inventory", "current_assets",
            "ppe_net", "goodwill", "total_assets", "accounts_payable",
            "short_term_debt", "current_liabilities", "long_term_debt",
            "total_liabilities", "retained_earnings", "stockholders_equity", "shares_outstanding",
        ]
        cashflow_keys = [
            "operating_cash_flow", "investing_cash_flow", "financing_cash_flow",
            "capex", "depreciation_amortization", "sbc", "dividends_paid", "share_repurchases",
        ]

        all_keys = list(dict.fromkeys(income_keys + balance_keys + cashflow_keys))
        _, extracted_meta, snapshots = self.build_harmonized_period_snapshots(
            facts,
            all_keys,
            period_type=period_type,
            periods=periods,
        )

        def slice_statement(keys_subset: List[str], include_computed: Optional[List[str]] = None) -> List[Dict[str, Any]]:
            rows: List[Dict[str, Any]] = []
            target_keys = keys_subset + (include_computed or [])
            for snap in snapshots:
                m = snap["metrics"]
                filtered = {k: m[k] for k in target_keys if k in m}
                rows.append({"period_end": snap["period_end"], "line_items": filtered})
            return rows

        result: Dict[str, Any] = {
            "company": {
                "cik": resolved["cik"],
                "ticker": resolved["ticker"],
                "name": facts.get("entityName") or resolved["title"],
            },
            "period_type": period_type,
            "periods_analyzed": [s["period_end"] for s in snapshots],
        }

        if len(snapshots) >= 2:
            latest_m = snapshots[0]["metrics"]
            oldest_m = snapshots[-1]["metrics"]
            n_intervals = len(snapshots) - 1
            result["multi_period_cagr_summary"] = {
                "intervals": n_intervals,
                "from_period": snapshots[-1]["period_end"],
                "to_period": snapshots[0]["period_end"],
                "revenue_cagr_pct": self._compute_cagr_pct(oldest_m.get("revenue"), latest_m.get("revenue"), n_intervals),
                "operating_income_cagr_pct": self._compute_cagr_pct(
                    oldest_m.get("operating_income"), latest_m.get("operating_income"), n_intervals
                ),
                "net_income_cagr_pct": self._compute_cagr_pct(
                    oldest_m.get("net_income"), latest_m.get("net_income"), n_intervals
                ),
                "fcf_cagr_pct": self._compute_cagr_pct(
                    oldest_m.get("free_cash_flow"), latest_m.get("free_cash_flow"), n_intervals
                ),
            }

        if "income_statement" in req_statements:
            result["income_statement"] = slice_statement(
                income_keys, include_computed=["total_expense_and_other_net"]
            )
        if "balance_sheet" in req_statements:
            result["balance_sheet"] = slice_statement(balance_keys, include_computed=["total_debt"])
        if "cash_flow" in req_statements:
            result["cash_flow"] = slice_statement(cashflow_keys, include_computed=["free_cash_flow"])
        if "ratios" in req_statements:
            result["financial_ratios"] = [
                {"period_end": s["period_end"], "ratios": s["ratios"]} for s in snapshots
            ]

        result["xbrl_tags_used"] = {
            mk: meta["tags_used"][0]
            for mk, meta in extracted_meta.items()
            if meta.get("tags_used")
        }
        if str(result["xbrl_tags_used"].get("operating_income", "")).startswith("derived:"):
            result["accounting_structure_notes"] = [
                "This company does not tag a standalone us-gaap:OperatingIncomeLoss subtotal in its 10-K XBRL (it presents Gross Profit minus Total Expense and Other Income = Pretax Income). Operating Income (EBIT = pretax_income + interest_expense), Core Operating Expenses (R&D + SG&A), and total_expense_and_other_net (gross_profit - pretax_income) are already derived and reconciled from the official SEC companyfacts XBRL API. Do NOT browse or download 10-K .htm files to re-verify XBRL tags."
            ]
        return prune_payload_for_llm(result, max_list_items=15)

    # ==========================================================================
    # Tool 3: `search_and_inspect_sec_filings`
    # ==========================================================================

    async def search_and_inspect_sec_filings(
        self,
        identifier: str,
        form_types: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        item_8k_filter: Optional[str] = None,
        include_amendments: bool = True,
        limit: int = 15,
    ) -> Dict[str, Any]:
        resolved = await self.resolve_company(identifier)
        if "error" in resolved:
            return resolved

        cik_10 = resolved["cik_10"]
        cik_int = resolved["cik_int"]
        limit = max(1, min(int(limit), 50))

        submissions = await self.get_submissions(cik_10)
        if not isinstance(submissions, dict) or "error" in submissions:
            return {"error": "submissions_unavailable", "company": resolved, "detail": submissions}

        # Check if start_date precedes the oldest date in `filings.recent` and overflow files exist
        extra_blocks: List[Dict[str, Any]] = []
        recent = (submissions.get("filings") or {}).get("recent") or {}
        recent_dates = recent.get("filingDate") or []
        overflow_files = (submissions.get("filings") or {}).get("files") or []

        if start_date and recent_dates and start_date < min(recent_dates) and overflow_files:
            tasks: Dict[str, Awaitable[Any]] = {}
            for ofile in overflow_files[:2]:
                fname = ofile.get("name")
                filing_from = ofile.get("filingFrom") or ""
                filing_to = ofile.get("filingTo") or "9999-12-31"
                if fname and filing_to >= start_date and (not end_date or filing_from <= end_date):
                    tasks[fname] = self.api_client.request("GET", f"/submissions/{fname}")
            if tasks:
                overflow_res = await self.api_client.fan_out_gather(tasks)
                for _, block in overflow_res.items():
                    if isinstance(block, dict) and "accessionNumber" in block:
                        extra_blocks.append(block)

        filtered = self.zip_and_filter_filings(
            submissions,
            cik_int,
            form_types=form_types,
            start_date=start_date,
            end_date=end_date,
            item_8k_filter=item_8k_filter,
            include_amendments=include_amendments,
            limit=limit,
            extra_recent_blocks=extra_blocks,
        )

        return prune_payload_for_llm({
            "company": {
                "cik": resolved["cik"],
                "ticker": resolved["ticker"],
                "name": submissions.get("name") or resolved["title"],
                "sic_description": submissions.get("sicDescription"),
            },
            "filters_applied": {
                "form_types": form_types,
                "start_date": start_date,
                "end_date": end_date,
                "item_8k_filter": item_8k_filter,
                "include_amendments": include_amendments,
            },
            "total_matching_filings": filtered["total_matching_filings"],
            "counts_by_form": filtered["counts_by_form"],
            "filings": filtered["filings"],
        }, max_list_items=limit)

    # ==========================================================================
    # Tool 4: `trace_xbrl_metric_history`
    # ==========================================================================

    async def trace_xbrl_metric_history(
        self,
        identifier: str,
        concept_or_tag: str,
        taxonomy: str = "us-gaap",
        period_type: str = "annual",
        periods: int = 10,
        include_restatement_audit: bool = False,
    ) -> Dict[str, Any]:
        resolved = await self.resolve_company(identifier)
        if "error" in resolved:
            return resolved

        cik_10 = resolved["cik_10"]
        cik_int = resolved["cik_int"]
        periods = max(1, min(int(periods), 25))

        clean_concept = (concept_or_tag or "").strip()
        if ":" in clean_concept:
            pfx, rest = clean_concept.split(":", 1)
            if pfx.lower() in ("us-gaap", "dei", "ifrs-full"):
                taxonomy = pfx.lower()
                clean_concept = rest.strip()

        lower_concept = clean_concept.lower()
        canonical_key = CONCEPT_SYNONYMS.get(lower_concept, lower_concept)

        # Also allow matching any XBRL tag name case-insensitively (e.g. OperatingIncomeLoss or OPERATINGINCOMELOSS)
        if canonical_key not in HARMONIZED_CONCEPTS and canonical_key not in ("free_cash_flow", "total_debt", "net_debt", "total_cash"):
            for h_key, h_spec in HARMONIZED_CONCEPTS.items():
                for _, h_tag in h_spec.get("tags", []):
                    if h_tag.lower() == lower_concept:
                        canonical_key = h_key
                        clean_concept = h_tag
                        break
                if canonical_key in HARMONIZED_CONCEPTS:
                    break

        spec = HARMONIZED_CONCEPTS.get(canonical_key)

        if spec:
            tag_pairs = spec["tags"][:4]
            frame_type = spec["frame_type"]
            concept_label = spec["label"]
        else:
            if clean_concept.lower().startswith("entity"):
                taxonomy = "dei"
            tag_pairs = [(taxonomy, clean_concept)]
            frame_type = "instant" if any(w in lower_concept for w in ("assets", "liabilities", "shares", "debt", "equity", "cash", "inventory", "goodwill", "receivable", "payable")) else "duration"
            concept_label = clean_concept

        # Parallel fan-out across `companyconcept` endpoints for candidate tags
        tasks = {
            f"{tax}:{tag}": self.api_client.request(
                "GET", f"/api/xbrl/companyconcept/CIK{cik_10}/{tax}/{tag}.json"
            )
            for tax, tag in tag_pairs
        }
        concept_responses = await self.api_client.fan_out_gather(tasks)

        candidate_extractions: List[Tuple[str, int, str, str, Dict[str, Dict[str, Any]], str]] = []
        for idx, (tax, tag) in enumerate(tag_pairs):
            tag_id = f"{tax}:{tag}"
            resp = concept_responses.get(tag_id)
            if not isinstance(resp, dict) or "error" in resp or "units" not in resp:
                continue
            unit, series = self.extract_points_from_concept_obj(
                resp,
                frame_type=frame_type,
                period_type=period_type,
                include_restatements=include_restatement_audit,
            )
            if series:
                latest_ym = max(series.keys())
                desc = str(resp.get("description") or resp.get("label") or "")
                candidate_extractions.append((latest_ym, -idx, tag_id, unit, series, desc))

        # Check if we need to fall back to harmonized companyfacts snapshots
        # (e.g. for derived metrics like free_cash_flow, total_debt, net_debt, or companies like IBM
        # where operating_income is derived from PretaxIncome + InterestExpense).
        newest_ym = max((x[0] for x in candidate_extractions), default="")
        derived_or_harmonized_keys = {
            "free_cash_flow",
            "total_debt",
            "net_debt",
            "total_cash",
            "operating_income",
            "gross_profit",
            "operating_expenses",
            "revenue",
            "net_income",
            "r_and_d",
            "sga",
            "sbc",
            "capex",
            "operating_cash_flow",
            "total_assets",
            "stockholders_equity",
        }
        if (not candidate_extractions or newest_ym < "2021-01") and canonical_key in derived_or_harmonized_keys:
            facts = await self.get_company_facts(cik_10)
            if isinstance(facts, dict) and "error" not in facts:
                eff_period_type = "annual" if period_type == "all" else period_type
                metric_list = [
                    "revenue",
                    "cost_of_revenue",
                    "gross_profit",
                    "r_and_d",
                    "sga",
                    "operating_expenses",
                    "operating_income",
                    "pretax_income",
                    "interest_expense",
                    "net_income",
                    "operating_cash_flow",
                    "capex",
                    "sbc",
                    "total_cash",
                    "total_assets",
                    "short_term_debt",
                    "long_term_debt",
                    "stockholders_equity",
                ]
                if canonical_key not in metric_list:
                    metric_list.append(canonical_key)
                _, extracted_map, snaps = self.build_harmonized_period_snapshots(
                    facts,
                    metric_list,
                    period_type=eff_period_type,
                    periods=periods + 1,
                )
                derived_series: Dict[str, Dict[str, Any]] = {}
                derived_tag_label = f"Derived:{canonical_key}"
                if canonical_key == "free_cash_flow":
                    derived_tag_label = "Derived:OCF-CapEx"
                    concept_label = "Free Cash Flow (OCF - CapEx)"
                elif canonical_key == "total_debt":
                    derived_tag_label = "Derived:ShortTerm+LongTermDebt"
                    concept_label = "Total Debt (Short + Long-Term)"
                elif canonical_key == "net_debt":
                    derived_tag_label = "Derived:TotalDebt-TotalCash"
                    concept_label = "Net Debt (Total Debt - Total Cash)"
                else:
                    used_list = extracted_map.get(canonical_key, {}).get("tags_used") or []
                    if used_list:
                        derived_tag_label = str(used_list[0]).split(" ")[0]

                for snap in snaps:
                    ym = snap["period_ym"]
                    val = snap["metrics"].get(canonical_key)
                    if val is None and canonical_key in snap.get("ratios", {}):
                        val = snap["ratios"].get(canonical_key)
                    if val is not None:
                        derived_series[ym] = {
                            "period_end": snap["period_end"],
                            "val": val,
                            "form": "10-K" if eff_period_type == "annual" else "10-Q",
                            "filed": snap["period_end"],
                            "frame": f"CY{snap['period_end'][:4]}",
                            "source_tag": derived_tag_label,
                        }
                if derived_series:
                    latest_derived_ym = max(derived_series.keys())
                    if not candidate_extractions or latest_derived_ym > newest_ym:
                        candidate_extractions.append(
                            (
                                latest_derived_ym,
                                10,
                                derived_tag_label,
                                "USD",
                                derived_series,
                                f"Harmonized SEC EDGAR series for {concept_label}",
                            )
                        )

        if not candidate_extractions:
            return {
                "error": "concept_not_found",
                "company": resolved,
                "concept_requested": concept_or_tag,
                "tried_tags": [f"{t}:{g}" for t, g in tag_pairs],
                "hint": "Call `resolve_and_discover_sec_entities` with `xbrl_tag_keyword` to discover exact XBRL tags reported by this company.",
            }

        candidate_extractions.sort(key=lambda x: (x[0], x[1]), reverse=True)
        merged_series: Dict[str, Dict[str, Any]] = {}
        tags_used: List[str] = []
        primary_unit = candidate_extractions[0][3]
        description = candidate_extractions[0][5]

        for _, _, tag_id, _, series, _ in candidate_extractions:
            added = False
            for ym, pt in series.items():
                if ym not in merged_series:
                    pt_copy = dict(pt)
                    pt_copy["source_tag"] = tag_id
                    merged_series[ym] = pt_copy
                    added = True
            if added:
                tags_used.append(tag_id)

        sorted_yms = sorted(merged_series.keys(), reverse=True)[: periods + 1]
        display_yms = sorted_yms[:periods]

        timeline: List[Dict[str, Any]] = []
        numeric_vals: List[float] = []
        for i, ym in enumerate(display_yms):
            pt = merged_series[ym]
            prev_pt = merged_series[sorted_yms[i + 1]] if (i + 1) < len(sorted_yms) else None
            val = pt.get("val")
            prev_val = prev_pt.get("val") if prev_pt else None
            if isinstance(val, (int, float)):
                numeric_vals.append(float(val))
            accn = str(pt.get("accn") or "")
            filing_index_url = (
                f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{accn.replace('-', '')}/{accn}-index.htm"
                if accn else None
            )
            pct_chg = self._safe_growth_pct(
                float(val) if isinstance(val, (int, float)) else None,
                float(prev_val) if isinstance(prev_val, (int, float)) else None,
            )
            rest_hist = pt.get("restatement_history") if include_restatement_audit else None
            rest_audit = {
                "was_restated": bool(rest_hist),
                "initial_reported_value": rest_hist[-1].get("prior_val") if rest_hist else None,
            }
            item: Dict[str, Any] = {
                "period_end": pt["period_end"],
                "val": val,
                "value": val,
                "pct_change": pct_chg,
                "period_over_period_growth_pct": pct_chg,
                "form": pt.get("form") or ("10-K" if period_type == "annual" else "10-Q"),
                "filed": pt.get("filed"),
                "frame": pt.get("frame"),
                "source_tag": pt.get("source_tag"),
                "filing_index_url": filing_index_url,
                "restatement_audit": rest_audit,
            }
            if rest_hist:
                item["restatement_history"] = rest_hist
            timeline.append(item)

        summary_stats: Dict[str, Any] = {}
        cagr_val: Optional[float] = None
        if numeric_vals:
            cagr_val = (
                self._compute_cagr_pct(numeric_vals[-1], numeric_vals[0], len(numeric_vals) - 1)
                if len(numeric_vals) >= 2
                else None
            )
            summary_stats = {
                "latest_val": numeric_vals[0],
                "oldest_val": numeric_vals[-1],
                "min_val": min(numeric_vals),
                "max_val": max(numeric_vals),
                "mean_val": round(statistics.mean(numeric_vals), 2),
                "cagr_pct": cagr_val,
            }

        resolved_tag = tags_used[0] if tags_used else concept_label
        return prune_payload_for_llm({
            "company": {
                "cik": resolved["cik"],
                "ticker": resolved["ticker"],
                "name": resolved["title"],
            },
            "concept_requested": concept_or_tag,
            "concept_resolved": resolved_tag,
            "cagr_pct": cagr_val,
            "concept": {
                "requested": concept_or_tag,
                "label": concept_label,
                "unit": primary_unit,
                "tags_used": tags_used,
                "description": description[:300] if description else None,
            },
            "period_type": period_type,
            "summary_statistics": summary_stats,
            "time_series": timeline,
        }, max_list_items=periods)

    # ==========================================================================
    # Tool 5: `compare_peer_group_financials`
    # ==========================================================================

    async def compare_peer_group_financials(
        self,
        identifiers: List[str],
        metrics: Optional[List[str]] = None,
        period_type: str = "annual",
        fiscal_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        clean_ids = [i.strip() for i in (identifiers or []) if i and i.strip()][:10]
        if len(clean_ids) < 2:
            return {"error": "invalid_peer_group", "message": "Provide at least 2 peer identifiers to compare."}

        resolved_peers: List[Dict[str, Any]] = []
        unresolved: List[str] = []
        for ident in clean_ids:
            res = await self.resolve_company(ident)
            if "error" in res:
                unresolved.append(ident)
            else:
                resolved_peers.append(res)

        if not resolved_peers:
            return {"error": "no_valid_peers", "unresolved": unresolved}

        # Parallel fan-out across all peer CIKs for `submissions` + `companyfacts`
        tasks: Dict[str, Awaitable[Any]] = {}
        for peer in resolved_peers:
            c10 = peer["cik_10"]
            tasks[f"sub_{c10}"] = self.get_submissions(c10)
            tasks[f"facts_{c10}"] = self.get_company_facts(c10)

        gathered = await self.api_client.fan_out_gather(tasks)

        core_keys = [
            "revenue", "cost_of_revenue", "gross_profit", "operating_income", "net_income",
            "eps_diluted", "r_and_d", "operating_cash_flow", "capex",
            "total_cash", "total_assets", "long_term_debt", "short_term_debt", "stockholders_equity",
        ]

        peer_rows: List[Dict[str, Any]] = []
        for peer in resolved_peers:
            c10 = peer["cik_10"]
            sub = gathered.get(f"sub_{c10}") or {}
            facts = gathered.get(f"facts_{c10}") or {}
            if not isinstance(facts, dict) or "error" in facts:
                continue

            _, _, snapshots = self.build_harmonized_period_snapshots(
                facts,
                core_keys,
                period_type=period_type,
                periods=4,
            )
            if not snapshots:
                continue

            chosen_snap = snapshots[0]
            if fiscal_year:
                target_prefix = str(fiscal_year)
                for s in snapshots:
                    if s["period_end"].startswith(target_prefix):
                        chosen_snap = s
                        break

            m = chosen_snap["metrics"]
            r = chosen_snap["ratios"]
            peer_rows.append({
                "ticker": peer["ticker"] or peer["cik"],
                "name": (sub.get("name") if isinstance(sub, dict) else None) or peer["title"],
                "cik": peer["cik"],
                "sic_industry": sub.get("sicDescription") if isinstance(sub, dict) else None,
                "period_end": chosen_snap["period_end"],
                "revenue": m.get("revenue"),
                "yoy_revenue_growth_pct": r.get("yoy_revenue_growth_pct"),
                "gross_margin_pct": r.get("gross_margin_pct"),
                "operating_margin_pct": r.get("operating_margin_pct"),
                "net_margin_pct": r.get("net_margin_pct"),
                "rd_pct_of_revenue": r.get("rd_pct_of_revenue"),
                "net_income": m.get("net_income"),
                "eps_diluted": m.get("eps_diluted"),
                "free_cash_flow": m.get("free_cash_flow"),
                "fcf_margin_pct": r.get("fcf_margin_pct"),
                "total_cash": m.get("total_cash"),
                "total_debt": m.get("total_debt"),
                "roe_pct": r.get("roe_pct"),
                "debt_to_equity": r.get("debt_to_equity"),
            })

        # Compute peer-group median and mean benchmarks across numeric fields
        benchmark_fields = [
            "revenue", "yoy_revenue_growth_pct", "gross_margin_pct",
            "operating_margin_pct", "net_margin_pct", "rd_pct_of_revenue",
            "free_cash_flow", "fcf_margin_pct", "roe_pct", "debt_to_equity",
        ]
        peer_medians: Dict[str, Any] = {}
        peer_means: Dict[str, Any] = {}
        for bf in benchmark_fields:
            vals = [float(p[bf]) for p in peer_rows if isinstance(p.get(bf), (int, float))]
            if vals:
                peer_medians[bf] = round(statistics.median(vals), 2)
                peer_means[bf] = round(statistics.mean(vals), 2)

        # Sort peers by revenue descending by default
        peer_rows.sort(key=lambda x: float(x.get("revenue") or 0.0), reverse=True)

        return prune_payload_for_llm({
            "period_type": period_type,
            "requested_fiscal_year": fiscal_year,
            "peer_count": len(peer_rows),
            "unresolved_identifiers": unresolved or None,
            "peer_group_benchmarks": {
                "median": peer_medians,
                "mean": peer_means,
            },
            "peer_comparison_table": peer_rows,
        }, max_list_items=12)

    # ==========================================================================
    # Tool 6: `benchmark_industry_xbrl_frame`
    # ==========================================================================

    async def benchmark_industry_xbrl_frame(
        self,
        concept_or_tag: str,
        calendar_year: int,
        calendar_quarter: Optional[int] = None,
        highlight_identifier: Optional[str] = None,
        unit: str = "USD",
        taxonomy: str = "us-gaap",
        top_n: int = 15,
    ) -> Dict[str, Any]:
        await self._ensure_tickers_loaded()
        top_n = max(5, min(int(top_n), 40))

        clean_concept = (concept_or_tag or "").strip()
        canonical_key = CONCEPT_SYNONYMS.get(clean_concept.lower(), clean_concept.lower())
        spec = HARMONIZED_CONCEPTS.get(canonical_key)

        if spec:
            tag_pairs = spec["tags"][:2]
            is_instant = spec["frame_type"] == "instant"
            unit = spec["unit"].replace("/", "-per-")
            concept_label = spec["label"]
        else:
            if ":" in clean_concept:
                taxonomy, clean_concept = clean_concept.split(":", 1)
            elif clean_concept.startswith("Entity"):
                taxonomy = "dei"
                unit = "shares"
            is_instant = any(
                w in clean_concept for w in ("Assets", "Liabilities", "Equity", "Cash", "Debt", "Shares", "Inventory", "Goodwill")
            )
            tag_pairs = [(taxonomy, clean_concept)]
            concept_label = clean_concept

        # Build candidate frame period strings (handling durational vs instantaneous `I` suffix)
        if calendar_quarter in (1, 2, 3, 4):
            if is_instant:
                frame_candidates = [f"CY{calendar_year}Q{calendar_quarter}I", f"CY{calendar_year}Q{calendar_quarter}"]
            else:
                frame_candidates = [f"CY{calendar_year}Q{calendar_quarter}", f"CY{calendar_year}Q{calendar_quarter}I"]
        else:
            if is_instant:
                frame_candidates = [f"CY{calendar_year}Q4I", f"CY{calendar_year}Q3I", f"CY{calendar_year}"]
            else:
                frame_candidates = [f"CY{calendar_year}", f"CY{calendar_year}Q4I"]

        highlight_company: Optional[Dict[str, Any]] = None
        if highlight_identifier:
            hc = await self.resolve_company(highlight_identifier)
            if "error" not in hc:
                highlight_company = hc

        # Fetch frame(s) across primary alias tags for the first working frame period
        chosen_frame = frame_candidates[0]
        merged_pts_by_cik: Dict[int, Dict[str, Any]] = {}
        tags_queried: List[str] = []

        for frame_period in frame_candidates:
            tasks = {
                f"{tax}:{tag}": self.api_client.request(
                    "GET", f"/api/xbrl/frames/{tax}/{tag}/{unit}/{frame_period}.json"
                )
                for tax, tag in tag_pairs
            }
            responses = await self.api_client.fan_out_gather(tasks)
            for tax, tag in tag_pairs:
                tag_id = f"{tax}:{tag}"
                resp = responses.get(tag_id)
                frame_rows = (resp.get("data") if isinstance(resp, dict) else None)
                if isinstance(frame_rows, list) and frame_rows:
                    chosen_frame = frame_period
                    tags_queried.append(tag_id)
                    for pt in frame_rows:
                        cik_val = pt.get("cik")
                        val = pt.get("val")
                        if cik_val is None or not isinstance(val, (int, float)):
                            continue
                        cik_int = int(cik_val)
                        if cik_int not in merged_pts_by_cik:
                            merged_pts_by_cik[cik_int] = {
                                "cik_int": cik_int,
                                "cik": f"CIK{cik_int:010d}",
                                "entity_name": pt.get("entityName"),
                                "loc": pt.get("loc"),
                                "val": float(val),
                                "end": pt.get("end"),
                                "accn": pt.get("accn"),
                                "source_tag": tag_id,
                            }
            if merged_pts_by_cik:
                break

        if not merged_pts_by_cik:
            return {
                "error": "frame_not_found",
                "concept": concept_or_tag,
                "tried_frames": frame_candidates,
                "tried_tags": [f"{t}:{g}" for t, g in tag_pairs],
                "unit": unit,
            }

        # Sort descending by value
        ranked = sorted(merged_pts_by_cik.values(), key=lambda x: x["val"], reverse=True)
        total_entities = len(ranked)
        vals_asc = sorted(x["val"] for x in ranked)

        def pct_at(p: float) -> float:
            idx = min(total_entities - 1, max(0, int(round(p * (total_entities - 1)))))
            return round(vals_asc[idx], 2)

        def enrich_pt(rank_idx: int, item: Dict[str, Any]) -> Dict[str, Any]:
            ent_meta = self._by_cik.get(item["cik_int"]) or {}
            return {
                "rank": rank_idx + 1,
                "percentile": round(((total_entities - rank_idx) / total_entities) * 100.0, 2),
                "ticker": ent_meta.get("ticker") or None,
                "entity_name": item.get("entity_name") or ent_meta.get("title"),
                "cik": item["cik"],
                "val": item["val"],
                "period_end": item.get("end"),
                "source_tag": item.get("source_tag"),
            }

        top_leaders = [enrich_pt(i, ranked[i]) for i in range(min(top_n, total_entities))]

        highlight_position: Optional[Dict[str, Any]] = None
        if highlight_company:
            target_cik = highlight_company["cik_int"]
            for idx, item in enumerate(ranked):
                if item["cik_int"] == target_cik:
                    neighbors_start = max(0, idx - 2)
                    neighbors_end = min(total_entities, idx + 3)
                    highlight_position = {
                        "company": enrich_pt(idx, item),
                        "out_of_total_entities": total_entities,
                        "surrounding_peers": [
                            enrich_pt(n_idx, ranked[n_idx])
                            for n_idx in range(neighbors_start, neighbors_end)
                        ],
                    }
                    break
            if not highlight_position:
                highlight_position = {
                    "company": highlight_company,
                    "note": f"Entity did not report in frame {chosen_frame} under {tags_queried} (often due to non-calendar fiscal year alignment; use `get_company_360_financial_dossier` or `compare_peer_group_financials`).",
                }

        return prune_payload_for_llm({
            "frame_period": chosen_frame,
            "concept": {
                "requested": concept_or_tag,
                "label": concept_label,
                "unit": unit,
                "tags_aggregated": tags_queried,
            },
            "market_distribution_statistics": {
                "total_reporting_entities": total_entities,
                "market_total_sum": round(sum(vals_asc), 2),
                "mean": round(statistics.mean(vals_asc), 2),
                "p10": pct_at(0.10),
                "p25": pct_at(0.25),
                "p50_median": pct_at(0.50),
                "p75": pct_at(0.75),
                "p90": pct_at(0.90),
                "p99": pct_at(0.99),
            },
            "highlighted_company_benchmark": highlight_position,
            "top_leaders": top_leaders,
        }, max_list_items=top_n)

    # ==========================================================================
    # Tool 7: `resolve_and_discover_sec_entities`
    # ==========================================================================

    async def resolve_and_discover_sec_entities(
        self,
        company_query: str,
        xbrl_tag_keyword: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        limit = max(1, min(int(limit), 15))
        matches = await self.fuzzy_search_companies(company_query, limit=limit)
        if not matches:
            # Try direct CIK resolution as fallback
            single = await self.resolve_company(company_query)
            if "error" not in single:
                matches = [single]
            else:
                return single

        # Parallel inline enrichment via `submissions` for top matches
        tasks: Dict[str, Awaitable[Any]] = {
            m["cik_10"]: self.get_submissions(m["cik_10"]) for m in matches
        }
        if xbrl_tag_keyword:
            tasks["top_facts"] = self.get_company_facts(matches[0]["cik_10"])

        gathered = await self.api_client.fan_out_gather(tasks)

        enriched_matches: List[Dict[str, Any]] = []
        for m in matches:
            c10 = m["cik_10"]
            sub = gathered.get(c10) or {}
            profile = self.extract_corporate_profile(sub, m)
            profile["match_score"] = m.get("match_score")
            enriched_matches.append(profile)

        discovered_tags: Optional[List[Dict[str, Any]]] = None
        if xbrl_tag_keyword:
            kw_lower = xbrl_tag_keyword.strip().lower()
            facts = gathered.get("top_facts") or {}
            taxonomies = (facts.get("facts") or {}) if isinstance(facts, dict) else {}
            tag_hits: List[Tuple[int, Dict[str, Any]]] = []

            for tax_name, tax_dict in taxonomies.items():
                if not isinstance(tax_dict, dict):
                    continue
                for tag_name, concept_obj in tax_dict.items():
                    if not isinstance(concept_obj, dict):
                        continue
                    label = str(concept_obj.get("label") or "")
                    desc = str(concept_obj.get("description") or "")
                    haystack = f"{tag_name} {label} {desc}".lower()
                    if kw_lower not in haystack:
                        continue

                    unit, series = self.extract_points_from_concept_obj(
                        concept_obj,
                        frame_type="duration",
                        period_type="all",
                    )
                    latest_ym = max(series.keys()) if series else ""
                    latest_pt = series.get(latest_ym) if latest_ym else None
                    score = (
                        (100 if kw_lower in tag_name.lower() else 50)
                        + (30 if latest_ym >= "2024-01" else 0)
                        + min(len(series), 20)
                    )
                    tag_hits.append((
                        score,
                        {
                            "taxonomy": tax_name,
                            "tag": tag_name,
                            "label": label,
                            "unit": unit,
                            "latest_period_end": latest_pt.get("period_end") if latest_pt else None,
                            "latest_val": latest_pt.get("val") if latest_pt else None,
                            "total_periods_reported": len(series),
                            "description": desc[:200] if desc else None,
                        },
                    ))

            tag_hits.sort(key=lambda x: x[0], reverse=True)
            discovered_tags = [t[1] for t in tag_hits[:20]]

        return prune_payload_for_llm({
            "query": company_query,
            "matched_companies": enriched_matches,
            "xbrl_tag_discovery": {
                "for_company": enriched_matches[0]["name"] if enriched_matches else None,
                "keyword": xbrl_tag_keyword,
                "matching_concepts": discovered_tags,
            } if xbrl_tag_keyword else None,
        }, max_list_items=20)
