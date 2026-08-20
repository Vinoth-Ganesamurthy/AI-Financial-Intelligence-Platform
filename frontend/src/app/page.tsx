"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  fetchFinancialIntelligence,
} from "@/lib/api";

import {
  AnalysisDetails,
} from "@/components/analysis-details";

import type {
  FinancialIntelligenceResponse,
  ModuleScore,
} from "@/types/intelligence";

import {
  IntelligenceCharts,
} from "@/components/intelligence-charts";

const moduleNames: Record<string, string> = {
  fundamental: "Fundamental",
  technical: "Technical",
  sentiment: "Sentiment",
  historical: "Historical",
  sector_macro: "Sector & Macro",
};

function scorePosition(score: number) {
  return Math.max(
    0,
    Math.min(100, ((score + 1) / 2) * 100),
  );
}

function ModuleCard({
  name,
  module,
}: {
  name: string;
  module: ModuleScore;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500">
            {moduleNames[name] ?? name}
          </p>

          <p className="mt-1 text-2xl font-bold text-slate-900">
            {module.is_available
              ? module.score.toFixed(3)
              : "N/A"}
          </p>
        </div>

        <span
          className={
            module.is_available
              ? "rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700"
              : "rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500"
          }
        >
          {module.is_available
            ? "Available"
            : "Unavailable"}
        </span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-blue-600 transition-all"
          style={{
            width: `${
              module.is_available
                ? scorePosition(module.score)
                : 0
            }%`,
          }}
        />
      </div>

      <div className="mt-4 flex justify-between text-xs text-slate-500">
        <span>
          Weight: {(module.weight * 100).toFixed(0)}%
        </span>

        <span>
          Contribution:{" "}
          {module.weighted_contribution === null
            ? "N/A"
            : module.weighted_contribution.toFixed(3)}
        </span>
      </div>
    </article>
  );
}

