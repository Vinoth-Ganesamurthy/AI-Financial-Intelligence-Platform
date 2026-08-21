AI Financial Intelligence Platform

A full-stack financial research application that combines fundamental analysis, technical indicators, historical stock performance, machine-learning-based news sentiment, and country-aware macroeconomic analysis in a responsive web dashboard.

The application allows users to search using a company name or stock symbol, resolves the listed company, collects data from multiple financial sources, evaluates five independent analysis modules, and generates an explainable Intelligence Score with coverage and confidence indicators.

The platform supports companies across multiple international markets, including the United States, India, Singapore, and Australia.

🌐 Live Application

🚀 Live Dashboard

👉 https://ai-financial-intelligence-platform-m9jl.onrender.com

📚 FastAPI Swagger Documentation

👉 https://ai-financial-intelligence-platform-api.onrender.com/docs

⚙️ Backend API

👉 https://ai-financial-intelligence-platform-api.onrender.com

❤️ Health Check

👉 https://ai-financial-intelligence-platform-api.onrender.com/health

Note: The application is hosted on Render. If the free backend instance has been inactive, the first request can take approximately 50 seconds or longer while the service starts. Subsequent requests should be faster.

📌 Project Overview

Investment research usually requires information from several independent sources. A user may need to review company fundamentals, technical signals, historical risk, recent news, and the broader economic environment before forming a view.

This project brings those areas together in one automated workflow that:

Accepts a company name or stock symbol from the user.

Resolves company names to supported exchange symbols.

Validates that the listed company exists.

Retrieves historical OHLCV market data.

Calculates technical indicators and historical risk metrics.

Retrieves and normalizes company fundamental data.

Fetches, filters, and deduplicates relevant financial news.

Uses a trained machine-learning model to classify article sentiment.

Retrieves country-specific macroeconomic indicators.

Adjusts macroeconomic effects according to the company sector.

Normalizes all module results to a common -1 to +1 scale.

Produces a weighted Intelligence Score, classification, coverage, and confidence.

Presents the complete analysis through a Next.js dashboard.

The system is intentionally explainable. It displays the individual module scores, weights, weighted contributions, data availability, and underlying metrics instead of returning an unexplained prediction.

✨ Key Features

🏢 Fundamental Analysis

The application evaluates company financial strength using metrics such as:

Market capitalization

Total revenue

Trailing and forward price-to-earnings ratios

Price-to-book ratio

Profit margin

Return on equity

Return on assets

Revenue growth

Earnings growth

Debt-to-equity ratio

Free cash flow

Fundamental data uses multiple retrieval paths so the report can continue when a primary provider is unavailable or rate-limited.

📈 Technical Analysis

The technical-analysis module calculates:

20-day, 50-day, and 200-day simple moving averages

12-day and 26-day exponential moving averages

Relative Strength Index (RSI)

Moving Average Convergence Divergence (MACD)

MACD signal and histogram

Bollinger Bands

Average True Range (ATR)

Current and average trading volume

Relative volume

Bullish and bearish signal points

These indicators are combined into a normalized technical score and an interpretable technical signal.

📰 Financial News Retrieval

The application retrieves recent company-related news using NewsAPI.

The news pipeline includes:

Company-specific search-name generation

Symbol and company-term matching

Headline and description relevance scoring

Low-quality headline filtering

Duplicate-title and duplicate-URL removal

Retry handling for temporary connection failures

Configurable article limits

Only sufficiently relevant articles are sent to the sentiment model.

🤖 Machine-Learning Sentiment Analysis

Financial headlines are classified into three sentiment categories:

🟢 Positive

🟡 Neutral

🔴 Negative

The sentiment pipeline uses:

TF-IDF text vectorization

A trained scikit-learn classification model

Label encoding

Saved model artifacts loaded with Joblib

The model produces article-level classifications and an overall company-news sentiment summary.

📊 Historical Stock Performance

The historical-analysis module calculates:

Current Price

1-Week Return

1-Month Return

3-Month Return

6-Month Return

1-Year Return

Annualized Volatility

Maximum Drawdown

Period High

Period Low

These metrics help users understand recent performance, variability, and downside risk.

🌎 Country-Aware Macroeconomic Analysis

The platform evaluates the economic environment associated with the stock's market using:

Inflation

GDP growth

