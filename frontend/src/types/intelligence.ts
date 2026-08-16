export interface ModuleScore {
  score: number;
  is_available: boolean;
  quality_factor: number;
  weight: number;
  weighted_contribution: number | null;
  [key: string]: unknown;
}

export interface ModuleScores {
  fundamental: ModuleScore;
  technical: ModuleScore;
  sentiment: ModuleScore;
  historical: ModuleScore;
  sector_macro: ModuleScore;
}

export interface FinancialIntelligenceResponse {
  stock_symbol: string;
  company_name: string | null;
  sector: string | null;
  intelligence_score: number;
  classification: string;
  summary: string;
  coverage_ratio: number;
  confidence_score: number;
  module_scores: ModuleScores;
  analysis: Record<string, unknown>;
  errors: Record<string, string>;
  generated_at_utc: string;
  disclaimer: string;
}