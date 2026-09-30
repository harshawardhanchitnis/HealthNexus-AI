import { GeospatialView } from './geospatial-models';
import { Router } from '@angular/router';
import { FederationStatus, FederationNode, FederationRequest, FederationRun } from './federation-models';
import { CopilotRequest, CopilotResponse, CopilotStatus, CopilotProgress } from './copilot-models';
import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Forecast, Performance } from './forecast-models';
import { PlanningRequest, PlanningPreview, PlanningResult } from './optimization-models';
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
  private router = inject(Router);
  federationStatus() { return this.http.get<FederationStatus>('/api/federation/status'); }
  savedFederation() { return this.http.get<FederationRun>('/api/federation/saved-demo'); }
  federationNodes() { return this.http.get<{items: FederationNode[]}>('/api/federation/nodes'); }
  startFederation(body: FederationRequest) { return this.http.post<FederationRun>('/api/federation/runs', body); }
  federationRun(id: string) { return this.http.get<FederationRun>('/api/federation/runs/' + encodeURIComponent(id)); }
  discardFederation(id: string) { return this.http.delete<void>('/api/federation/runs/' + encodeURIComponent(id)); }
  copilotStatus() { return this.http.get<CopilotStatus>('/api/ai/status'); }
  copilot(body: CopilotRequest) {
    return this.http.post<CopilotResponse>('/api/ai/copilot', body);
  }
  copilotProgress(id: string, country: string) {
    return this.http.get<CopilotProgress>('/api/ai/requests/' + encodeURIComponent(id), {
      params: this.params({country_id: country}),
    });
  }
  discardConversation(id: string, country: string) {
    return this.http.delete<void>('/api/ai/conversations/' + encodeURIComponent(id), {
      params: this.params({country_id: country}),
    });
  }
  profile(): string {
    return this.router.parseUrl(this.router.url).queryParams['profile'] || 'constrained';
  }
  planningPreview(body: PlanningRequest) {
    return this.http.post<PlanningPreview>('/api/optimization/preview', { ...body, profile: this.profile() });
  }
  optimize(body: PlanningRequest) {
    return this.http.post<PlanningResult>('/api/optimization/redistribution', { ...body, profile: this.profile() });
  }
  plan(id: string, country: string) {
    return this.http.get<PlanningResult>('/api/optimization/runs/' + encodeURIComponent(id), {
      params: this.params({ country_id: country }),
    });
  }
  discardPlan(id: string, country: string) {
    return this.http.delete<void>('/api/optimization/runs/' + encodeURIComponent(id), {
      params: this.params({ country_id: country }),
    });
  }
  runScenario(body: ScenarioDefinition) {
    return this.http.post<ScenarioResult>('/api/scenarios', { ...body, profile: this.profile() });
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
    let params = new HttpParams().set('profile', this.profile());
    for (const [key, value] of Object.entries(scope))
      if (value !== '') params = params.set(key, value);
    return params;
  }
  geospatial(scope: Record<string, string>) {
    return this.http.get<GeospatialView>('/api/geospatial', {params: this.params(scope)});
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