Unemployment

Monetary or policy rates

A real-rate proxy

Country-specific frameworks are configured for the United States, India, Singapore, and Australia. The macro module reports the source quality, availability, classification, and component contribution for each indicator.

🏭 Sector-Sensitive Macro Impact

Macroeconomic conditions do not affect every industry equally.

The platform applies sector-specific weights to inflation, growth, unemployment, and monetary conditions. For example, interest-rate changes can receive a larger weight for rate-sensitive sectors, while economic growth may receive a larger weight for cyclical sectors.

If the company sector cannot be identified, the application uses transparent default weights and marks that fallback in the response.

🧠 Explainable Intelligence Score

The five analytical modules contribute to a combined score:

Module

Weight

Purpose

Fundamental

30%

Financial quality, valuation, growth, and leverage

Technical

20%

Trend, momentum, volatility, and volume

Sentiment

15%

Recent company-news sentiment

Historical

15%

Return and risk characteristics

Sector & Macro

20%

Economic conditions adjusted for sector sensitivity

Each module uses a normalized range from -1 to +1:

-1.0  → Strongly unfavourable
 0.0  → Neutral or balanced
+1.0  → Strongly favourable

When a module is unavailable, the final result is recalculated using the available weights. The dashboard separately displays:

Intelligence Score

Overall classification

Coverage ratio

Confidence score

Module availability

Module quality factor

Weighted contribution

The Intelligence Score is an analytical research indicator. It is not a guaranteed forecast or a direct buy/sell recommendation.

🏗️ System Architecture

The application follows a full-stack, service-oriented architecture.

┌───────────────────────────────────────────────┐
│                Next.js Frontend               │
│                                               │
│ Company Search       Intelligence Summary     │
│ Module Cards         Charts and Metrics       │
│ Detailed Analysis    Partial-Data Warnings    │
└───────────────────────┬───────────────────────┘
                        │ HTTP / JSON
                        ▼
┌───────────────────────────────────────────────┐
│                FastAPI Backend                │
│                                               │
│ Input Validation      Response Schemas        │
│ Company Resolution    Error Handling          │
│ CORS Configuration    OpenAPI Documentation   │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│          Financial Intelligence Engine        │
│                                               │
│ Fundamental          Technical                │
│ Sentiment            Historical               │
│ Sector & Macro       Weighted Aggregation     │
└───────────────┬─────────────────┬─────────────┘
                │                 │
                ▼                 ▼
        External Data APIs    ML Model Artifacts

🧰 Technology Stack

Frontend

Next.js 16

React

TypeScript

Tailwind CSS

Recharts

Backend

Python 3.12

FastAPI

Uvicorn

Requests

curl-cffi

python-dotenv

Data Analysis and Machine Learning

pandas

NumPy

scikit-learn

TF-IDF Vectorization

Joblib

yfinance

Financial and Macroeconomic Data

Yahoo Finance

Finnhub

NewsAPI

FRED

MoSPI eSankhyiki

Reserve Bank of India

SingStat

World Bank

Testing and Deployment

pytest

FastAPI TestClient

Render Web Service

Render Static Site

GitHub

📁 Project Structure

AI-Financial-Intelligence-Platform/
│
├── frontend/                         # Next.js dashboard
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── types/
│   ├── next.config.ts
│   └── package.json
│
├── models/                           # Trained sentiment artifacts
│   ├── sentiment_model.pkl
│   ├── tfidf_vectorizer.pkl
│   └── label_encoder.pkl
│
├── src/
│   ├── analysis/
│   │   ├── fundamental/
│   │   ├── historical/
│   │   ├── intelligence/
│   │   ├── macro/
│   │   ├── sentiment/
│   │   └── technical/
│   ├── api/                          # FastAPI app and schemas
│   └── data/                         # Company, market, and macro services
│
├── tests/                            # Unit and API tests
├── requirements.txt
├── .python-version
└── README.md

🔌 API Endpoints

Interactive API documentation is available at:

https://ai-financial-intelligence-platform-api.onrender.com/docs

API Status

GET /

Returns the application name, version, running status, and documentation path.

Example:

{
  "name": "AI Financial Intelligence Platform",
  "version": "1.0.0",
  "status": "running",
  "documentation": "/docs"
}

Health Check

GET /health

