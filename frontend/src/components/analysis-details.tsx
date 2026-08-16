import type {
  ReactNode,
} from "react";

type DataRecord = Record<string, unknown>;

function asRecord(value: unknown): DataRecord {
  if (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  ) {
    return value as DataRecord;
  }

  return {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function formatNumber(
  value: unknown,
  digits = 2,
) {
  if (typeof value !== "number") {
    return "N/A";
  }

  return value.toLocaleString("en-IN", {
    maximumFractionDigits: digits,
  });
}

function formatPercent(value: unknown) {
  if (typeof value !== "number") {
    return "N/A";
  }

  return `${formatNumber(value)}%`;
}

function formatCompactNumber(
  value: unknown,
  currency?: unknown,
) {
  if (typeof value !== "number") {
    return "N/A";
  }

  const formatted = new Intl.NumberFormat(
    "en",
    {
      notation: "compact",
      maximumFractionDigits: 2,
    },
  ).format(value);

  return currency
    ? `${String(currency)} ${formatted}`
    : formatted;
}

function formatText(value: unknown) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "N/A";
  }

  return String(value).replaceAll("_", " ");
}

function DetailSection({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-950">
          {title}
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          {description}
        </p>
      </div>

      {children}
    </section>
  );
}

function MetricTile({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-lg font-bold text-slate-900">
        {value}
      </p>
    </div>
  );
}

function MacroComponent({
  title,
  data,
}: {
  title: string;
  data: DataRecord;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="font-bold text-slate-900">
          {title}
        </h3>

        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold capitalize text-slate-600">
          {formatText(data.status)}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-600">
        {formatText(data.summary)}
      </p>

      <p className="mt-4 text-sm font-semibold text-blue-600">
        Score: {formatNumber(data.score)}
      </p>
    </article>
  );
}

