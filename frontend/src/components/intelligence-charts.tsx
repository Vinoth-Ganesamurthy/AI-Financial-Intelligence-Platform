"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  ModuleScores,
} from "@/types/intelligence";

type DataRecord = Record<string, unknown>;

const moduleLabels: Record<string, string> = {
  fundamental: "Fundamental",
  technical: "Technical",
  sentiment: "Sentiment",
  historical: "Historical",
  sector_macro: "Sector & Macro",
};

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

function ChartContainer({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-xl font-bold text-slate-950">
        {title}
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        {description}
      </p>

      <div className="mt-6 h-80 w-full">
        {children}
      </div>
    </article>
  );
}

export function IntelligenceCharts({
  intelligenceScore,
  coverageRatio,
  confidenceScore,
  moduleScores,
  analysis,
}: {
  intelligenceScore: number;
  coverageRatio: number;
  confidenceScore: number;
  moduleScores: ModuleScores;
  analysis: Record<string, unknown>;
}) {
  const boundedScore = Math.max(
    -1,
    Math.min(1, intelligenceScore),
  );

  const scorePosition =
    ((boundedScore + 1) / 2) * 100;
  const historical = asRecord(
    analysis.historical,
  );

  const moduleData = Object.entries(
    moduleScores,
  ).map(([name, module]) => ({
    name: moduleLabels[name] ?? name,
    score: module.is_available
      ? module.score
      : 0,
  }));

  const historicalData = [
    {
      period: "1 Week",
      value: historical.one_week_return,
    },
    {
      period: "1 Month",
      value: historical.one_month_return,
    },
    {
      period: "3 Months",
      value: historical.three_month_return,
    },
    {
      period: "6 Months",
      value: historical.six_month_return,
    },
    {
      period: "1 Year",
      value: historical.one_year_return,
    },
  ].filter(
    (
      item,
    ): item is {
      period: string;
      value: number;
    } => typeof item.value === "number",
  );

  return (
    <section>
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-slate-950">
          Intelligence Visuals
        </h2>

        <p className="mt-1 text-slate-500">
          Visual comparison of analysis scores and
          historical stock returns.
        </p>
      </div>
<article className="mb-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
  <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
    <div>
      <h3 className="text-xl font-bold text-slate-950">
        Overall Intelligence Score
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        Combined weighted assessment from -1 to +1.
        This is not a predicted investment return.
      </p>

      <p className="mt-3 text-4xl font-bold text-slate-950">
        {intelligenceScore.toFixed(3)}
      </p>
    </div>

    <div className="grid grid-cols-2 gap-3">
        <MetricSummary
        label="Coverage"
        value={`${(coverageRatio * 100).toFixed(0)}%`}
      />

        <MetricSummary
        label="Confidence"
        value={`${(confidenceScore * 100).toFixed(0)}%`}
      />
    </div>
  </div>

  <div className="mt-7">
    <div className="relative">
      <div
        className="h-3 rounded-full"
        style={{
          background:
            "linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%)",
        }}
      />

      <div
        className="absolute top-1/2 h-6 w-6 -translate-x-1/2 -translate-y-1/2 rounded-full border-4 border-white bg-slate-950 shadow"
        style={{
          left: `${scorePosition}%`,
        }}
      />
    </div>

    <div className="mt-3 flex justify-between text-xs font-semibold text-slate-500">
      <span>-1 Unfavourable</span>
      <span>0 Neutral</span>
      <span>+1 Favourable</span>
    </div>
  </div>
</article>
      <div className="grid gap-6 xl:grid-cols-2">
        <ChartContainer
          title="Module Score Comparison"
          description="Normalized scores from the five intelligence modules."
        >
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <BarChart
              data={moduleData}
              margin={{
                top: 10,
                right: 10,
                left: -20,
                bottom: 35,
              }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                vertical={false}
                stroke="#e2e8f0"
              />

              <XAxis
                dataKey="name"
                angle={-20}
                textAnchor="end"
                interval={0}
                tick={{
                  fill: "#64748b",
                  fontSize: 12,
                }}
              />

              <YAxis
                domain={[-1, 1]}
                tick={{
                  fill: "#64748b",
                  fontSize: 12,
                }}
              />

              <Tooltip />

              <ReferenceLine
                y={0}
                stroke="#94a3b8"
              />

              <Bar
                dataKey="score"
                radius={[6, 6, 0, 0]}
              >
                {moduleData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={
                      entry.score >= 0
                        ? "#2563eb"
                        : "#ef4444"
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartContainer>

        <ChartContainer
          title="Historical Returns"
          description="Percentage price return across available periods."
        >
          {historicalData.length > 0 ? (
            <ResponsiveContainer
              width="100%"
              height="100%"
            >
              <BarChart
                data={historicalData}
                margin={{
                  top: 10,
                  right: 10,
                  left: -10,
                  bottom: 20,
                }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e2e8f0"
                />

                <XAxis
                  dataKey="period"
                  tick={{
                    fill: "#64748b",
                    fontSize: 12,
                  }}
                />

                <YAxis
                  unit="%"
                  tick={{
                    fill: "#64748b",
                    fontSize: 12,
                  }}
                />

                <Tooltip />

                <ReferenceLine
                  y={0}
                  stroke="#94a3b8"
                />

                <Bar
                  dataKey="value"
                  name="Return"
                  unit="%"
                  radius={[6, 6, 0, 0]}
                >
                  {historicalData.map((entry) => (
                    <Cell
                      key={entry.period}
                      fill={
                        entry.value >= 0
                          ? "#10b981"
                          : "#ef4444"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-full items-center justify-center text-sm text-slate-500">
              Historical returns are unavailable.
            </div>
          )}
        </ChartContainer>
      </div>
    </section>
  );
}
function MetricSummary({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="min-w-32 rounded-2xl bg-slate-50 px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-xl font-bold text-slate-950">
        {value}
      </p>
    </div>
  );
}