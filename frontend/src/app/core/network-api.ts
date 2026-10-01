import { GeospatialView } from './geospatial-models';
import { Router } from '@angular/router';
import { FederationStatus, FederationNode, FederationRequest, FederationRun } from './federation-models';
import { CopilotRequest, CopilotResponse, CopilotStatus, CopilotProgress } from './copilot-models';
import { inject, Injectable, signal } from '@angular/core';
import { shareReplay, tap } from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Forecast, Performance } from './forecast-models';
import { ReadCache } from './read-cache';
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
  private cache = inject(ReadCache);
  // Conservative until server capabilities arrive. Never infer policy from a hostname.
  districtOnly = signal(true);
  private countryRequest = this.httpCountries();
  private httpCountries() {
    return this.cache.read('countries', () => this.http.get<{items: Country[]; low_memory?: boolean}>('/api/countries'), Infinity).pipe(
      tap(data => this.districtOnly.set(data.low_memory === true)), shareReplay({bufferSize:1,refCount:false}));
  }
  federationStatus() { return this.read<FederationStatus>('/api/federation/status', {}, 0); }
  savedFederation() { return this.read<FederationRun>('/api/federation/saved-demo', {}, 120_000); }
  federationNodes() { return this.read<{items: FederationNode[]}>('/api/federation/nodes', {}, 0); }
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
    return this.read<ScenarioMetadata[]>('/api/scenarios', { country_id: country }, 0);
  }
  discardScenario(id: string, country: string) {
    return this.http.delete<void>('/api/scenarios/' + encodeURIComponent(id), {
      params: this.params({ country_id: country }),
    });
  }
  warnings(scope: Record<string, string>, force = false) {
    return this.read<WarningList>('/api/warnings', scope, scope['scenario_id'] ? 0 : 60_000, force);
  }
  readKey(url: string, scope: Record<string, string | number> = {}) {
    return this.cache.key(url, this.params(scope));
  }
  private read<T>(url: string, scope: Record<string, string | number> = {}, ttl = 60_000, force = false) {
    const params = this.params(scope); // Capture profile before a queued request can change routes.
    return this.cache.read(this.cache.key(url, params), () => this.http.get<T>(url, { params }), ttl, force);
  }
  private params(scope: Record<string, string | number>) {
    let params = new HttpParams().set('profile', this.profile());
    for (const [key, value] of Object.entries(scope))
      if (value !== '') params = params.set(key, value);
    return params;
  }
  geospatial(scope: Record<string, string>) {
    const stable = (!scope['mode'] || scope['mode'] === 'network') && !scope['scenario_id'] && !scope['run_id'];
    return this.read<GeospatialView>('/api/geospatial', scope, stable ? 60_000 : 0);
  }
  countries() {
    return this.countryRequest;
  }
  forecast(facility: string, resource: string, country = 'IN', horizon = 14) {
    return this.read<Forecast>(this.forecastEndpoint(facility, resource), { country_id: country, horizon });
  }
  forecastKey(facility: string, resource: string, country = 'IN', horizon = 14) {
    return this.readKey(this.forecastEndpoint(facility, resource), { country_id: country, horizon });
  }
  private forecastEndpoint(facility: string, resource: string) {
    const suffix =
      resource === 'footfall'
        ? 'footfall'
        : resource === 'admissions'
          ? 'beds'
          : 'medicines/' + encodeURIComponent(resource);
    return '/api/forecasts/facilities/' + encodeURIComponent(facility) + '/' + suffix;
  }
  performance(country = 'IN') {
    return this.read<Performance>('/api/models/forecasting/metrics', { country_id: country }, 120_000);
  }
  sources(country = '') {
    return this.read<SourcesResponse>('/api/data-sources', { country_id: country }, 120_000);
  }
  regions(country = 'IN') {
    return this.read<{ regions: Region[]; districts: District[] }>('/api/regions', { country_id: country });
  }
  overview(scope: Record<string, string>, force = false) {
    return this.read<Overview>('/api/overview', scope, 60_000, force);
  }
  facilities(scope: Record<string, string | number>, force = false) {
    return this.read<FacilityList>('/api/facilities', scope, 60_000, force);
  }
  facility(id: string, country = 'IN') {
    return this.read<{
      facility: Facility;
      alerts: Alert[];
      as_of: string;
      country: Country;
      provenance: Record<string, Provenance>;
      calibration: Calibration;
    }>('/api/facilities/' + encodeURIComponent(id), { country_id: country });
  }
  alerts(scope: Record<string, string>, force = false) {
    return this.read<{ items: Alert[]; total: number }>('/api/alerts', scope, 60_000, force);
  }
  inventory(scope: Record<string, string>, force = false) {
    return this.read<{ items: Supply[] }>('/api/inventory', scope, 60_000, force);
  }
}