Used by users and Render to confirm that the backend service is healthy.

Example:

{
  "status": "healthy"
}

Generate Financial Intelligence

GET /api/v1/intelligence/{stock_symbol}

Query parameter:

Parameter

Type

Description

news_limit

Integer

Maximum number of relevant news articles to analyze

Examples:

GET /api/v1/intelligence/AAPL?news_limit=5
GET /api/v1/intelligence/INFY.NS?news_limit=5
GET /api/v1/intelligence/Tesla?news_limit=5

The response contains:

Resolved stock symbol

Company name and sector

Intelligence Score and classification

Coverage and confidence

Five module scores

Module weights and contributions

Detailed analysis data

Partial-data warnings

Generation timestamp

Research disclaimer

🛡️ Resilient Data Retrieval Strategy

External financial providers can be rate-limited, unavailable, or restricted by subscription level. The platform therefore uses layered data retrieval and reports partial-data warnings instead of silently generating misleading values.

Market Data

Stock Symbol
     ↓
yfinance Historical Data
     ↓ unavailable or rate-limited
Direct Yahoo Finance Chart API
     ↓
Clean OHLCV DataFrame

The fallback retains the same Open, High, Low, Close, and Volume structure required by the technical and historical modules.

Fundamental Data

Stock Symbol
     ↓
yfinance Company Information
     ↓ unavailable or rate-limited
Finnhub Profile and Metrics
     ↓ unavailable or market-restricted
Direct Yahoo Search and Time-Series Data
     ↓
Normalized Fundamental Metrics

The direct Yahoo fallback supports international securities such as NSE-listed stocks and performs currency normalization where required.

Financial News

Company Name + Symbol
          ↓
       NewsAPI
          ↓
  Relevance Scoring
          ↓
  Duplicate Removal
          ↓
  Selected Articles
          ↓
 TF-IDF + ML Classifier
          ↓
Positive / Neutral / Negative

Transient NewsAPI connection failures use retry handling before the sentiment module is marked unavailable.

Macroeconomic Data

Official sources are preferred wherever possible:

United States: FRED

India: MoSPI CPI, PLFS, NAS, and Reserve Bank of India

Singapore: SingStat and configured official sources

Australia: Configured official sources

Fallback: World Bank annual indicators where appropriate

Successful official observations are cached so temporary source outages do not automatically remove macro coverage.

📐 Intelligence Calculations

Weighted Module Contribution

Weighted Contribution = Module Score × Module Weight

Example:

Fundamental Score     = 0.800
Fundamental Weight    = 0.300
Weighted Contribution = 0.240

Final Intelligence Score

                         Sum of Available Weighted Contributions
Intelligence Score = ------------------------------------------------
                              Sum of Available Module Weights

This prevents an unavailable provider from being treated as a negative investment signal.

Coverage Ratio

Coverage Ratio = Sum of Available Module Weights

A coverage value of 1.0 means all five analytical modules are available.

Confidence Score

Confidence considers both coverage and the quality of the available inputs. Examples include:

Number of relevant news articles

Official versus fallback macro data

Fundamental metric availability

Market-history availability

Sector identification

Historical Return

             Current Price - Previous Price
Return (%) = ------------------------------ × 100
                       Previous Price

Annualized Volatility

Annualized volatility estimates the variability of daily returns over a trading year. Higher values generally indicate larger price fluctuations.

Maximum Drawdown

Maximum drawdown measures the largest decline from a historical peak to a subsequent trough during the analyzed period. It provides a simple measure of downside risk.

🌍 Multi-Market Support

The application has been tested with companies from multiple stock exchanges.

Market

Example Companies

Example Symbols

🇺🇸 United States

Apple, Tesla, NVIDIA

AAPL, TSLA, NVDA

🇮🇳 India

Reliance Industries, Infosys, TCS

RELIANCE.NS, INFY.NS, TCS.NS

🇸🇬 Singapore

DBS Group, ST Engineering

D05.SI, S63.SI

🇦🇺 Australia

BHP, Commonwealth Bank

BHP.AX, CBA.AX

Users can search with either a symbol or a company name. Examples:

AAPL
Tesla
INFY.NS
Tata Consultancy Services
DBS Group
BHP.AX

