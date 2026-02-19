"""
Smart Financial Alerts API endpoints.

Provides price alert management with:
- Alert creation/deletion for stock tickers
- Auto-extraction of tickers from documents
- Alert checking against live market data
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status, Depends

from app.services.llm import LLMService, get_llm_service
from app.services.vector_store import VectorStore, get_vector_store
from app.middleware.auth import get_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Financial Alerts"])


# ═══════════════════════════════════════════════════════
# In-memory alert storage
# ═══════════════════════════════════════════════════════

class AlertConfig(BaseModel):
    id: str
    ticker: str
    condition: str  # 'above' or 'below'
    target_price: float
    current_price: Optional[float] = None
    created_at: str
    triggered: bool = False
    triggered_at: Optional[str] = None
    document_id: Optional[str] = None  # Optional link to source document
    note: Optional[str] = None


_alerts_store: Dict[str, List[AlertConfig]] = {}  # user_id -> list of alerts


# ═══════════════════════════════════════════════════════
# TICKER EXTRACTION
# ═══════════════════════════════════════════════════════

TICKER_EXTRACTION_PROMPT = """Analyze the following financial document content and extract all stock ticker symbols mentioned or clearly implied.

Document content:
{context}

Return ONLY a JSON object in this format:
{{
    "tickers": [
        {{"symbol": "AAPL", "company": "Apple Inc.", "context": "Mentioned as key holding"}},
        {{"symbol": "MSFT", "company": "Microsoft Corporation", "context": "Revenue comparison"}}
    ]
}}

Only include tickers that are clearly referenced or strongly implied. Return ONLY valid JSON."""


class ExtractedTicker(BaseModel):
    symbol: str
    company: str
    context: str


class TickerExtractionResponse(BaseModel):
    document_id: str
    tickers: List[ExtractedTicker]


@router.get(
    "/documents/{document_id}/tickers",
    response_model=TickerExtractionResponse,
    summary="Extract Tickers from Document",
    description="Auto-extract stock ticker symbols mentioned in a document."
)
async def extract_tickers(
    document_id: str,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Extract stock tickers from a document."""
    try:
        results = vector_store.search(
            user_id=user_id,
            query="stock ticker company shares equity investment portfolio holdings",
            n_results=6,
            document_id=document_id
        )

        docs = [r["content"] for r in results] if results else []
        if not docs:
            return TickerExtractionResponse(document_id=document_id, tickers=[])

        context = "\n\n".join(docs)[:4000]

        messages = [
            {"role": "system", "content": "You are a financial analyst. Extract stock tickers. Return only valid JSON."},
            {"role": "user", "content": TICKER_EXTRACTION_PROMPT.format(context=context)}
        ]

        response = llm_service._call_openai(
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )

        content = response["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        tickers = [
            ExtractedTicker(
                symbol=t.get("symbol", ""),
                company=t.get("company", ""),
                context=t.get("context", "")
            )
            for t in data.get("tickers", [])
        ]

        return TickerExtractionResponse(document_id=document_id, tickers=tickers)

    except Exception as e:
        logger.error(f"Ticker extraction failed: {e}")
        return TickerExtractionResponse(document_id=document_id, tickers=[])


# ═══════════════════════════════════════════════════════
# ALERT CRUD
# ═══════════════════════════════════════════════════════

class CreateAlertRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10)
    condition: str = Field(..., pattern="^(above|below)$")
    target_price: float = Field(..., gt=0)
    document_id: Optional[str] = None
    note: Optional[str] = None


class AlertsResponse(BaseModel):
    alerts: List[AlertConfig]
    total: int


@router.post(
    "/alerts",
    response_model=AlertConfig,
    summary="Create Price Alert",
    description="Create a new price alert for a stock ticker."
)
async def create_alert(
    request: CreateAlertRequest,
    user_id: str = Depends(get_user_id)
):
    """Create a new price alert."""
    import uuid

    alert = AlertConfig(
        id=str(uuid.uuid4())[:8],
        ticker=request.ticker.upper(),
        condition=request.condition,
        target_price=request.target_price,
        created_at=datetime.now().isoformat(),
        document_id=request.document_id,
        note=request.note
    )

    if user_id not in _alerts_store:
        _alerts_store[user_id] = []

    # Limit to 20 alerts per user
    if len(_alerts_store[user_id]) >= 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Maximum 20 alerts allowed", "error_code": "ALERT_LIMIT"}
        )

    _alerts_store[user_id].append(alert)

    return alert


@router.get(
    "/alerts",
    response_model=AlertsResponse,
    summary="List All Alerts",
    description="Get all price alerts for the authenticated user."
)
async def list_alerts(
    user_id: str = Depends(get_user_id)
):
    """List all alerts for a user."""
    alerts = _alerts_store.get(user_id, [])
    return AlertsResponse(alerts=alerts, total=len(alerts))


@router.delete(
    "/alerts/{alert_id}",
    summary="Delete Alert",
    description="Delete a specific price alert."
)
async def delete_alert(
    alert_id: str,
    user_id: str = Depends(get_user_id)
):
    """Delete a specific alert."""
    alerts = _alerts_store.get(user_id, [])
    _alerts_store[user_id] = [a for a in alerts if a.id != alert_id]
    return {"status": "deleted", "alert_id": alert_id}


# ═══════════════════════════════════════════════════════
# ALERT CHECKING
# ═══════════════════════════════════════════════════════

@router.post(
    "/alerts/check",
    summary="Check All Alerts",
    description="Check all active alerts against current market prices."
)
async def check_alerts(
    user_id: str = Depends(get_user_id)
):
    """Check alerts against live prices."""
    alerts = _alerts_store.get(user_id, [])
    if not alerts:
        return {"triggered": [], "total_checked": 0}

    try:
        import yfinance as yf
    except ImportError:
        return {"triggered": [], "total_checked": 0, "error": "yfinance not available"}

    triggered = []
    tickers_to_check = list(set(a.ticker for a in alerts if not a.triggered))

    # Batch-fetch prices
    prices: Dict[str, float] = {}
    for ticker in tickers_to_check:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d")
            if not hist.empty:
                prices[ticker] = float(hist["Close"].iloc[-1])
        except Exception as e:
            logger.warning(f"Could not fetch price for {ticker}: {e}")

    # Check each alert
    for alert in alerts:
        if alert.triggered:
            continue

        price = prices.get(alert.ticker)
        if price is None:
            continue

        alert.current_price = round(price, 2)

        hit = False
        if alert.condition == "above" and price >= alert.target_price:
            hit = True
        elif alert.condition == "below" and price <= alert.target_price:
            hit = True

        if hit:
            alert.triggered = True
            alert.triggered_at = datetime.now().isoformat()
            triggered.append({
                "alert_id": alert.id,
                "ticker": alert.ticker,
                "condition": alert.condition,
                "target_price": alert.target_price,
                "current_price": alert.current_price,
                "note": alert.note
            })

    return {
        "triggered": triggered,
        "total_checked": len(tickers_to_check),
        "prices": {k: round(v, 2) for k, v in prices.items()}
    }
