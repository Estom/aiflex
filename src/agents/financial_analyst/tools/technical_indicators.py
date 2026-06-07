"""Technical indicators calculation tool."""

from typing import Dict, Any, List
import asyncio
import pandas as pd

try:
    import yfinance as yf
    import ta as ta_lib
except ImportError:
    yf = None
    ta_lib = None


class TechnicalIndicatorsTool:
    """Tool for calculating technical indicators."""

    name = "technical_indicators"
    description = "Calculate technical indicators (MA, RSI, MACD, Bollinger Bands) for stocks"

    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Stock ticker symbol"
            },
            "indicator": {
                "type": "string",
                "enum": ["ma", "ema", "rsi", "macd", "bollinger", "all"],
                "description": "Technical indicator to calculate"
            },
            "period": {
                "type": "integer",
                "description": "Time period for calculation (default: 20)"
            },
            "interval": {
                "type": "string",
                "description": "Data interval (1d, 1h, etc.)"
            }
        },
        "required": ["ticker", "indicator"]
    }

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check if required libraries are installed."""
        if yf is None:
            raise ImportError("yfinance is not installed. Install with: pip install yfinance")
        if ta_lib is None:
            raise ImportError("ta library is not installed. Install with: pip install ta")

    async def execute(self, input: Dict[str, Any], context: Any = None) -> str:
        """Calculate technical indicators."""
        try:
            ticker = input.get("ticker", "").upper()
            indicator = input.get("indicator", "all")
            period = input.get("period", 20)
            interval = input.get("interval", "1d")

            if not ticker:
                return "Error: ticker is required"

            # Fetch historical data
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo", interval=interval)

            if hist.empty:
                return f"No data available for {ticker}"

            # Create DataFrame
            df = pd.DataFrame(hist)

            result = {
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "data_points": len(df)
            }

            # Calculate indicators
            if indicator in ["ma", "all"]:
                result["sma"] = self._calculate_sma(df, period)
                result["ema"] = self._calculate_ema(df, period)

            if indicator in ["rsi", "all"]:
                result["rsi"] = self._calculate_rsi(df, period)

            if indicator in ["macd", "all"]:
                result["macd"] = self._calculate_macd(df)

            if indicator in ["bollinger", "all"]:
                result["bollinger"] = self._calculate_bollinger(df, period)

            return self._format_result(result)

        except Exception as e:
            return f"Error calculating technical indicators: {str(e)}"

    def _calculate_sma(self, df: pd.DataFrame, period: int) -> Dict[str, float]:
        """Calculate Simple Moving Average."""
        sma = df['Close'].rolling(window=period).mean()

        return {
            "period": period,
            "current_value": float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None,
            "recent_values": sma.tail(5).tolist()
        }

    def _calculate_ema(self, df: pd.DataFrame, period: int) -> Dict[str, float]:
        """Calculate Exponential Moving Average."""
        ema = df['Close'].ewm(span=period).mean()

        return {
            "period": period,
            "current_value": float(ema.iloc[-1]) if not pd.isna(ema.iloc[-1]) else None,
            "recent_values": ema.tail(5).tolist()
        }

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """Calculate Relative Strength Index."""
        # Simple RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return {
            "period": period,
            "current_value": float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None,
            "recent_values": rsi.tail(5).tolist(),
            "overbought_threshold": 70,
            "oversold_threshold": 30,
            "signal": "OVERBOUGHT" if rsi.iloc[-1] > 70 else "OVERSOLD" if rsi.iloc[-1] < 30 else "NEUTRAL"
        }

    def _calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Any]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        # Calculate EMAs
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal).mean()

        # Histogram
        histogram = macd_line - signal_line

        return {
            "parameters": {"fast": fast, "slow": slow, "signal": signal},
            "macd_line": float(macd_line.iloc[-1]),
            "signal_line": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1]),
            "signal": "BULLISH" if macd_line.iloc[-1] > signal_line.iloc[-1] else "BEARISH",
            "recent_histogram": histogram.tail(5).tolist()
        }

    def _calculate_bollinger(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, Any]:
        """Calculate Bollinger Bands."""
        sma = df['Close'].rolling(window=period).mean()
        std = df['Close'].rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        current_price = float(df['Close'].iloc[-1])

        return {
            "parameters": {"period": period, "std_dev": std_dev},
            "middle_band": float(sma.iloc[-1]),
            "upper_band": float(upper_band.iloc[-1]),
            "lower_band": float(lower_band.iloc[-1]),
            "current_price": current_price,
            "bandwidth": float((upper_band.iloc[-1] - lower_band.iloc[-1]) / sma.iloc[-1]),
            "position": "UPPER" if current_price > upper_band.iloc[-1] else "LOWER" if current_price < lower_band.iloc[-1] else "MIDDLE",
            "squeeze": (upper_band.iloc[-1] - lower_band.iloc[-1]) < ((upper_band.iloc[-5] - lower_band.iloc[-5]) * 0.7)
        }

    def _format_result(self, data: dict) -> str:
        """Format result as readable text."""
        return str(data)