🔄 Application Flow

                         USER
                           │
                           ▼
                 Next.js Web Dashboard
                           │
                  Company Name / Symbol
                           ▼
                    FastAPI Backend
                           │
                           ▼
               Company & Symbol Resolution
                           │
                           ▼
              Financial Intelligence Engine
                           │
       ┌──────────┬────────┼────────┬──────────┐
       │          │        │        │          │
       ▼          ▼        ▼        ▼          ▼
 Fundamental  Technical  Sentiment Historical  Macro
   Analysis   Analysis   Analysis   Analysis   Analysis
       │          │        │        │          │
       └──────────┴────────┼────────┴──────────┘
                           │
                           ▼
                Normalized Module Scores
                           │
                           ▼
               Weighted Intelligence Score
                           │
                           ▼
       Classification + Coverage + Confidence
                           │
                           ▼
                    JSON API Response
                           │
                           ▼
                 Interactive Dashboard

💻 Local Installation

1. Clone the Repository

git clone https://github.com/Vinoth-Ganesamurthy/AI-Financial-Intelligence-Platform.git
cd AI-Financial-Intelligence-Platform

2. Create a Python Virtual Environment

Windows PowerShell:

python -m venv .venv
.venv\Scripts\Activate.ps1

macOS/Linux:

python3 -m venv .venv
source .venv/bin/activate

3. Install Backend Dependencies

python -m pip install --upgrade pip
pip install -r requirements.txt

4. Configure Backend Environment Variables

Create a .env file in the project root:

FRED_API_KEY=your_fred_api_key
NEWS_API_KEY=your_newsapi_key
FINNHUB_API_KEY=your_finnhub_api_key
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

Never commit the .env file or API keys to GitHub.

5. Start the FastAPI Backend

From the project root:

python -m uvicorn src.api.main:app --reload

The backend will run locally at:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

6. Install Frontend Dependencies

Open another terminal:

cd frontend
npm ci

7. Configure the Frontend API URL

Create frontend/.env.local:

NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000

8. Start the Next.js Frontend

npm run dev

The frontend will normally run at:

http://localhost:3000

⚙️ Frontend API Configuration

The frontend uses an environment-based backend URL:

NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.com

For production, the deployed static site communicates with the Render-hosted FastAPI backend using this variable at build time.

The frontend API helper also provides a local default:

http://127.0.0.1:8000

🔐 Security

API credentials are stored using environment variables.

The project .env and frontend .env.local files should remain excluded through .gitignore.

Production API keys are configured directly through Render environment variables rather than being committed to the repository.

Required backend variables:

FRED_API_KEY=...
NEWS_API_KEY=...
FINNHUB_API_KEY=...
FRONTEND_ORIGINS=...

Frontend production variable:

NEXT_PUBLIC_API_BASE_URL=https://ai-financial-intelligence-platform-api.onrender.com

Additional safeguards include:

Sanitized provider errors

Validated API query parameters

Rejection of unresolved stock inputs

Explicitly configured CORS origins

No secrets stored in frontend code

🚀 Production Deployment

Backend

The FastAPI backend is deployed as a Render Web Service.

Root directory:

Repository root

Build command:

pip install -r requirements.txt

Start command:

python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT

Health-check path:

/health

Backend:

https://ai-financial-intelligence-platform-api.onrender.com

Swagger:

https://ai-financial-intelligence-platform-api.onrender.com/docs

Frontend

The Next.js application is deployed as a Render Static Site using static export mode.

Root directory:

frontend

Build command:

npm ci && npm run build

Publish directory:

out

Production environment variable:

NEXT_PUBLIC_API_BASE_URL=https://ai-financial-intelligence-platform-api.onrender.com

Live dashboard:

https://ai-financial-intelligence-platform-m9jl.onrender.com

🌐 CORS Configuration

Because the frontend and backend are deployed separately, the FastAPI backend allows requests from configured frontend origins.

Development origins include:

http://localhost:3000
http://127.0.0.1:3000
http://localhost:3001
http://127.0.0.1:3001

Production origin:

https://ai-financial-intelligence-platform-m9jl.onrender.com

Additional origins can be supplied through the comma-separated FRONTEND_ORIGINS environment variable.

🧪 Testing

Run the backend test suite from the repository root:

python -m pytest -q

Current verified result:

26 passed

The suite covers:

Individual intelligence-module scoring

Complete financial-intelligence aggregation

