"""
Stock Market API endpoints for FinRAG.

Provides live stock market data including indices,
top movers, and price history for the dashboard.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeout

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


class IndexData(BaseModel):
    """Stock index data."""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    sparkline: List[float]


class StockMover(BaseModel):
    """Top mover stock data."""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int


class MarketResponse(BaseModel):
    """Market overview response."""
    indices: List[IndexData]
    top_gainers: List[StockMover]
    top_losers: List[StockMover]
    trending: List[StockMover]
    last_updated: str


# Cache for market data (avoid hitting API too frequently)
_market_cache: Dict[str, Any] = {}
_cache_expiry: Optional[datetime] = None
CACHE_DURATION_SECONDS = 300  # 5 minutes


def _get_cached_data() -> Optional[Dict[str, Any]]:
    """Return cached data if still valid."""
    global _cache_expiry
    if _cache_expiry and datetime.now() < _cache_expiry and _market_cache:
        return _market_cache
    return None


def _set_cache(data: Dict[str, Any]) -> None:
    """Cache the market data."""
    global _market_cache, _cache_expiry
    _market_cache = data
    _cache_expiry = datetime.now() + timedelta(seconds=CACHE_DURATION_SECONDS)


def _fetch_market_data() -> Dict[str, Any]:
    """
    Fetch live market data using yfinance.
    
    Returns dict with indices, gainers, losers, trending.
    """
    try:
        import yfinance as yf
    except ImportError:
        logger.warning("yfinance not installed, using fallback data")
        return _get_fallback_data()
    
    try:
        # Fetch major indices
        index_symbols = {
            "^GSPC": "S&P 500",
            "^IXIC": "NASDAQ",
            "^DJI": "Dow Jones",
            "^RUT": "Russell 2000",
        }
        
        # ── Helper functions for parallel fetching ──────────────
        def _fetch_index(symbol: str, name: str) -> Optional[IndexData]:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d", interval="1h")
                if hist.empty:
                    return None
                current_price = float(hist["Close"].iloc[-1])
                prev_close = float(hist["Close"].iloc[0])
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close else 0
                sparkline = [round(float(v), 2) for v in hist["Close"].tail(24).tolist()]
                return IndexData(
                    symbol=symbol, name=name,
                    price=round(current_price, 2),
                    change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    sparkline=sparkline,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
                return None

        # ── Known company names (avoid slow ticker.info calls) ──
        STOCK_NAMES = {
            "AAPL": "Apple Inc.", "MSFT": "Microsoft", "GOOGL": "Alphabet Inc.",
            "AMZN": "Amazon.com", "NVDA": "NVIDIA Corp.", "META": "Meta Platforms",
            "TSLA": "Tesla Inc.", "JPM": "JPMorgan Chase", "V": "Visa Inc.",
            "WMT": "Walmart Inc.", "JNJ": "Johnson & Johnson", "PG": "Procter & Gamble",
            "MA": "Mastercard", "HD": "Home Depot", "DIS": "Walt Disney",
            "NFLX": "Netflix Inc.", "AMD": "AMD Inc.", "INTC": "Intel Corp.",
            "CRM": "Salesforce", "PYPL": "PayPal", "BA": "Boeing Co.", "GS": "Goldman Sachs",
        }

        def _fetch_mover(sym: str) -> Optional[StockMover]:
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="2d")
                if hist.empty:
                    return None
                current = float(hist["Close"].iloc[-1])
                prev = float(hist["Close"].iloc[0]) if len(hist) > 1 else current
                change = current - prev
                change_pct = (change / prev) * 100 if prev else 0
                volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist else 0
                return StockMover(
                    symbol=sym, name=STOCK_NAMES.get(sym, sym),
                    price=round(current, 2),
                    change=round(change, 2),
                    change_percent=round(change_pct, 2),
                    volume=volume,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch {sym}: {e}")
                return None

        # ── Parallel fetch indices + movers ─────────────────────
        stock_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
            "JPM", "V", "WMT", "JNJ", "PG", "MA", "HD", "DIS",
            "NFLX", "AMD", "INTC", "CRM", "PYPL", "BA", "GS",
        ]

        indices: List[IndexData] = []
        movers: List[StockMover] = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            idx_futures = {
                executor.submit(_fetch_index, sym, name): sym
                for sym, name in index_symbols.items()
            }
            mover_futures = {
                executor.submit(_fetch_mover, sym): sym
                for sym in stock_symbols
            }

            for fut in as_completed(idx_futures, timeout=30):
                result = fut.result()
                if result:
                    indices.append(result)

            for fut in as_completed(mover_futures, timeout=30):
                result = fut.result()
                if result:
                    movers.append(result)

        # If we got nothing from live API, use fallback data
        if not indices or len(movers) < 5:
            logger.warning("yfinance returned insufficient data, using fallback")
            return _get_fallback_data()
        
        # Sort for gainers/losers
        sorted_movers = sorted(movers, key=lambda x: x.change_percent, reverse=True)
        top_gainers = sorted_movers[:5]
        top_losers = sorted_movers[-5:][::-1]  # Reverse so worst is first
        
        # Trending = highest volume
        trending = sorted(movers, key=lambda x: x.volume, reverse=True)[:8]
        
        return {
            "indices": indices,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
            "trending": trending,
            "last_updated": datetime.now().isoformat(),
        }
    except (Exception, FuturesTimeout) as e:
        logger.error(f"Failed to fetch market data: {e}")
        return _get_fallback_data()


def _get_fallback_data() -> Dict[str, Any]:
    """Return fallback/demo data when yfinance is unavailable."""
    import random
    
    def rand_sparkline(base: float, n: int = 24) -> List[float]:
        vals = [base]
        for _ in range(n - 1):
            vals.append(round(vals[-1] + random.uniform(-base * 0.002, base * 0.002), 2))
        return vals
    
    indices = [
        IndexData(symbol="^GSPC", name="S&P 500", price=5987.15, change=23.45, change_percent=0.39, sparkline=rand_sparkline(5987)),
        IndexData(symbol="^IXIC", name="NASDAQ", price=19432.80, change=-42.12, change_percent=-0.22, sparkline=rand_sparkline(19432)),
        IndexData(symbol="^DJI", name="Dow Jones", price=43812.50, change=112.30, change_percent=0.26, sparkline=rand_sparkline(43812)),
        IndexData(symbol="^RUT", name="Russell 2000", price=2287.40, change=-8.55, change_percent=-0.37, sparkline=rand_sparkline(2287)),
    ]
    
    sample_stocks = [
        ("AAPL", "Apple Inc.", 235.42, 3.12, 1.34, 52341000),
        ("NVDA", "NVIDIA Corp.", 875.30, 18.45, 2.15, 45200000),
        ("MSFT", "Microsoft", 418.92, 5.67, 1.37, 23100000),
        ("GOOGL", "Alphabet Inc.", 178.90, 2.34, 1.33, 19800000),
        ("META", "Meta Platforms", 612.45, 8.90, 1.47, 17500000),
        ("TSLA", "Tesla Inc.", 248.90, -5.40, -2.12, 68900000),
        ("AMZN", "Amazon.com", 198.30, -1.20, -0.60, 31200000),
        ("AMD", "AMD Inc.", 168.75, -3.80, -2.20, 42000000),
        ("JPM", "JPMorgan Chase", 198.50, 1.20, 0.61, 8500000),
        ("NFLX", "Netflix Inc.", 892.10, -12.30, -1.36, 5200000),
    ]
    
    movers = [
        StockMover(symbol=s[0], name=s[1], price=s[2], change=s[3], change_percent=s[4], volume=s[5])
        for s in sample_stocks
    ]
    
    sorted_movers = sorted(movers, key=lambda x: x.change_percent, reverse=True)
    
    return {
        "indices": indices,
        "top_gainers": sorted_movers[:5],
        "top_losers": sorted_movers[-5:][::-1],
        "trending": sorted(movers, key=lambda x: x.volume, reverse=True)[:8],
        "last_updated": datetime.now().isoformat(),
    }


@router.get(
    "/market",
    response_model=MarketResponse,
    summary="Get Market Overview",
    description="""
    Get a comprehensive market overview including:
    - Major index performance (S&P 500, NASDAQ, DOW, Russell 2000)
    - Top gainers and losers
    - Trending stocks by volume
    
    Data is cached for 5 minutes to avoid rate limiting.
    """,
)
def get_market_data():
    """
    Fetch market overview data.

    Returns cached data if available, otherwise fetches fresh data.
    Note: This is a regular def (not async) so FastAPI runs it in
    a thread pool, preventing it from blocking the event loop.
    """
    cached = _get_cached_data()
    if cached:
        return cached
    
    data = _fetch_market_data()
    _set_cache(data)
    return data


@router.get(
    "/price-history/{symbol}",
    summary="Get Price History",
    description="Get historical price data for a specific stock symbol.",
)
def get_price_history(
    symbol: str,
    period: str = "1mo",
    interval: str = "1d",
):
    """
    Get historical prices for a stock.
    
    Args:
        symbol: Stock ticker symbol (e.g. AAPL)
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y)
        interval: Data interval (1m, 5m, 15m, 1h, 1d)
    """
    try:
        import yfinance as yf
    except ImportError:
        # Return fallback data
        import random
        base_price = 150.0
        data_points = []
        for i in range(30):
            base_price += random.uniform(-3, 3)
            data_points.append({
                "date": (datetime.now() - timedelta(days=30-i)).strftime("%Y-%m-%d"),
                "open": round(base_price - random.uniform(0, 2), 2),
                "high": round(base_price + random.uniform(0, 3), 2),
                "low": round(base_price - random.uniform(0, 3), 2),
                "close": round(base_price, 2),
                "volume": random.randint(10000000, 50000000),
            })
        return {"symbol": symbol, "data": data_points}
    
    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": f"Invalid period. Use one of: {valid_periods}"}
        )
    
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"No data found for symbol '{symbol}'"}
            )
        
        data_points = []
        for date, row in hist.iterrows():
            data_points.append({
                "date": date.strftime("%Y-%m-%d %H:%M") if interval in ["1m", "5m", "15m", "1h"] else date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        
        return {
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "data": data_points,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch price history for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": f"Failed to fetch data for {symbol}"}
        )
