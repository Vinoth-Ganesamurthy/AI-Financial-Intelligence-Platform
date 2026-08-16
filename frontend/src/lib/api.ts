import type {
  FinancialIntelligenceResponse,
} from "@/types/intelligence";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000";

export async function fetchFinancialIntelligence(
  stockSymbol: string,
  newsLimit = 5,
): Promise<FinancialIntelligenceResponse> {
  const normalizedSymbol = stockSymbol
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("Please enter a stock symbol.");
  }

  const url =
    `${API_BASE_URL}/api/v1/intelligence/` +
    `${encodeURIComponent(normalizedSymbol)}` +
    `?news_limit=${newsLimit}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let message =
      `Request failed with status ${response.status}.`;

    try {
      const errorBody: { detail?: string } =
        await response.json();

      if (errorBody.detail) {
        message = errorBody.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json();
}