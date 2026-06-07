"""Stock fetcher tool using yfinance."""

from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio

try:
    import yfinance as yf
except ImportError:
    yf = None


class StockFetcherTool:
    """Tool for fetching stock data using yfinance."""

    name = "stock_fetcher"
    description = "Fetch stock prices, history, and company information using yfinance"

    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)"
            },
            "action": {
                "type": "string",
                "enum": ["price", "history", "info", "dividends"],
                "description": "Type of data to fetch"
            },
            "period": {
                "type": "string",
                "description": "Time period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"
            },
            "interval": {
                "type": "string",
                "description": "Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)"
            }
        },
        "required": ["ticker", "action"]
    }

    def __init__(self):
        self._check_dependency()

    def _check_dependency(self) -> None:
        """Check if yfinance is installed."""
        if yf is None:
            raise ImportError(
                "yfinance is not installed. Install with: pip install yfinance"
            )

    async def execute(self, input: Dict[str, Any], context: Any = None) -> str:
        """
        Execute stock fetch operation.

        Args:
            input: Tool input with ticker and action
            context: Agent context

        Returns:
            str: Result or error message
        """
        try:
            ticker = input.get("ticker", "").upper()
            action = input.get("action", "price")
            period = input.get("period", "1mo")
            interval = input.get("interval", "1d")

            if not ticker:
                return "Error: ticker is required"

            if action == "price":
                return await self._get_current_price(ticker)
            elif action == "history":
                return await self._get_historical_data(ticker, period, interval)
            elif action == "info":
                return await self._get_company_info(ticker)
            elif action == "dividends":
                return await self._get_dividends(ticker)
            else:
                return f"Error: Unknown action '{action}'"

        except Exception as e:
            return f"Error fetching stock data: {str(e)}"

    async def _get_current_price(self, ticker: str) -> str:
        """Get current stock price."""
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
            "ticker": ticker,
            "current_price": info.get("currentPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open"),
            "high": info.get("dayHigh"),
            "low": info.get("dayLow"),
            "volume": info.get("volume"),
            "market_cap": info.get("marketCap"),
            "timestamp": datetime.now().isoformat()
        }

        return self._format_result(result)

    async def _get_historical_data(self, ticker: str, period: str, interval: str) -> str:
        """Get historical price data."""
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            return f"No historical data found for {ticker}"

        # Get last 10 data points
        recent_data = hist.tail(10)

        result = {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "data_points": len(hist),
            "recent_prices": [
                {
                    "date": str(idx.date()),
                    "open": float(row['Open']) if not pd.isna(row['Open']) else None,
                    "high": float(row['High']) if not pd.isna(row['High']) else None,
                    "low": float(row['Low']) if not pd.isna(row['Low']) else None,
                    "close": float(row['Close']) if not pd.isna(row['Close']) else None,
                    "volume": int(row['Volume']) if not pd.isna(row['Volume']) else None,
                }
                for idx, row in recent_data.iterrows()
            ]
        }

        return self._format_result(result)

    async def _get_company_info(self, ticker: str) -> str:
        """Get company information."""
        stock = yf.Ticker(ticker)
        info = stock.info

        result = {
            "ticker": ticker,
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "pb_ratio": info.get("priceToBook"),
            "dividend_yield": info.get("dividendYield"),
            "52_week_high": info.get("fiftyTwoWeekHigh"),
            "52_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "timestamp": datetime.now().isoformat()
        }

        return self._format_result(result)

    async def _get_dividends(self, ticker: str) -> str:
        """Get dividend information."""
        stock = yf.Ticker(ticker)
        dividends = stock.dividends.tail(10)

        if dividends.empty:
            return f"No dividend data found for {ticker}"

        result = {
            "ticker": ticker,
            "dividend_count": len(dividends),
            "recent_dividends": [
                {
                    "date": str(idx.date()),
                    "dividend": float(row['Dividends']) if not pd.isna(row['Dividends']) else None,
                }
                for idx, row in dividends.iterrows()
            ]
        }

        return self._format_result(result)

    def _format_result(self, data: dict) -> str:
        """Format result as readable text."""
        return str(data)