FastAPI routes and validation

Company-name and acronym lookup

Invalid-company rejection

United States macro-data resilience

India GDP and policy-rate retrieval

Verified MoSPI connectivity

Provider outage and cache behavior

Build and type-check the frontend:

cd frontend
npm run build

The production build generates the static out directory used by Render.

🧪 Example Companies to Test

Try the live application with:

Apple
Tesla
NVIDIA
Reliance Industries
Infosys
Tata Consultancy Services
DBS Group
BHP
Commonwealth Bank

These examples demonstrate company-name resolution and the platform's multi-market capabilities.

📊 Example Workflow

Searching for:

Infosys

produces a workflow similar to:

Infosys
   ↓
INFY.NS
   ↓
Company Validation
   ↓
Historical Market Data
   ├── Technical Indicators
   └── Historical Risk and Return

Fundamental Data
   ↓
Valuation, Profitability, Growth, and Leverage

NewsAPI
   ↓
Infosys-Relevant Articles
   ↓
ML Sentiment Classification

India Macro Sources
   ↓
Inflation + GDP + Unemployment + RBI Policy Rate
   ↓
Technology-Sector Macro Impact

All Five Module Scores
   ↓
Weighted Intelligence Score
   ↓
Coverage + Confidence + Detailed Dashboard

⚠️ Limitations

The application has several practical limitations:

Financial-data providers can impose rate limits or temporary access restrictions.

Some fallback sources expose fewer metrics than the primary provider.

News availability depends on NewsAPI coverage and the selected article limit.

A company may have fewer relevant recent articles than requested.

Sentiment classifications do not necessarily predict future price movement.

Historical performance does not guarantee future returns.

Country and sector thresholds are analytical classifications, not official forecasts.

The project currently focuses on four configured market contexts.

Free Render services may require a startup period after inactivity.

When a non-critical module fails, the application reports reduced coverage and displays the provider issue under Partial data warnings.

🔮 Future Improvements

Potential future enhancements include:

Interactive candlestick and long-term price charts

Sentiment trends over time

Side-by-side company comparison

Portfolio analysis and watchlists

Additional international exchanges

Larger company-symbol reference data

Transformer-based sentiment models such as FinBERT

Article-level sentiment confidence

News-source credibility weighting

Earnings-calendar integration

Analyst-estimate and target-price analysis

Valuation comparison against sector peers

User authentication

Saved reports and database-backed history

PDF report export

Docker deployment

Automated CI/CD workflows

Scheduled provider-health monitoring

Automated model evaluation and retraining

🎓 Project Highlights

This project demonstrates practical experience with:

Full-stack financial application development

REST API development with FastAPI

Next.js and TypeScript frontend development

Responsive dashboard design

Machine-learning model integration

NLP-based financial sentiment analysis

Fundamental and technical analysis

Financial risk and return calculations

Country-aware macroeconomic analysis

Sector-sensitive economic scoring

Explainable weighted scoring systems

External financial API integration

Multi-market stock-symbol handling

Company-name and acronym resolution

Data normalization and currency conversion

Provider fallback, retry, and caching strategies

Pydantic response validation

Automated testing with pytest

Environment-variable and CORS management

Git and GitHub version control

Full-stack cloud deployment with Render

⚖️ Disclaimer

This project is intended for educational, research, and analytical purposes only.

The Intelligence Score, sentiment classifications, fundamental metrics, technical indicators, macroeconomic analysis, and other information displayed by the application should not be considered personal financial or investment advice.

The platform does not guarantee future performance or provide an automated recommendation to buy, hold, or sell any security.

Users should conduct independent research and consult qualified financial professionals before making investment decisions.

👨‍💻 Author

Vinoth Ganesamurthy

GitHub

https://github.com/Vinoth-Ganesamurthy

LinkedIn

https://www.linkedin.com/in/vinoth-ganesamurthy/

Developed as a full-stack financial analytics, machine-learning, and cloud-deployment portfolio project.

⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

GitHub Repository

https://github.com/Vinoth-Ganesamurthy/AI-Financial-Intelligence-Platform

Live Demo

https://ai-financial-intelligence-platform-m9jl.onrender.com

API Documentation

https://ai-financial-intelligence-platform-api.onrender.com/docs

📄 License

See the repository's LICENSE file for the applicable license terms.