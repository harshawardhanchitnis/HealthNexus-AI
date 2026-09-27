import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Forecast, Performance } from './forecast-models';
import {
  ScenarioDefinition,
  ScenarioMetadata,
  ScenarioResult,
  WarningList,
} from './resilience-models';
import {
  Alert,
  District,
  Facility,
  FacilityList,
  Overview,
  Region,
  Supply,
  Country,
  SourcesResponse,
  Calibration,
  Provenance,
} from './models';
@Injectable({ providedIn: 'root' })
export class NetworkApi {
  private http = inject(HttpClient);
  runScenario(body: ScenarioDefinition) {
    return this.http.post<ScenarioResult>('/api/scenarios', body);
  }
  scenario(id: string, country: string) {
    return this.http.get<ScenarioResult>('/api/scenarios/' + encodeURIComponent(id), {
      params: this.params({ country_id: country }),
    });
  }
  scenarios(country: string) {
    return this.http.get<ScenarioMetadata[]>('/api/scenarios', {
      params: this.params({ country_id: country }),
    });
  }
  discardScenario(id: string, country: string) {
    return this.http.delete<void>('/api/scenarios/' + encodeURIComponent(id), {
      params: this.params({ country_id: country }),
    });
  }
  warnings(scope: Record<string, string>) {
    return this.http.get<WarningList>('/api/warnings', { params: this.params(scope) });
  }
  private params(scope: Record<string, string | number>) {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(scope))
      if (value !== '') params = params.set(key, value);
    return params;
  }
  countries() {
    return this.http.get<{ items: Country[] }>('/api/countries');
  }
  forecast(facility: string, resource: string, country = 'IN', horizon = 14) {
    const suffix =
      resource === 'footfall'
        ? 'footfall'
        : resource === 'admissions'
          ? 'beds'
          : 'medicines/' + encodeURIComponent(resource);
    return this.http.get<Forecast>(
      '/api/forecasts/facilities/' + encodeURIComponent(facility) + '/' + suffix,
      { params: this.params({ country_id: country, horizon }) },
    );
  }
  performance(country = 'IN') {
    return this.http.get<Performance>('/api/models/forecasting/metrics', {
      params: this.params({ country_id: country }),
    });
  }
  sources(country = '') {
    return this.http.get<SourcesResponse>('/api/data-sources', {
      params: this.params({ country_id: country }),
    });
  }
  regions(country = 'IN') {
    return this.http.get<{ regions: Region[]; districts: District[] }>('/api/regions', {
      params: this.params({ country_id: country }),
    });
  }
  overview(scope: Record<string, string>) {
    return this.http.get<Overview>('/api/overview', { params: this.params(scope) });
  }
  facilities(scope: Record<string, string | number>) {
    return this.http.get<FacilityList>('/api/facilities', { params: this.params(scope) });
  }
  facility(id: string, country = 'IN') {
    return this.http.get<{
      facility: Facility;
      alerts: Alert[];
      as_of: string;
      country: Country;
      provenance: Record<string, Provenance>;
      calibration: Calibration;
    }>('/api/facilities/' + encodeURIComponent(id), {
      params: this.params({ country_id: country }),
    });
  }
  alerts(scope: Record<string, string>) {
    return this.http.get<{ items: Alert[]; total: number }>('/api/alerts', {
      params: this.params(scope),
    });
  }
  inventory(scope: Record<string, string>) {
    return this.http.get<{ items: Supply[] }>('/api/inventory', { params: this.params(scope) });
  }
}
