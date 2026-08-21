<div align="center">

📊 AI Financial Intelligence Platform

Explainable, multi-market investment research in one dashboard

Combine company fundamentals, technical indicators, historical performance, financial-news sentiment, and country-aware macroeconomic analysis in a single transparent report.











Live Application · REST API · Swagger UI

</div>

🌐 Live Application

Service

Link

🚀 Dashboard

Open the live dashboard

⚙️ Backend API

Open the FastAPI service

📚 Swagger documentation

Explore the API

❤️ Health check

Check API health

[!NOTE]
Render's free backend can spin down after inactivity. The first request may take 50 seconds or longer while the service starts; later requests should be faster.

📌 Project Overview

Investment research is often fragmented across company accounts, price charts, news, and economic releases. This platform combines those areas into one explainable workflow.

The application:

Accepts a company name or stock symbol.

Resolves the input to a supported listed symbol.

Retrieves market, company, news, and macroeconomic data.

Runs five independent analysis modules.

Normalizes every module to a -1 to +1 scale.

Produces a weighted Intelligence Score.

Reports coverage, confidence, module contributions, and partial-data warnings.

Presents the complete result through a responsive Next.js dashboard.

Unlike a black-box prediction, the report exposes the inputs and contribution of every available module.

✨ Key Features

Module

What the platform analyses

🏢 Fundamental

Valuation, profitability, growth, leverage, returns, revenue, and cash flow

📈 Technical

SMA, EMA, RSI, MACD, Bollinger Bands, ATR, volume, and combined signals

📰 Sentiment

Relevant company news classified as Positive, Neutral, or Negative by a trained ML model

📊 Historical

Returns, annualized volatility, maximum drawdown, price range, and current price

🌎 Sector & Macro

Inflation, GDP growth, unemployment, and interest-rate conditions weighted by sector

Additional capabilities include:

Search by stock symbol or company name

Multi-market symbol resolution

Invalid-company rejection

Provider fallback and retry handling

Official macroeconomic data caching

Explainable weights and contributions

Coverage and confidence indicators

Responsive charts and detailed metric cards

FastAPI OpenAPI documentation

Production deployment on Render

🌍 Multi-Market Support

Market

Example companies

Symbols

🇺🇸 United States

Apple, Tesla, NVIDIA

AAPL, TSLA, NVDA

🇮🇳 India — NSE

Reliance Industries, Infosys, TCS

RELIANCE.NS, INFY.NS, TCS.NS

🇸🇬 Singapore — SGX

DBS Group, ST Engineering

D05.SI, S63.SI

🇦🇺 Australia — ASX

BHP, Commonwealth Bank

BHP.AX, CBA.AX

The search box accepts both direct symbols and company names such as Tesla, Infosys, or Tata Consultancy Services.

🔄 Application Flow

flowchart TD
    A[User enters company name or symbol] --> B[Next.js Dashboard]
    B --> C[FastAPI API]
    C --> D[Company & Symbol Resolution]
    D --> E[Financial Intelligence Engine]

    E --> F[Fundamental Analysis]
    E --> G[Technical Analysis]
    E --> H[News Sentiment Analysis]
    E --> I[Historical Analysis]
    E --> J[Sector-aware Macro Analysis]

    F --> K[Normalized Module Scores]
    G --> K
    H --> K
    I --> K
    J --> K

    K --> L[Weighted Intelligence Score]
    L --> M[Classification, Coverage & Confidence]
    M --> N[JSON Response]
    N --> B

🏗️ System Architecture

flowchart LR
    UI[Next.js Frontend] -->|HTTPS / JSON| API[FastAPI Backend]
    API --> ENGINE[Intelligence Engine]

    ENGINE --> MARKET[Market Data Services]
    ENGINE --> FUND[Fundamental Services]
    ENGINE --> NEWS[News Service]
    ENGINE --> MACRO[Macro Data Services]
    ENGINE --> MODEL[Sentiment Model]

    MARKET --> YF[Yahoo Finance]
    FUND --> FH[Finnhub]
    NEWS --> NA[NewsAPI]
    MACRO --> OFFICIAL[FRED / MoSPI / RBI / SingStat]
    MACRO --> WB[World Bank Fallback]

    ENGINE --> RESULT[Explainable Financial Intelligence Report]

🧠 Intelligence Score

Each module produces a normalized score:

Score range

Interpretation

+0.50 to +1.00

Strongly favourable

+0.20 to < +0.50

Favourable

-0.20 to < +0.20

Neutral or balanced

-0.50 to -0.20

Cautious

-1.00 to ≤ -0.50

