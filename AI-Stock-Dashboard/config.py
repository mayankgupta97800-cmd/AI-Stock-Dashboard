"""Application configuration. Loads environment variables and constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env located next to this file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---- API Keys ----
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()

# ---- App ----
APP_NAME = "AI Stock Dashboard"
APP_ICON = "📈"
DB_PATH = str(BASE_DIR / "database" / "dashboard.db")

# Gemini model
GEMINI_MODEL = "gemini-2.0-flash"

# ---- Market Data ----
# Major global indices
INDICES = {
    "^GSPC": "S&P 500",
    "^DJI": "Dow Jones",
    "^IXIC": "NASDAQ",
    "^NSEI": "NIFTY 50",
    "^BSESN": "SENSEX",
    "^RUT": "Russell 2000",
    "^FTSE": "FTSE 100",
    "^VIX": "VIX",
}

# Sector ETFs for sector performance + heatmap
SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLV": "Health Care",
    "XLY": "Consumer Disc.",
    "XLP": "Consumer Staples",
    "XLE": "Energy",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication",
}

# Curated tickers used to compute Top Gainers / Losers / Most Active / Trending
POPULAR_TICKERS = [
    # US Mega caps
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AVGO", "ORCL", "ADBE",
    "NFLX", "AMD", "INTC", "CRM", "QCOM", "CSCO", "TXN", "IBM", "PYPL", "UBER",
    "SHOP", "PLTR", "SNOW", "COIN", "SQ", "SPOT", "ZM", "DOCU", "ROKU", "PINS",
    # US Financials / Industrials / Health
    "JPM", "BAC", "WFC", "GS", "MS", "BLK", "V", "MA", "AXP", "C",
    "JNJ", "PFE", "MRK", "ABBV", "LLY", "UNH", "TMO", "ABT", "DHR", "BMY",
    "WMT", "COST", "HD", "MCD", "NKE", "SBUX", "DIS", "PEP", "KO", "PG",
    "BA", "CAT", "GE", "HON", "LMT", "RTX", "UPS", "FDX", "DE", "MMM",
    "XOM", "CVX", "COP", "SLB", "OXY",
    # India NSE
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "MARUTI.NS", "ASIANPAINT.NS", "TITAN.NS",
    "BAJFINANCE.NS", "WIPRO.NS", "HCLTECH.NS", "ADANIENT.NS", "TATAMOTORS.NS",
]