export function AnalysisDetails({
  analysis,
}: {
  analysis: Record<string, unknown>;
}) {
  const historical = asRecord(
    analysis.historical,
  );
  const technical = asRecord(
    analysis.technical,
  );
  const fundamental = asRecord(
    analysis.fundamental,
  );
  const sentiment = asRecord(
    analysis.sentiment,
  );
  const sentimentFeatures = asRecord(
    sentiment.features,
  );
  const articles = asArray(
    sentiment.articles,
  ).map(asRecord);
  const macro = asRecord(analysis.macro);
  const macroAnalysis = asRecord(
    macro.analysis,
  );
  const sectorMacro = asRecord(
    analysis.sector_macro,
  );

  return (
    <div className="space-y-8">
      <DetailSection
        title="Fundamental Analysis"
        description="Company valuation, profitability, growth and financial-position metrics."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile
            label="Industry"
            value={formatText(
              fundamental.industry,
            )}
          />

          <MetricTile
            label="Market Cap"
            value={formatCompactNumber(
              fundamental.market_cap,
              fundamental.currency,
            )}
          />

          <MetricTile
            label="Revenue"
            value={formatCompactNumber(
              fundamental.total_revenue,
              fundamental.currency,
            )}
          />

          <MetricTile
            label="Forward P/E"
            value={formatNumber(
              fundamental.forward_pe,
            )}
          />

          <MetricTile
            label="Price to Book"
            value={formatNumber(
              fundamental.price_to_book,
            )}
          />

          <MetricTile
            label="Profit Margin"
            value={formatPercent(
              fundamental.profit_margin,
            )}
          />

          <MetricTile
            label="Return on Equity"
            value={formatPercent(
              fundamental.return_on_equity,
            )}
          />

          <MetricTile
            label="Revenue Growth"
            value={formatPercent(
              fundamental.revenue_growth,
            )}
          />

          <MetricTile
            label="Earnings Growth"
            value={formatPercent(
              fundamental.earnings_growth,
            )}
          />

          <MetricTile
            label="Debt to Equity"
            value={formatNumber(
              fundamental.debt_to_equity,
            )}
          />

          <MetricTile
            label="Free Cash Flow"
            value={formatCompactNumber(
              fundamental.free_cash_flow,
              fundamental.currency,
            )}
          />
        </div>
      </DetailSection>

      <DetailSection
        title="Technical Analysis"
        description="Price trend, momentum, volatility and volume indicators."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile
            label="Signal"
            value={formatText(technical.signal)}
          />

          <MetricTile
            label="Current Price"
            value={formatNumber(
              technical.current_price,
            )}
          />

          <MetricTile
            label="RSI"
            value={formatNumber(technical.rsi)}
          />

          <MetricTile
            label="SMA 20"
            value={formatNumber(
              technical.sma_20,
            )}
          />

          <MetricTile
            label="SMA 50"
            value={formatNumber(
              technical.sma_50,
            )}
          />

          <MetricTile
            label="SMA 200"
            value={formatNumber(
              technical.sma_200,
            )}
          />

          <MetricTile
            label="MACD"
            value={formatNumber(
              technical.macd,
              4,
            )}
          />

          <MetricTile
            label="MACD Signal"
            value={formatNumber(
              technical.macd_signal,
              4,
            )}
          />

          <MetricTile
            label="ATR"
            value={formatNumber(
              technical.atr,
            )}
          />

          <MetricTile
            label="Relative Volume"
            value={formatNumber(
              technical.relative_volume,
            )}
          />

          <MetricTile
            label="Bullish Points"
            value={formatNumber(
              technical.bullish_points,
              0,
            )}
          />

          <MetricTile
            label="Bearish Points"
            value={formatNumber(
              technical.bearish_points,
              0,
            )}
          />
        </div>
      </DetailSection>

      <DetailSection
        title="Historical Performance"
        description="Returns and risk calculated from historical market prices."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile
            label="Current Price"
            value={formatNumber(
              historical.current_price,
            )}
          />

          <MetricTile
            label="1 Week Return"
            value={formatPercent(
              historical.one_week_return,
            )}
          />

          <MetricTile
            label="1 Month Return"
            value={formatPercent(
              historical.one_month_return,
            )}
          />

          <MetricTile
            label="3 Month Return"
            value={formatPercent(
              historical.three_month_return,
            )}
          />

          <MetricTile
            label="6 Month Return"
            value={formatPercent(
              historical.six_month_return,
            )}
          />

          <MetricTile
            label="1 Year Return"
            value={formatPercent(
              historical.one_year_return,
            )}
          />

          <MetricTile
            label="Annualized Volatility"
            value={formatPercent(
              historical.annualized_volatility,
            )}
          />

          <MetricTile
            label="Maximum Drawdown"
            value={formatPercent(
              historical.maximum_drawdown,
            )}
          />

          <MetricTile
            label="Period High"
            value={formatNumber(
              historical.period_high,
            )}
          />

          <MetricTile
            label="Period Low"
            value={formatNumber(
              historical.period_low,
            )}
          />
        </div>
      </DetailSection>

      <DetailSection
        title="News Sentiment"
        description="Recent company-news sentiment produced by the trained financial sentiment model."
      >
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile
            label="Overall Sentiment"
            value={formatText(
              sentimentFeatures.overall_sentiment,
            )}
          />

          <MetricTile
            label="Sentiment Score"
            value={formatNumber(
              sentimentFeatures.sentiment_score,
            )}
          />

          <MetricTile
            label="Articles Analysed"
            value={formatNumber(
              sentimentFeatures.article_count,
              0,
            )}
          />

          <MetricTile
            label="Positive Ratio"
            value={
              typeof sentimentFeatures.positive_ratio ===
              "number"
                ? `${(
                    sentimentFeatures.positive_ratio * 100
                  ).toFixed(0)}%`
                : "N/A"
            }
          />
        </div>

        <div className="mt-6 space-y-3">
          {articles.length === 0 ? (
            <p className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">
              No relevant news articles were available.
            </p>
          ) : (
            articles.map((article, index) => {
              const url =
                typeof article.url === "string"
                  ? article.url
                  : null;

              const content = (
                <>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <h3 className="font-semibold text-slate-900">
                      {formatText(article.title)}
                    </h3>

                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold uppercase text-blue-700">
                      {formatText(
                        article.sentiment ??
                          article.prediction,
                      )}
                    </span>
                  </div>

                  <p className="mt-2 text-sm text-slate-500">
                    {formatText(
                      article.source ??
                        article.publisher,
                    )}
                  </p>
                </>
              );

              return url ? (
                <a
                  key={`${url}-${index}`}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="block rounded-2xl border border-slate-200 p-4 transition hover:border-blue-300 hover:bg-blue-50/30"
                >
                  {content}
                </a>
              ) : (
                <article
                  key={index}
                  className="rounded-2xl border border-slate-200 p-4"
                >
                  {content}
                </article>
              );
            })
          )}
        </div>
      </DetailSection>

      <DetailSection
        title="Macroeconomic Analysis"
        description={`${formatText(
          macro.country,
        )} macroeconomic conditions and their sector-specific impact.`}
      >
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricTile
            label="Country"
            value={formatText(macro.country)}
          />

          <MetricTile
            label="General Macro Score"
            value={formatNumber(
              macro.combined_macro_score,
            )}
          />

          <MetricTile
            label="Sector Macro Score"
            value={formatNumber(
              sectorMacro.sector_macro_score,
            )}
          />

          <MetricTile
            label="Macro Confidence"
            value={
              typeof macro.confidence_score ===
              "number"
                ? `${(
                    macro.confidence_score * 100
                  ).toFixed(0)}%`
                : "N/A"
            }
          />
        </div>

        <p className="mb-6 rounded-2xl bg-blue-50 p-4 text-sm leading-6 text-blue-900">
          {formatText(
            sectorMacro.outlook ?? macro.outlook,
          )}
        </p>

        <div className="grid gap-4 md:grid-cols-2">
          <MacroComponent
            title="Inflation"
            data={asRecord(
              macroAnalysis.inflation,
            )}
          />

          <MacroComponent
            title="GDP Growth"
            data={asRecord(
              macroAnalysis.gdp_growth,
            )}
          />

          <MacroComponent
            title="Unemployment"
            data={asRecord(
              macroAnalysis.unemployment,
            )}
          />

          <MacroComponent
            title="Monetary Environment"
            data={asRecord(
              macroAnalysis.monetary_environment,
            )}
          />
        </div>
      </DetailSection>
    </div>
  );
}