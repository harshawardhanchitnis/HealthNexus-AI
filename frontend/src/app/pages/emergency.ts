import { Component, computed, DestroyRef, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe, KeyValuePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, forkJoin, of, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Facility } from '../core/models';
import { ScenarioDefinition, ScenarioResult, ScenarioType } from '../core/resilience-models';
import { Forecast } from '../core/forecast-models';
import { ScenarioChart } from '../shared/scenario-chart';
import { WarningCards } from '../shared/warning-cards';

@Component({
  selector: 'app-emergency',
  imports: [
    DatePipe,
    DecimalPipe,
    PercentPipe,
    KeyValuePipe,
    FormsModule,
    RouterLink,
    ScenarioChart,
    WarningCards,
  ],
  templateUrl: './emergency.html',
})
export class EmergencyPage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroy = inject(DestroyRef);
  types: { id: ScenarioType; name: string; description: string; category: string; domains: string }[] = [
    {
      id: 'DENGUE_SURGE', category: 'DEMAND SURGE', domains: 'Patient demand · medicines · beds · workforce',
      name: 'Dengue surge',
      description: 'Additional fever visits flow through medicine demand, admissions and capacity.',
    },
    {
      id: 'DELIVERY_DELAY', category: 'SUPPLY CHAIN', domains: 'Known receipts · inventory · reserve protection',
      name: 'Medicine delivery delay',
      description: 'Shift known future receipts and recompute inventory and stock-out risk.',
    },
    {
      id: 'STAFF_SHORTAGE', category: 'WORKFORCE', domains: 'Available staff · service pressure',
      name: 'Staff shortage',
      description: 'Reduce available personnel and measure the resulting service pressure.',
    },
    {
      id: 'FACILITY_DISRUPTION', category: 'INFRASTRUCTURE', domains: 'Usable beds · service capacity · overflow',
      name: 'Facility / flood disruption',
      description:
        'Reduce usable beds and service capacity; retain existing patients as explicit overflow.',
    },
  ];
  kind: ScenarioType = 'DENGUE_SURGE';
  severity = 'severe';
  duration = 14;
  seed = 42;
  startDate = '';
  facilityFilter = '';
  medicine = 'IVF';
  custom: number | null = null;
  country = signal('IN');
  profile = signal('constrained');
  state = signal('');
  district = signal('');
  facilities = signal<Facility[]>([]);
  result = signal<ScenarioResult | null>(null);
  loading = signal(false);
  running = signal(false);
  error = signal('');
  notice = signal('');
  selected = signal('');
  chartResource = signal('footfall');
  focus = computed(
    () =>
      this.result()?.scenario_result.facilities.find((f) => f.facility_id === this.selected()) ||
      this.result()?.scenario_result.facilities[0],
  );
  baseline = computed(() =>
    this.result()?.baseline.facilities.find((f) => f.facility_id === this.focus()?.facility_id),
  );
  resources = computed(() => this.focus()?.resources || []);
  resource = computed(() => this.resources().find((r) => r.resource_id === this.chartResource()));
  baseResource = computed(() =>
    this.baseline()?.resources.find((r) => r.resource_id === this.chartResource()),
  );
  kpis = [
    { key: 'patient_demand', name: 'Patient demand', unit: 'visits' },
    { key: 'unmet_admissions', name: 'Unmet admissions', unit: 'requested admissions' },
    { key: 'peak_bed_occupancy_percent', name: 'Peak bed occupancy', unit: '% · highest facility' },
    {
      key: 'peak_workload_ratio',
      name: 'Peak personnel pressure',
      unit: 'demand / service capacity',
    },
    {
      key: 'max_stockout_probability',
      name: 'Maximum stock-out risk',
      unit: 'probability · within 14 days',
    },
    { key: 'critical_facilities', name: 'Critical facilities', unit: 'facilities' },
  ];
  constructor() {
    this.route.queryParamMap
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set('');
          this.result.set(null);
        }),
        switchMap((p) => {
          this.profile.set(p.get('profile') || 'constrained');
          this.country.set(p.get('country_id') || 'IN');
          this.state.set(p.get('state_id') || '');
          this.district.set(p.get('district_id') || '');
          this.facilityFilter = '';
          return forkJoin({
            facilities: this.api.facilities({
              country_id: this.country(),
              state_id: this.state(),
              district_id: this.district(),
              limit: 250,
            }),
            result: p.get('scenario_id')
              ? this.api.scenario(p.get('scenario_id')!, this.country())
              : of(null),
          }).pipe(
            catchError((e) => {
              this.error.set(this.message(e));
              return of(null);
            }),
          );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((r) => {
        this.facilities.set(r?.facilities.items || []);
        this.result.set(r?.result || null);
        this.selected.set(r?.result?.scenario_result.facilities[0]?.facility_id || '');
        if (r?.result) {
          const d = r.result.scenario.definition;
          this.kind = d.scenario_type;
          this.severity = d.severity;
          this.duration = d.duration;
          this.seed = d.seed;
          this.startDate = d.start_date || '';
          this.facilityFilter = d.facility_ids.length === 1 ? d.facility_ids[0] : '';
          this.medicine = d.parameters.medicine_id || 'IVF';
          this.custom =
            d.parameters.delay_days ??
            (d.parameters.unavailable_fraction != null
              ? d.parameters.unavailable_fraction * 100
              : null) ??
            (d.parameters.capacity_reduction != null
              ? d.parameters.capacity_reduction * 100
              : null);
        }
        this.loading.set(false);
      });
  }
  message(e: { error?: { detail?: unknown } }) {
    const detail = e.error?.detail;
    return typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((x) => (x as { msg: string }).msg).join('; ')
        : 'Projection unavailable. Check backend connectivity and saved model artifacts.';
  }
  title(kind = this.kind) {
    return this.types.find((t) => t.id === kind)?.name || kind;
  }
  description() {
    return this.types.find((t) => t.id === this.kind)?.description;
  }
  changeKind() {
    this.custom = null;
  }
  pune(profile = 'constrained') {
    this.seed = 42;
    this.facilityFilter = '';
    this.result.set(null);
    this.startDate = '';
    this.kind = 'DENGUE_SURGE';
    this.severity = 'severe';
    this.duration = 14;
    this.custom = null;
    this.router.navigate(['/emergency'], {
      queryParams: { profile, country_id: 'IN', state_id: 'MH', district_id: 'MH-PUNE' },
    });
  }
  run() {
    if (this.running()) return;
    this.running.set(true);
    this.error.set('');
    this.notice.set('');
    const parameters: ScenarioDefinition['parameters'] = {};
    if (this.kind === 'DELIVERY_DELAY') {
      parameters.medicine_id = this.medicine;
      if (this.custom !== null) parameters.delay_days = this.custom;
    }
    if (this.kind === 'STAFF_SHORTAGE' && this.custom !== null)
      parameters.unavailable_fraction = this.custom / 100;
    if (this.kind === 'FACILITY_DISRUPTION' && this.custom !== null)
      parameters.capacity_reduction = this.custom / 100;
    const definition: ScenarioDefinition = {
      scenario_type: this.kind,
      country_id: this.country(),
      state_id: this.state() || undefined,
      district_id: this.district() || undefined,
      facility_ids: this.facilityFilter ? [this.facilityFilter] : [],
      severity: this.severity,
      duration: this.duration,
      seed: this.seed,
      start_date: this.startDate || undefined,
      parameters,
    };
    const scope = this.router.url;
    this.api
      .runScenario(definition)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: (r) => {
          this.running.set(false);
          if (this.router.url !== scope) return;
          this.result.set(r);
          this.selected.set(r.scenario_result.facilities[0]?.facility_id || '');
          this.router.navigate([], {
            relativeTo: this.route,
            queryParams: { scenario_id: r.scenario.scenario_id },
            queryParamsHandling: 'merge',
          });
        },
        error: (e) => {
          this.error.set(this.message(e));
          this.running.set(false);
        },
      });
  }
  discard() {
    const r = this.result();
    if (!r) return;
    this.running.set(true);
    this.api
      .discardScenario(r.scenario.scenario_id, r.scenario.definition.country_id)
      .pipe(takeUntilDestroyed(this.destroy))
      .subscribe({
        next: () => {
          this.running.set(false);
          this.result.set(null);
          this.notice.set(
            'Scenario discarded. Baseline forecasts and network data remain unchanged.',
          );
          this.router.navigate([], {
            relativeTo: this.route,
            queryParams: { scenario_id: null },
            queryParamsHandling: 'merge',
          });
        },
        error: (e) => {
          this.error.set(this.message(e));
          this.running.set(false);
        },
      });
  }
  chooseFacility(event: Event) {
    this.selected.set((event.target as HTMLSelectElement).value);
  }
  chooseResource(event: Event) {
    this.chartResource.set((event.target as HTMLSelectElement).value);
  }
  chart(scenario: boolean): Forecast['forecast'] {
    return this.chartResource() === 'footfall'
      ? (scenario ? this.focus()?.footfall : this.baseline()?.footfall) || []
      : (scenario ? this.resource()?.forecast : this.baseResource()?.forecast) || [];
  }
  stockChart(scenario: boolean): Forecast['forecast'] {
    return ((scenario ? this.resource() : this.baseResource())?.stockout.trajectory || []).map(
      (p) => ({
        date: p.date,
        point: p.closing_stock,
        lower80: p.lower95,
        upper80: p.upper95,
        lower95: p.lower95,
        upper95: p.upper95,
      }),
    );
  }
  risk(value: number | null) {
    return value === null ? '—' : (value * 100).toFixed(1) + '%';
  }
}
