import { Component, computed, DestroyRef, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe, KeyValuePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, forkJoin, of, Subscription, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { PlanningRequest, PlanningPreview, PlanningResult } from '../core/optimization-models';
import { ScenarioMetadata } from '../core/resilience-models';

@Component({
  selector: 'app-redistribution',
  imports: [FormsModule, DatePipe, DecimalPipe, PercentPipe, KeyValuePipe, RouterLink],
  templateUrl: './redistribution.html',
})
export class RedistributionPage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroy = inject(DestroyRef);
  private pending?: Subscription;
  country = 'IN';
  profile = 'constrained';
  state = '';
  district = '';
  scenarioId = '';
  scope: PlanningRequest['scope'] = 'national';
  resource = '';
  seconds = 10;
  scenarios = signal<ScenarioMetadata[]>([]);
  preview = signal<PlanningPreview | null>(null);
  result = signal<PlanningResult | null>(null);
  loading = signal(false);
  running = signal(false);
  error = signal('');
  notice = signal('');
  selected = signal('');
  selectedResource = signal('IVF');
  receiverLimit = signal(30);
  donorLimit = signal(30);
  focus = computed(() => this.result()?.after.find((f) => f.facility_id === this.selected()));
  afterResource = computed(() =>
    this.focus()?.resources.find((r) => r.resource_id === this.selectedResource()),
  );
  beforeResource = computed(() =>
    this.result()
      ?.before.find((f) => f.facility_id === this.selected())
      ?.resources.find((r) => r.resource_id === this.selectedResource()),
  );
  beforeWarnings = computed(
    () =>
      this.result()?.before_warnings.items.filter(
        (w) => w.facility_id === this.selected() && w.resource_id === this.selectedResource(),
      ) || [],
  );
  afterWarnings = computed(
    () =>
      this.result()?.after_warnings.items.filter(
        (w) => w.facility_id === this.selected() && w.resource_id === this.selectedResource(),
      ) || [],
  );
  medicineCount = computed(() => new Set(this.result()?.transfers.map((t) => t.resource_id)).size);
  constructor() {
    this.destroy.onDestroy(() => this.pending?.unsubscribe());
    this.route.queryParamMap
      .pipe(
        tap((p) => {
          this.pending?.unsubscribe();
          this.running.set(false);
          this.loading.set(true);
          this.error.set('');
          this.preview.set(null);
          this.result.set(null);
          this.profile = p.get('profile') || 'constrained';
          this.country = p.get('country_id') || 'IN';
          this.state = p.get('state_id') || '';
          this.district = p.get('district_id') || '';
          this.scenarioId = p.get('scenario_id') || '';
          const donorScope = p.get('donor_scope');
          if (['district','cross_district','state','national'].includes(donorScope || '')) this.scope = donorScope as PlanningRequest['scope'];
          else if (!p.get('run_id')) this.scope = this.district ? 'district' : 'national';
          if (
            (this.scope === 'district' && !this.district) ||
            (this.scope === 'state' && !this.state) || (this.scope === 'cross_district' && (!this.state || !this.district || this.country !== 'IN'))
          )
            this.scope = 'national';
        }),
        switchMap((p) =>
          forkJoin({
            scenarios: this.api.scenarios(this.country),
            plan: p.get('run_id') ? this.api.plan(p.get('run_id')!, this.country) : of(null),
          }).pipe(
            catchError((e) => {
              this.error.set(e.error?.detail || 'Unable to load planning context.');
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(this.destroy),
      )
      .subscribe((data) => {
        this.loading.set(false);
        if (!data) return;
        this.scenarios.set(data.scenarios);
        if (data.plan) {
          const q = data.plan.preview.request;
          if (
            (q.profile || 'constrained') !== this.profile ||
            q.country_id !== this.country ||
            (q.state_id || '') !== this.state ||
            (q.district_id || '') !== this.district ||
            (q.scenario_id || '') !== this.scenarioId
          ) {
            this.error.set(
              'This saved plan belongs to a different scope. Remove the run_id or return to its original scope.',
            );
            return;
          }
          if (this.route.snapshot.queryParamMap.get('donor_scope') && this.scope !== q.scope) { this.error.set('Saved plan donor scope does not match.'); return; }
          this.scope = q.scope;
          this.resource = q.resources.length === 1 ? q.resources[0] : '';
          this.seconds = q.time_limit_seconds;
          this.show(data.plan);
        } else this.loadPreview();
      });
  }
  body(): PlanningRequest {
    return {
      country_id: this.country,
      ...(this.state ? { state_id: this.state } : {}),
      ...(this.district ? { district_id: this.district } : {}),
      ...(this.scenarioId ? { scenario_id: this.scenarioId } : {}),
      scope: this.scope,
      resources: this.resource ? [this.resource] : ['PCM', 'IVF', 'ORS', 'AMX', 'IFA'],
      horizon: 14,
      time_limit_seconds: this.seconds,
    };
  }
  changeScope(value: PlanningRequest['scope']) {
    this.router.navigate([], {relativeTo:this.route,queryParams:{donor_scope:value,run_id:null},queryParamsHandling:'merge'});
  }
  donorDistrictNames() { return this.result()?.geography.donor_districts.map(d=>d.name).join(', ') || 'None'; }
  changeScenario() {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { scenario_id: this.scenarioId || null, run_id: null },
      queryParamsHandling: 'merge',
    });
  }
  resetContext() {
    this.router.navigate([], {relativeTo:this.route,queryParams:{scenario_id:null,run_id:null},queryParamsHandling:'merge'});
  }
  loadPreview() {
    if (this.route.snapshot.queryParamMap.get('run_id')) {
      this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { run_id: null },
        queryParamsHandling: 'merge',
      });
      return;
    }
    this.pending?.unsubscribe();
    this.preview.set(null);
    this.result.set(null);
    this.error.set('');
    this.notice.set('');
    this.loading.set(true);
    this.pending = this.api.planningPreview(this.body()).subscribe({
      next: (p) => {
        this.preview.set(p);
        this.loading.set(false);
      },
      error: (e) => {
        this.loading.set(false);
        this.error.set(e.error?.detail || 'Could not calculate safe donor capacity.');
      },
    });
  }
  optimize() {
    if (!this.preview() || this.running()) return;
    this.running.set(true);
    this.error.set('');
    this.pending = this.api.optimize(this.body()).subscribe({
      next: (p) => {
        this.running.set(false);
        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: { run_id: p.run_id, donor_scope: p.preview.request.scope },
          queryParamsHandling: 'merge',
        });
      },
      error: (e) => {
        this.running.set(false);
        this.error.set(e.error?.detail || 'Optimization failed.');
      },
    });
  }
  show(p: PlanningResult) {
    this.result.set(p);
    this.preview.set(p.preview);
    const urgent = [...p.preview.receivers].sort(
      (a, b) => Number(b.critical) - Number(a.critical) || b.priority - a.priority,
    )[0];
    this.selected.set(urgent?.facility_id || p.after[0]?.facility_id || '');
    this.selectedResource.set(urgent?.resource_id || 'IVF');
  }
  discard() {
    const p = this.result();
    if (!p) return;
    this.running.set(true);
    this.pending = this.api.discardPlan(p.run_id, this.country).subscribe({
      next: () => {
        this.running.set(false);
        this.router.navigate([], {
          relativeTo: this.route,
          queryParams: { run_id: null },
          queryParamsHandling: 'merge',
        });
      },
      error: (e) => {
        this.running.set(false);
        this.error.set(e.error?.detail || 'Could not discard plan.');
      },
    });
  }
}