export default function Home() {
  const [symbol, setSymbol] = useState("");
  const [result, setResult] =
    useState<FinancialIntelligenceResponse | null>(
      null,
    );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
  event: FormEvent<HTMLFormElement>,
) {
  event.preventDefault();

  const normalizedSymbol = symbol
    .trim()
    .toUpperCase();

  const validSymbolPattern =
  /^[A-Z0-9][A-Z0-9&-]{0,19}(?:\.(?:NS|BO|SI|AX))?$/;

const validCompanyNamePattern =
  /^[A-Z0-9][A-Z0-9 .&'()-]{1,79}$/;

const isValidSearch =
  validSymbolPattern.test(normalizedSymbol) ||
  validCompanyNamePattern.test(normalizedSymbol);

  setError("");

  if (!normalizedSymbol) {
    setResult(null);
    setError("Please enter a stock symbol.");
    return;
  }

  if (!isValidSearch) {
    setResult(null);
    setError(
     "Enter one company name or stock symbol only.",
);
    return;
  }

  setSymbol(normalizedSymbol);
  setLoading(true);

  try {
    const response =
      await fetchFinancialIntelligence(
        normalizedSymbol,
      );

    setResult(response);
  } catch (requestError) {
    setResult(null);

    setError(
      requestError instanceof Error
        ? requestError.message
        : "Unable to complete the analysis.",
    );
  } finally {
    setLoading(false);
  }
}

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">
            Investment Research Dashboard
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            AI Financial Intelligence Platform
          </h1>

          <p className="mt-2 max-w-3xl text-slate-600">
            Combine fundamental, technical, sentiment,
            historical and country-aware macroeconomic
            analysis in one report.
          </p>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10">
        <section className="rounded-3xl bg-slate-950 p-6 text-white shadow-xl sm:p-8">
          <h2 className="text-xl font-semibold">
            Analyse a listed company
          </h2>

          <p className="mt-2 text-sm text-slate-300">
            Examples: AAPL, RELIANCE.NS, D05.SI or
            BHP.AX
          </p>

          <form
            onSubmit={handleSubmit}
            className="mt-6 flex flex-col gap-3 sm:flex-row"
          >
            <input
              type="text"
              value={symbol}
              onChange={(event) =>
                setSymbol(event.target.value)
              }
              placeholder="Enter stock symbol"
              className="min-h-12 flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 text-white outline-none transition placeholder:text-slate-500 focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
            />

            <button
              type="submit"
              disabled={loading}
              className="min-h-12 rounded-xl bg-blue-600 px-7 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading
                ? "Analysing..."
                : "Generate Intelligence"}
            </button>
          </form>
        </section>

        {error && (
          <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-8">
            <section className="grid gap-5 lg:grid-cols-[1.4fr_0.6fr]">
              <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-blue-600">
                      {result.stock_symbol}
                    </p>

                    <h2 className="mt-1 text-3xl font-bold text-slate-950">
                      {result.company_name ??
                        result.stock_symbol}
                    </h2>

                    <p className="mt-2 text-slate-500">
                      {result.sector ??
                        "Sector unavailable"}
                    </p>
                  </div>

                  <span className="rounded-full bg-blue-50 px-4 py-2 text-sm font-semibold capitalize text-blue-700">
                    {result.classification.replaceAll(
                      "_",
                      " ",
                    )}
                  </span>
                </div>

                <p className="mt-6 leading-7 text-slate-600">
                  {result.summary}
                </p>
              </div>

              <div className="rounded-3xl bg-blue-600 p-7 text-white shadow-lg">
                <p className="text-sm font-medium text-blue-100">
                  Intelligence Score
                </p>

                <p className="mt-2 text-5xl font-bold">
                  {result.intelligence_score.toFixed(3)}
                </p>
                <p className="mt-2 text-sm font-medium text-blue-100">
                  Scale: -1.000 to +1.000
                </p>

                <p className="mt-1 text-xs text-blue-100">
                  Neutral range: above -0.200 and below +0.200
                </p>

                <p className="mt-1 text-xs text-blue-100">
                  Higher scores indicate more favourable overall
                  conditions.
                </p>
                <div className="mt-7 space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-blue-100">
                      Coverage
                    </span>
                    <span className="font-semibold">
                      {(result.coverage_ratio * 100).toFixed(
                        0,
                      )}
                      %
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-blue-100">
                      Confidence
                    </span>
                    <span className="font-semibold">
                      {(
                        result.confidence_score * 100
                      ).toFixed(0)}
                      %
                    </span>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <div className="mb-5">
                <h2 className="text-2xl font-bold text-slate-950">
                  Analysis Modules
                </h2>

              <p className="mt-1 text-slate-500">
               Individual module scores range from -1 to +1.
               Negative values weaken the combined score, while
               positive values strengthen it.
              </p>
              </div>

              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(
                  result.module_scores,
                ).map(([name, module]) => (
                  <ModuleCard
                    key={name}
                    name={name}
                    module={module}
                  />
                ))}
              </div>
            </section>
            <IntelligenceCharts
              intelligenceScore={result.intelligence_score}
              coverageRatio={result.coverage_ratio}
              confidenceScore={result.confidence_score}
              moduleScores={result.module_scores}
              analysis={result.analysis}
             />
            <AnalysisDetails analysis={result.analysis} />

            {Object.keys(result.errors).length > 0 && (
              <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
                <h2 className="font-semibold text-amber-900">
                  Partial data warnings
                </h2>

                <ul className="mt-3 space-y-2 text-sm text-amber-800">
                  {Object.entries(result.errors).map(
                    ([module, message]) => (
                      <li key={module}>
                        <strong>{module}:</strong>{" "}
                        {message}
                      </li>
                    ),
                  )}
                </ul>
              </section>
            )}

            <footer className="border-t border-slate-200 pt-6 text-sm text-slate-500">
              {result.disclaimer}
            </footer>
          </div>
        )}
      </div>
    </main>
  );
}