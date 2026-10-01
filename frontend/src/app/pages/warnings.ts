import { Component, inject, signal } from '@angular/core';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, combineLatest, of, startWith, switchMap, tap } from 'rxjs';
import { computationPolicy } from '../core/computation-policy';
import { NetworkApi } from '../core/network-api';
import { WarningList, ScenarioMetadata } from '../core/resilience-models';
import { WarningCards } from '../shared/warning-cards';
import { ComputationNotice } from '../shared/computation-notice';
import { ReadNotice } from '../shared/read-notice';
@Component({
  selector: 'app-warnings',
  imports: [RouterLink, WarningCards, ComputationNotice, ReadNotice],
  template: `<div class="page-heading">
      <div>
        <div class="eyebrow">EARLY WARNING ENGINE / 14-DAY OUTLOOK</div>
        <h1>Early Warning Centre</h1>
        <p>
          Prioritised operational risks. Every warning has a traceable rule, forecast and
          explanation.
        </p>
      </div>
      <a class="button secondary" routerLink="/geospatial" [queryParams]="{mode:scenario()?'emergency':'forecast',run_id:null}" queryParamsHandling="merge">View on Map</a>
      <a class="button primary" routerLink="/emergency" queryParamsHandling="preserve"
        >Open simulator →</a
      >
    </div>
    <div class="severity-filters" aria-label="Quick severity filters">@for(level of ['', 'CRITICAL', 'WARNING', 'WATCH', 'INFO']; track level) {<button [attr.aria-pressed]="severity() === level" (click)="selectSeverity(level)">{{level || 'All severities'}}</button>}</div>
    <div class="forecast-controls">
      <label
        >Operating context<select
          aria-label="Warning context"
          [value]="scenario()"
          (change)="change('scenario_id', $event)"
        >
          <option value="" [selected]="!scenario()">Baseline forecast</option>
          @for (s of scenarios(); track s.scenario_id) {
            <option [value]="s.scenario_id" [selected]="s.scenario_id === scenario()">
              {{ s.definition.scenario_type.replaceAll('_', ' ') }} ·
              {{ s.definition.district_id || s.definition.state_id || s.definition.country_id }} ·
              {{ s.definition.severity }} · {{ s.scenario_id.slice(0, 8) }}
            </option>
          }
        </select></label
      >
      <label
        >Severity<select
          aria-label="Warning severity"
          [value]="severity()"
          (change)="change('severity', $event)"
        >
          <option value="" [selected]="!severity()">All severities</option>
          @for (s of ['CRITICAL', 'WARNING', 'WATCH', 'INFO']; track s) {
            <option [value]="s" [selected]="severity() === s">{{ s }}</option>
          }
        </select></label
      >
      <label
        >Category<select
          aria-label="Warning category"
          [value]="category()"
          (change)="change('category', $event)"
        >
          <option value="" [selected]="!category()">All categories</option>
          @for (c of ['medicine', 'demand', 'beds', 'personnel', 'emergency']; track c) {
            <option [value]="c" [selected]="category() === c">{{ c }}</option>
          }
        </select></label
      >
    </div>
    <div class="forecast-notice">
      {{
        scenario()
          ? 'SCENARIO PROJECTION — conditional on specified emergency assumptions.'
          : 'BASELINE FORECAST — saved country-local models and deterministic capacity rules.'
      }}
      Simulated operations; no clinical validation.
    </div>
    @if (districtRequired()) { <app-computation-notice /> } @else if (loading()) {
      <div class="loading-state" role="status">
        Evaluating saved forecasts and operational warning rules…
      </div>
    } @else if (error()) {
      <div class="empty-state" role="alert">
        {{ error() }} <button class="button secondary" (click)="reset()">Return to baseline</button>
      </div>
    } @else if (data(); as d) {
      <app-read-notice [keys]="readKeys()" />
      @if (scenarioListError()) { <p class="forecast-notice" role="status">Saved scenario list unavailable. The warning evidence below remains available for the selected context.</p> }
      <div class="kpi-grid">
        <article class="kpi">
          <div class="kpi-label">Critical</div>
          <div class="kpi-value critical-text">{{ d.summary.counts['CRITICAL'] }}</div>
          <div class="kpi-note">Short-horizon failures / severe pressure</div>
        </article>
        <article class="kpi">
          <div class="kpi-label">Warning</div>
          <div class="kpi-value">{{ d.summary.counts['WARNING'] }}</div>
          <div class="kpi-note">Capacity or reserve approaching limits</div>
        </article>
        <article class="kpi">
          <div class="kpi-label">Watch</div>
          <div class="kpi-value">{{ d.summary.counts['WATCH'] }}</div>
          <div class="kpi-note">Emerging operational pressure</div>
        </article>
        <article class="kpi">
          <div class="kpi-label">Facilities affected</div>
          <div class="kpi-value">{{ d.summary.facilities_affected }}</div>
          <div class="kpi-note">
            {{ d.summary.medicines_at_risk }} medicines · {{ d.summary.bed_warnings }} bed warnings
            · {{ d.summary.staff_warnings }} staff warnings
          </div>
        </article>
      </div>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>{{ d.summary.total }} active warnings</h2>
            <p>Sorted by deterministic priority. Counts reflect selected geography and filters.</p>
          </div>
          @if (scenario()) {
            <a class="button secondary" routerLink="/emergency" queryParamsHandling="preserve"
              >Compare scenario →</a
            >
          }
        </div>
        <app-warning-cards [items]="d.items" />
      </section>
    } `,
})
export class WarningsPage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  data = signal<WarningList | null>(null);
  scenarios = signal<ScenarioMetadata[]>([]);
  scenario = signal('');
  severity = signal('');
  category = signal('');
  loading = signal(true);
  error = signal('');
  districtRequired = signal(false);
  scenarioListError = signal(false);
  readKeys() {
    const p = this.route.snapshot.queryParamMap;
    return [this.api.readKey('/api/warnings', {country_id:p.get('country_id') || 'IN', state_id:p.get('state_id') || '', district_id:p.get('district_id') || '', facility_id:p.get('facility_id') || '', scenario_id:this.scenario(), severity:this.severity(), category:this.category()})];
  }
  constructor() {
    combineLatest([this.route.queryParamMap, computationPolicy(this.api)])
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set('');
          this.scenarioListError.set(false);
        }),
        switchMap(([p]) => {
          const country = p.get('country_id') || 'IN';
          this.scenario.set(p.get('scenario_id') || '');
          this.severity.set(p.get('severity') || '');
          this.category.set(p.get('category') || '');
          this.districtRequired.set(this.api.districtOnly() && !p.get('district_id') && !p.get('facility_id'));
          if (this.districtRequired()) return of(null);
          return combineLatest({
            warnings: this.api.warnings({
              country_id: country,
              state_id: p.get('state_id') || '',
              district_id: p.get('district_id') || '',
              facility_id: p.get('facility_id') || '',
              scenario_id: this.scenario(),
              severity: this.severity(),
              category: this.category(),
            }),
            scenarios: this.api.scenarios(country).pipe(
              catchError(() => { this.scenarioListError.set(true); return of([] as ScenarioMetadata[]); }), startWith([] as ScenarioMetadata[])),
          }).pipe(
            catchError((e) => {
              this.error.set(
                typeof e.error?.detail === 'string'
                  ? e.error.detail
                  : 'Warnings unavailable. Check saved models and selected scenario.',
              );
              return of(null);
            }),
          );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((r) => {
        this.data.set(r?.warnings || null);
        this.scenarios.set(r?.scenarios || []);
        this.loading.set(false);
      });
  }
  selectSeverity(severity: string) { this.router.navigate([], {relativeTo:this.route,queryParams:{severity:severity || null},queryParamsHandling:'merge'}); }
  change(key: string, event: Event) {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { [key]: (event.target as HTMLSelectElement).value || null },
      queryParamsHandling: 'merge',
    });
  }
  reset() {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { scenario_id: null, severity: null, category: null },
      queryParamsHandling: 'merge',
    });
  }
}
