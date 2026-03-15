import yfinance as yf
import boto3
from langchain.tools import tool
from app.config import settings

bedrock_agent_runtime = boto3.client(
    "bedrock-agent-runtime",
    region_name=settings.aws_region
)


@tool
def retrieve_realtime_stock_price(ticker: str) -> str:
    """
    Retrieve the current real-time stock price for a given ticker symbol.
    Use this when the user asks for the current or latest price of a stock.
    Args:
        ticker: Stock ticker symbol e.g. 'AMZN'
    """
    try:
        stock         = yf.Ticker(ticker.upper())
        info          = stock.info
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close    = info.get("previousClose")
        currency      = info.get("currency", "USD")
        name          = info.get("longName", ticker)
        market_cap    = info.get("marketCap")
        change        = current_price - prev_close if current_price and prev_close else None
        pct_change    = (change / prev_close * 100) if change and prev_close else None

        result = (
            f"📈 {name} ({ticker.upper()})\n"
            f"Current Price: {currency} {current_price:.2f}\n"
            f"Previous Close: {currency} {prev_close:.2f}\n"
        )
        if change is not None:
            direction = "▲" if change >= 0 else "▼"
            result += f"Change: {direction} {abs(change):.2f} ({abs(pct_change):.2f}%)\n"
        if market_cap:
            result += f"Market Cap: ${market_cap:,.0f}\n"
        return result
    except Exception as e:
        return f"Error retrieving real-time price for {ticker}: {str(e)}"


@tool
def retrieve_historical_stock_price(ticker: str, period: str = "1y") -> str:
    """
    Retrieve historical stock price data for a given ticker and time period.
    Use for past performance, Q4 prices, or historical data questions.
    Args:
        ticker: Stock ticker symbol e.g. 'AMZN'
        period: '1mo','3mo','6mo','1y','2y','5y','ytd'
    """
    try:
        stock = yf.Ticker(ticker.upper())
        hist  = stock.history(period=period)

        if hist.empty:
            return f"No historical data found for {ticker}"

        start_date   = hist.index[0].strftime("%Y-%m-%d")
        end_date     = hist.index[-1].strftime("%Y-%m-%d")
        open_price   = hist["Open"].iloc[0]
        close_price  = hist["Close"].iloc[-1]
        high         = hist["High"].max()
        low          = hist["Low"].min()
        avg_price    = hist["Close"].mean()
        total_change = ((close_price - open_price) / open_price) * 100

        result = (
            f"📊 Historical Data for {ticker.upper()} ({start_date} → {end_date})\n"
            f"Opening Price: ${open_price:.2f}\n"
            f"Latest Close:  ${close_price:.2f}\n"
            f"Period High:   ${high:.2f}\n"
            f"Period Low:    ${low:.2f}\n"
            f"Average Close: ${avg_price:.2f}\n"
            f"Total Change:  {total_change:+.2f}%\n"
        )

        q4_data = hist[
            (hist.index >= "2024-10-01") & (hist.index <= "2024-12-31")
        ]
        if not q4_data.empty:
            q4_open   = q4_data["Close"].iloc[0]
            q4_close  = q4_data["Close"].iloc[-1]
            q4_high   = q4_data["High"].max()
            q4_low    = q4_data["Low"].min()
            q4_change = ((q4_close - q4_open) / q4_open) * 100
            result += (
                f"\n📅 Q4 2024 (Oct–Dec 2024):\n"
                f"  Start: ${q4_open:.2f}  |  End: ${q4_close:.2f}\n"
                f"  High:  ${q4_high:.2f}  |  Low: ${q4_low:.2f}\n"
                f"  Change: {q4_change:+.2f}%\n"
            )

        monthly = hist.resample("ME")["Close"].last().tail(6)
        result += "\n📆 Recent Monthly Closes:\n"
        for date, price in monthly.items():
            result += f"  {date.strftime('%b %Y')}: ${price:.2f}\n"

        return result
    except Exception as e:
        return f"Error retrieving historical data for {ticker}: {str(e)}"


@tool
def retrieve_from_knowledge_base(query: str) -> str:
    """
    Search Amazon's financial documents (2024 Annual Report, Q2/Q3 2025 Earnings)
    for relevant information. Use for questions about Amazon's business, financials,
    AI strategy, office space, analyst predictions, and any company-specific data.
    Args:
        query: Natural language question to search the knowledge base
    """
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=settings.knowledge_base_id,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5
                }
            }
        )

        results = response.get("retrievalResults", [])
        if not results:
            return "No relevant information found in the knowledge base."

        formatted = "📚 From Amazon Financial Documents:\n\n"
        for i, result in enumerate(results, 1):
            content  = result["content"]["text"]
            score    = result.get("score", 0)
            location = result.get("location", {})
            source   = location.get("s3Location", {}).get("uri", "Financial Document")

            formatted += f"[Source {i} | Relevance: {score:.2f}]\n"
            formatted += f"File: {source.split('/')[-1]}\n"
            formatted += f"{content}\n\n---\n\n"

        return formatted
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"