Unfavourable

Module Weights

Module

Weight

Fundamental

30%

Technical

20%

Sentiment

15%

Historical

15%

Sector & Macro

20%

The combined score is calculated from available weighted contributions:

                         Sum of available weighted contributions
Intelligence Score = -------------------------------------------------
                              Sum of available module weights

If a module is unavailable, its weight is excluded rather than treated as a negative score.

[!IMPORTANT]
The Intelligence Score is an analytical research indicator. It is not a price forecast, guaranteed return, or direct buy/sell recommendation.

🛡️ Resilient Data Pipeline

The platform uses layered data retrieval so a temporary provider failure does not automatically stop the report.

Market Data

flowchart LR
    A[Stock Symbol] --> B[yfinance]
    B -->|Success| D[Clean OHLCV Data]
    B -->|Unavailable / Rate-limited| C[Direct Yahoo Chart API]
    C --> D

Fundamental Data

flowchart LR
    A[Stock Symbol] --> B[yfinance Company Info]
    B -->|Unavailable| C[Finnhub Profile & Metrics]
    C -->|Restricted / Unavailable| D[Direct Yahoo Search & Time Series]
    B -->|Success| E[Normalized Fundamentals]
    C -->|Success| E
    D --> E

Financial News and Sentiment

flowchart LR
    A[Company & Symbol] --> B[NewsAPI]
    B --> C[Relevance Scoring]
    C --> D[Quality Filtering]
    D --> E[Duplicate Removal]
    E --> F[TF-IDF Vectorizer]
    F --> G[ML Classifier]
    G --> H[Positive / Neutral / Negative]

Macroeconomic Data

Market

Preferred sources

Resilience

United States

FRED

Latest successful official snapshot is cached

India

MoSPI CPI, PLFS, NAS and RBI

Cached official observations and World Bank fallbacks

Singapore

SingStat and configured official sources

Cached observations and configured fallbacks

Australia

Configured official sources

Cached observations and configured fallbacks

Every module reports its availability and quality factor. Any recoverable failure appears under Partial data warnings.

🧰 Technology Stack

Layer

Technologies

Frontend

Next.js 16, React, TypeScript, Tailwind CSS, Recharts

Backend

Python 3.12, FastAPI, Uvicorn, Pydantic

Data analysis

pandas, NumPy, yfinance

Machine learning

scikit-learn, TF-IDF, Joblib

HTTP and configuration

Requests, curl-cffi, python-dotenv

Data providers

Yahoo Finance, Finnhub, NewsAPI, FRED, MoSPI, RBI, SingStat, World Bank

Testing

pytest, FastAPI TestClient

Deployment

Render Web Service, Render Static Site, GitHub

📁 Project Structure

Path

Purpose

frontend/

Next.js and TypeScript dashboard

frontend/src/app/

Main application page and layout

frontend/src/components/

Report details and intelligence charts

frontend/src/lib/

Backend API client

frontend/src/types/

TypeScript response definitions

models/

Trained sentiment model, TF-IDF vectorizer, and label encoder

src/analysis/fundamental/

Fundamental data normalization and scoring

src/analysis/technical/

Technical indicator calculations

src/analysis/historical/

Historical return and risk calculations

src/analysis/sentiment/

News retrieval and ML sentiment prediction

src/analysis/macro/

Macro interpretation and sector impact

src/analysis/intelligence/

Weighted intelligence aggregation

src/api/

FastAPI routes and response schemas

src/data/

Company lookup, market data, and macro data services

tests/

Backend unit and API tests

🔌 API Endpoints

Interactive documentation: Open Swagger UI

API Status

GET /

Example response:

{
  "name": "AI Financial Intelligence Platform",
  "version": "1.0.0",
  "status": "running",
  "documentation": "/docs"
}

Health Check

GET /health

Example response:

{
  "status": "healthy"
}

Generate Financial Intelligence

GET /api/v1/intelligence/{stock_symbol}?news_limit=5

Examples:

GET /api/v1/intelligence/AAPL?news_limit=5
GET /api/v1/intelligence/INFY.NS?news_limit=5
GET /api/v1/intelligence/Tesla?news_limit=5

The response includes:

Resolved company identity

Overall Intelligence Score and classification

Coverage and confidence

Module scores, weights, and contributions

Fundamental, technical, sentiment, historical, and macro details

Partial-data warnings

Generation timestamp and disclaimer

💻 Local Installation

1. Clone the Repository

git clone https://github.com/Vinoth-Ganesamurthy/AI-Financial-Intelligence-Platform.git
cd AI-Financial-Intelligence-Platform

