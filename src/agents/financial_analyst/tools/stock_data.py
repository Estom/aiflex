"""
Stock Data Tool

Example tool for fetching stock data.
"""

from pstock_sdk.agent.tools.base_tool import BaseTool


class StockDataTool(BaseTool):
    """Tool for fetching basic stock information"""

    name: str = "stock_data"
    description: str = (
        "Fetches basic stock information including price, market cap, and volume"
    )

    async def execute(self, input: dict, context=None) -> str:
        """
        Execute the stock data tool

        Args:
            input: Dictionary with 'symbol' key (e.g., {'symbol': 'AAPL'})
            context: Agent context (unused)

        Returns:
            Formatted stock information
        """
        symbol = input.get("symbol", "").upper()

        if not symbol:
            return "Error: No stock symbol provided"

        # Mock data - in production, this would call a real API
        mock_data = {
            "AAPL": {"price": 178.50, "market_cap": "2.8T", "volume": "45.2M"},
            "GOOGL": {"price": 141.25, "market_cap": "1.7T", "volume": "18.5M"},
            "MSFT": {"price": 378.90, "market_cap": "2.8T", "volume": "22.1M"},
        }

        data = mock_data.get(symbol, {"price": "N/A", "market_cap": "N/A", "volume": "N/A"})

        return f"""
Stock Information for {symbol}:
- Current Price: ${data['price']}
- Market Cap: ${data['market_cap']}
- Volume: {data['volume']}

Note: This is mock data. In production, real-time data would be fetched.
        """.strip()


def create_tool():
    """Factory function for tool discovery"""
    return StockDataTool()
