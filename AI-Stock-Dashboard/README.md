# 📈 AI Stock Dashboard

A production-ready, AI-powered stock market dashboard built with **Streamlit**, **Plotly**, **yfinance**, **SQLite**, **NewsAPI** and **Google Gemini**.

> Real-time global markets · Stock details with technical indicators · News & AI summaries · Portfolio tracker · Watchlist · Gemini chatbot · User auth.

---

## ✨ Features

| Page | What it does |
| --- | --- |
| **Dashboard** | Global indices (S&P 500, Dow, NASDAQ, NIFTY, SENSEX…), Fear & Greed gauge (computed), sector heatmap & performance, Top Gainers / Losers / Most Active / Trending. |
| **Stock Details** | Search any ticker (incl. NSE `.NS` & BSE `.BO`). Candlestick + MA(20/50/200), Volume, RSI, MACD, 52-week range, fundamentals, analyst targets. |
| **Compare** | Side-by-side comparison of up to 4 stocks with normalized return chart and a metrics table. |
| **News** | NewsAPI search & top headlines, sentiment badges, “Open Article” and **Gemini AI Summary** buttons. Friendly fallback when key is missing. |
| **AI Chatbot** | Conversational Gemini assistant with chat memory; reset anytime. |
| **Portfolio** | Buy / Sell at live or custom price, P&L, allocation pie, equity curve, transactions, delete holdings. |
| **Watchlist** | Add / remove tickers; live prices update on every refresh. |
| **Account** | Sign up / Log in / Log out — bcrypt password hashing, SQLite storage. |

Beautiful dark-themed UI, responsive layout, robust error handling (no page ever crashes).

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone <your-repo-url> AI-Stock-Dashboard
cd AI-Stock-Dashboard

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate           # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY and NEWSAPI_KEY

# 5. Run
streamlit run app.py
```

App opens at **http://localhost:8501**.

---

## 🔑 API Keys

The app reads **only** from `.env`. Never hard-code keys.

| Variable | Where to get it | Required? |
| --- | --- | --- |
| `GOOGLE_API_KEY` | <https://aistudio.google.com/apikey> | For AI chatbot + news summaries |
| `NEWSAPI_KEY` | <https://newsapi.org/register> (free tier) | For the News page |

Without these keys the dashboard, stock details, compare, portfolio and watchlist pages still work — the News and Chatbot pages will simply show a friendly “API key not set” message.

---

## 🗂️ Project Structure

```
AI-Stock-Dashboard/
├── app.py                  # Streamlit entrypoint (navigation + sidebar)
├── config.py               # Loads .env, app constants
├── requirements.txt        # All Python dependencies
├── README.md
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml         # Theme & server config
├── assets/
│   └── styles.css          # Custom CSS for cards, badges, etc.
├── database/
│   ├── __init__.py
│   └── db.py               # SQLite connection + table init
├── services/
│   ├── __init__.py
│   ├── stock_service.py    # yfinance wrappers, technicals, F&G
│   ├── news_service.py     # NewsAPI integration
│   ├── ai_service.py       # Gemini chat + summarization
│   └── portfolio_service.py# Auth, portfolio, watchlist DB ops
├── pages/
│   ├── __init__.py
│   ├── home.py
│   ├── stock_details.py
│   ├── compare.py
│   ├── news.py
│   ├── chatbot.py
│   ├── portfolio.py
│   ├── watchlist.py
│   └── auth.py
├── utils/
│   ├── __init__.py
│   ├── helpers.py          # Formatting / sentiment helpers
│   └── ui.py               # Reusable Streamlit components
└── models/
    └── __init__.py
```

---

## 🖼️ Screenshots

> Add your screenshots to `assets/screenshots/` and reference them here.

- Dashboard with Fear & Greed gauge and sector heatmap
- Stock Details with candlestick + RSI + MACD
- Portfolio with allocation pie and equity curve
- News with Gemini AI summaries
- AI Chatbot conversation

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **Streamlit** ≥ 1.36 (uses `st.navigation`)
- **Plotly** for interactive charts
- **yfinance** for market data
- **NewsAPI** for headlines
- **Google Gemini** (`gemini-2.0-flash`) for AI features
- **SQLite** for storage (users, portfolio, transactions, watchlist)
- **bcrypt** for password hashing
- **python-dotenv** for env management

---

## 🧰 Troubleshooting

**`ModuleNotFoundError` after install** — make sure your virtual env is activated: `source venv/bin/activate`, then `pip install -r requirements.txt` again.

**News page says “key not configured”** — add `NEWSAPI_KEY=...` to `.env` and restart Streamlit.

**Chatbot says “could not reach Gemini”** — verify `GOOGLE_API_KEY` is correct at <https://aistudio.google.com/apikey>.

**`yfinance` returns no data for a ticker** — the symbol may be wrong (e.g. use `RELIANCE.NS` not `RELIANCE`) or Yahoo may be rate-limiting briefly. The app shows a friendly message instead of crashing.

**Port 8501 already in use** — `streamlit run app.py --server.port 8502`.

**Reset the database** — delete `database/dashboard.db`; tables are recreated on next launch.

---

## ⚖️ Disclaimer

This project is built for **educational and portfolio purposes only**. Nothing here is investment advice. Market data may be delayed and is provided by third parties.

---

## 📜 License

MIT — feel free to fork, extend and showcase on your portfolio.
