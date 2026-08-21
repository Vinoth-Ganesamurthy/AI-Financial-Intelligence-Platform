# 📊 AI Financial Intelligence Platform

A full-stack financial research application that combines **fundamental analysis, technical indicators, historical stock performance, machine-learning-based news sentiment, and country-aware macroeconomic analysis** in a responsive web dashboard.

Unlike black-box predictions, the platform provides **explainable intelligence** by exposing module scores, weights, contributions, and data availability.

---

## 🌐 Live Application

- 🚀 **Dashboard** → [Live Demo](https://ai-financial-intelligence-platform-m9jl.onrender.com/)  
- 📚 **Swagger Docs** → [API Documentation](https://ai-financial-intelligence-platform-api.onrender.com/docs)  
- ⚙️ **Backend API** → [FastAPI Service](https://ai-financial-intelligence-platform-api.onrender.com/)  
- ❤️ **Health Check** → [Status Endpoint](https://ai-financial-intelligence-platform-api.onrender.com/health)

> ⚠️ Hosted on Render free tier. Cold starts may take ~50s after inactivity.

---

## 📌 Overview

The platform automates investment research by:

1. Accepting company name or stock symbol  
2. Resolving to supported exchange symbols  
3. Validating listed companies  
4. Retrieving market, company, news, and macro data  
5. Running five independent analysis modules  
6. Normalizing results to `-1` → `+1` scale  
7. Producing a weighted **Intelligence Score**  
8. Reporting coverage, confidence, and partial-data warnings  
9. Presenting results via a **Next.js dashboard**

---

## ✨ Key Features

- 🏢 **Fundamental Analysis** → Valuation, profitability, growth, leverage, returns, cash flow  
- 📈 **Technical Analysis** → SMA, EMA, RSI, MACD, Bollinger Bands, ATR, volume signals  
- 📰 **News Sentiment** → ML-classified company news (Positive / Neutral / Negative)  
- 📊 **Historical Performance** → Returns, volatility, drawdown, price range  
- 🌎 **Macro Analysis** → Inflation, GDP growth, unemployment, interest rates (sector-aware)  

Additional capabilities:
- Multi-market support (US, India, Singapore, Australia)  
- Provider fallback & retry handling  
- Official macroeconomic data caching  
- Explainable weights & contributions  
- Responsive charts & metric cards  

---

## 🧠 Intelligence Score

| Module        | Weight | Purpose                                        |
|---------------|--------|------------------------------------------------|
| Fundamental   | 30%    | Financial quality, valuation, growth, leverage |
| Technical     | 20%    | Trend, momentum, volatility, volume            |
| Sentiment     | 15%    | Company-news sentiment                         |
| Historical    | 15%    | Return and risk characteristics                |
| Sector & Macro| 20%    | Economic conditions adjusted for sector        |

**Score Range:**
- `+0.50 → +1.00` → Strongly favourable  
- `+0.20 → +0.50` → Favourable  
- `-0.20 → +0.20` → Neutral  
- `-0.50 → -0.20` → Cautious  
- `-1.00 → -0.50` → Unfavourable  

> ℹ️ The Intelligence Score is **not** a forecast or recommendation. It is an analytical indicator.

---

## 🧰 Tech Stack

- **Frontend** → Next.js 16, React, TypeScript, Tailwind CSS, Recharts  
- **Backend** → Python 3.12, FastAPI, Uvicorn, Pydantic  
- **Data Analysis** → pandas, NumPy, yfinance  
- **ML** → scikit-learn, TF-IDF, Joblib  
- **Data Providers** → Yahoo Finance, Finnhub, NewsAPI, FRED, MoSPI, RBI, SingStat, World Bank  
- **Deployment** → Render (Web Service + Static Site), GitHub  
- **Testing** → pytest, FastAPI TestClient  

---

## 🔌 API Endpoints

- **Status** → `GET /`  
- **Health Check** → `GET /health`  
- **Generate Intelligence Report** →  
GET /api/v1/intelligence/{stock_symbol}?news_limit=5

Code
Examples:  
- `/api/v1/intelligence/AAPL?news_limit=5`  
- `/api/v1/intelligence/INFY.NS?news_limit=5`  
- `/api/v1/intelligence/Tesla?news_limit=5`

Response includes:
- Resolved company identity  
- Intelligence Score & classification  
- Coverage & confidence  
- Module scores & contributions  
- Fundamental, technical, sentiment, historical, macro details  
- Partial-data warnings  

---

## 💻 Local Installation

```bash
# Clone repository
git clone https://github.com/Vinoth-Ganesamurthy/AI-Financial-Intelligence-Platform.git
cd AI-Financial-Intelligence-Platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows

# Install backend dependencies
pip install -r requirements.txt

# Configure environment variables (.env)
FRED_API_KEY=your_fred_api_key
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key
FRONTEND_ORIGINS=http://localhost:3000

# Start backend
uvicorn src.api.main:app --reload
Frontend setup:

bash
cd frontend
npm ci
echo "NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000" > .env.local
npm run dev
🧪 Testing
bash
python -m pytest -q
npm run build

Covers:
Module score calculations
Intelligence aggregation
API routes & validation
Company resolution & rejection
Macro resilience & caching

🔮 Future Improvements
Interactive candlestick charts
Sentiment trends over time
Side-by-side company comparison
Watchlists & portfolio analysis
FinBERT sentiment model
Earnings calendar integration
Peer valuation comparisons
PDF export & saved reports
Authentication & history
Docker + CI/CD

⚖️ Disclaimer
This project is for educational and analytical purposes only.
It does not provide financial advice or guarantee future performance.
Users should conduct independent research and consult professionals before making investment decisions.

👨‍💻 Owner & Author
Vinoth Ganesamurthy
LinkedIn → https://www.linkedin.com/in/vinoth-ganesamurthy/

Developed as a full-stack financial analytics, machine-learning, and cloud-deployment portfolio project.

⭐ Support
If you find this project useful, consider giving the repository a ⭐ on GitHub.

Repository → https://github.com/Vinoth-Ganesamurthy/Real-Time-Financial-News-Sentiment-Analyzer
Live Demo → https://ai-financial-intelligence-platform-m9jl.onrender.com
