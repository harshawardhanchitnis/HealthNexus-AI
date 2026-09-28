export interface ForecastMetric {
  mae: number;
  rmse: number;
  wape: number | null;
  samples: number;
}
export interface Coverage {
  coverage: number;
  mean_width: number;
  samples: number;
  calibration_paths: number;
}
export interface Forecast {
  country_id: string;
  facility_id: string;
  resource_id: string;
  target: string;
  horizon: number;
  as_of: string;
  unit: string;
  history: { date: string; value: number }[];
  forecast: {
    date: string;
    point: number;
    lower80: number;
    upper80: number;
    lower95: number;
    upper95: number;
  }[];
  summary: {
    latest_demand: number;
    recent_daily_mean: number;
    forecast_daily_mean: number;
    forecast_total: number;
    change_percent: number | null;
    total_lower80: number;
    total_upper80: number;
    total_lower95: number;
    total_upper95: number;
  };
  provenance: {
    operational_profile: 'constrained' | 'redistribution-ready';
    profile_version: string;
    model_sha256: string;
    operational_history_sha256: string;
    data_type: string;
    model_version: string;
    model: string;
    trained_through: string;
    evaluated_at: string;
    windows: Record<string, { start: string; end: string }>;
    history_sha256: string;
    calibration_sources: unknown[];
    source_vintage_note: string;
    uncertainty_method: string;
  };
  test_metric: ForecastMetric;
  coverage: Record<string, Coverage>;
  explanations: string[];
  stockout: null | {
    current_stock: number;
    safety_stock: number;
    days_of_cover: number | null;
    cover_method: string;
    safety_breach_date: string | null;
    stockout_date: string | null;
    probabilities: Record<string, number>;
    simulations: number;
    status: string;
    method: string;
    trajectory: {
      date: string;
      expected_receipts: number;
      demand: number;
      closing_stock: number;
      unmet_demand: number;
      lower95: number;
      upper95: number;
    }[];
  };
}
export interface Performance {
  country_id: string;
  model_version: string;
  evaluated_at: string;
  data_type: string;
  selection_rule: string;
  uncertainty_method: string;
  source_vintage_note: string;
  windows: Record<string, { start: string; end: string }>;
  targets: Record<
    string,
    {
      champion: string;
      models: Record<
        string,
        {
          selection: ForecastMetric;
          test: ForecastMetric;
          test_by_horizon: Record<string, ForecastMetric>;
        }
      >;
      coverage: Record<string, Record<string, Coverage>>;
      train_rows: number;
      test_rows: number;
    }
  >;
}