2. Create a Virtual Environment

Windows PowerShell:

python -m venv .venv
.venv\Scripts\Activate.ps1

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

3. Install Backend Dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt

4. Configure Backend Variables

Create .env in the repository root:

FRED_API_KEY=your_fred_api_key
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

5. Start the Backend

python -m uvicorn src.api.main:app --reload

Backend: http://127.0.0.1:8000
Swagger: http://127.0.0.1:8000/docs

6. Configure and Start the Frontend

cd frontend
npm ci

Create frontend/.env.local:

NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000

Start Next.js:

npm run dev

Frontend: http://localhost:3000

[!WARNING]
Never commit .env, .env.local, or API keys to GitHub.

🧪 Testing

Run all backend tests from the repository root:

python -m pytest -q

Current verified result:

26 passed

The test suite covers:

Module score calculations

Complete intelligence aggregation

API routes and validation

Company-name resolution

Invalid-company rejection

India GDP and policy-rate retrieval

United States macro resilience

MoSPI connectivity

Cache and provider-failure behaviour

Build and type-check the frontend:

cd frontend
npm run build

🚀 Production Deployment

Backend — Render Web Service

Setting

Value

Root directory

Repository root

Build command

pip install -r requirements.txt

Start command

python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT

Health-check path

/health

Backend environment variables:

FRED_API_KEY=...
NEWS_API_KEY=...
FINNHUB_API_KEY=...
FRONTEND_ORIGINS=https://ai-financial-intelligence-platform-m9jl.onrender.com

Frontend — Render Static Site

Setting

Value

Root directory

frontend

Build command

npm ci && npm run build

Publish directory

out

Frontend environment variable:

NEXT_PUBLIC_API_BASE_URL=https://ai-financial-intelligence-platform-api.onrender.com

The frontend uses Next.js static export mode and is served through Render's static-site CDN.

🧪 Example Companies

Try the live application with:

Company input

Resolved symbol

Apple

AAPL

Tesla

TSLA

Infosys

INFY.NS

Tata Consultancy Services

TCS.NS

Reliance Industries

RELIANCE.NS

DBS Group

D05.SI

BHP

BHP.AX

⚠️ Limitations

Third-party providers can impose rate limits or temporary restrictions.

Some fallback sources provide fewer metrics than primary providers.

News coverage varies by company, market, and publication activity.

Sentiment does not necessarily predict future price movement.

Historical performance does not guarantee future returns.

Macro classifications use analytical thresholds rather than official forecasts.

Free hosting can introduce a cold-start delay after inactivity.

The platform currently focuses on four configured market contexts.

🔮 Future Improvements

Interactive candlestick charts

Sentiment trends over time

Side-by-side company comparison

Watchlists and portfolio analysis

Additional exchanges and macro frameworks

FinBERT-based sentiment analysis

News-source credibility weighting

Earnings-calendar and analyst-estimate integration

Peer valuation comparisons

Saved reports and PDF export

Authentication and database-backed history

Docker and automated CI/CD

Scheduled data-provider monitoring

🎓 Project Highlights

This project demonstrates experience with:

Full-stack financial application development

FastAPI REST API design

Next.js and TypeScript dashboard development

Financial and macroeconomic data analysis

Machine-learning model deployment

Explainable weighted scoring

Multi-market symbol resolution

Provider retry, fallback, and caching strategies

Pydantic response validation

Automated pytest coverage

Render cloud deployment

Git and GitHub workflow

🔐 Security

Secrets are loaded from environment variables.

Provider errors are sanitized before reaching users.

API parameters and company inputs are validated.

Unresolved companies are rejected rather than scored.

CORS origins are explicitly configured.

Production credentials are managed in Render, not committed to Git.

⚖️ Disclaimer

This project is intended for educational, research, and analytical purposes only.

The Intelligence Score, sentiment classifications, fundamental metrics, technical indicators, macroeconomic analysis, and other information displayed by the platform should not be considered personal financial or investment advice.

The platform does not guarantee future performance or provide an automated recommendation to buy, hold, or sell a security. Users should conduct independent research and consult qualified financial professionals before making investment decisions.

👨‍💻 Author

Vinoth Ganesamurthy

GitHub: github.com/Vinoth-Ganesamurthy

LinkedIn: linkedin.com/in/vinoth-ganesamurthy

Developed as a full-stack financial analytics, machine-learning, and cloud-deployment portfolio project.

⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

GitHub Repository

Live Dashboard

API Documentation

📄 License

This project is licensed under the MIT License. See the LICENSE file for details.