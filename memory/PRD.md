# AI Stock Dashboard — PRD

## Original Problem Statement (verbatim, condensed)
Build a production-ready Streamlit AI Stock Dashboard for a B.Tech CSE portfolio. Tech:
Python 3.11, Streamlit, SQLite, Plotly, Pandas, NumPy, yfinance, NewsAPI, Google Gemini,
bcrypt, dotenv. Strict project structure required, every feature must work end-to-end,
no crashes, no placeholders. Must run with `pip install -r requirements.txt && streamlit run app.py`.

## Architecture
- **Single-process Streamlit app** at `/app/AI-Stock-Dashboard/`, listens on **port 8501**.
- **SQLite** file at `database/dashboard.db` (created on first launch via `init_db`).
- **Multipage** via `st.navigation([st.Page(...)])` API (callable-based, overrides Streamlit's
  auto-page discovery, so the `pages/` folder is used as a regular Python module).
- **Services layer**:
  - `services/stock_service.py` — yfinance wrappers, technical indicators (MA, RSI, MACD),
    bulk quotes, indices, sectors, gainers/losers/active/trending, calculated Fear & Greed.
  - `services/news_service.py` — NewsAPI client with friendly key-missing fallback.
  - `services/ai_service.py` — Google Gemini (`gemini-2.0-flash`) chat with multi-turn memory.
  - `services/portfolio_service.py` — bcrypt auth + portfolio + transactions + watchlist CRUD.
- **Caching**: `st.cache_data(ttl=60-600s)` on all yfinance calls to avoid rate-limits.
- **Error handling**: every external call wrapped in try/except returning friendly fallbacks.

## User Personas
- **B.Tech CSE student** showcasing full-stack Python skills on GitHub / portfolio.
- **Retail investor** using the local app to monitor markets, news, and a paper portfolio.
- **Recruiter / reviewer** cloning the repo and expecting it to run zero-friction.

## Core Requirements (static)
- Exact directory layout (27 files), no missing `__init__.py`.
- No hard-coded secrets — keys read from `.env` only.
- All pages must render even when `GOOGLE_API_KEY` and `NEWSAPI_KEY` are missing.

## What's Implemented (2026-06-28)
- ✅ Dashboard: Global indices grid (S&P 500, Dow, NASDAQ, NIFTY 50, SENSEX, Russell 2000,
  FTSE 100, VIX), calculated Fear & Greed gauge, sector treemap heatmap, sector performance bar,
  Top Gainers / Top Losers / Most Active / Trending tabs.
- ✅ Stock Details: ticker search, candlestick + MA20/50/200 + Volume, RSI(14), MACD(12,26,9),
  KPI cards (Price, 52W H/L, Mkt Cap), company profile, fundamentals (PE, PEG, P/B, EPS,
  Dividend, Beta, Margins, ROE), analyst targets, "Add to Watchlist".
- ✅ Compare: up to 4 tickers, normalized % return chart, key-metrics table.
- ✅ News: NewsAPI search + category + country, sentiment badges (keyword-based), open article,
  Gemini AI summary button. Friendly fallback when key missing.
- ✅ AI Chatbot: Gemini chat with conversation memory + reset. Friendly fallback when key missing.
- ✅ Portfolio: Buy / Sell at live or custom price, P&L, allocation pie, equity curve, delete
  holding, transactions table.
- ✅ Watchlist: add / remove / live prices.
- ✅ Auth: signup, login, logout, bcrypt hashing, SQLite storage, session_state-backed.
- ✅ Theme: dark theme via `.streamlit/config.toml` + custom CSS (`assets/styles.css`).
  Users can toggle Light/Dark via Streamlit's built-in Settings menu.
- ✅ Verified end-to-end with Playwright: signup → login → buy AAPL → watchlist NVDA.

## Backlog (P1)
- Allow theme toggle button directly in sidebar (not just via Settings menu).
- Persist conversation history per-user in SQLite (currently in `st.session_state`).
- Replace yfinance `Search.lookup` results cache with longer TTL on hits and persist to disk.
- Add CSV export of portfolio + transactions.
- Add price alerts for watchlist (email via SendGrid or SMTP).

## Backlog (P2)
- Option-chain analytics & Greeks.
- Crypto market overview tab (CoinGecko).
- AI-generated weekly portfolio summary email.
- Tests in `tests/` using pytest + requests-mock.

## How to Run
```bash
cd /app/AI-Stock-Dashboard
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your keys
streamlit run app.py   # → http://localhost:8501
```
