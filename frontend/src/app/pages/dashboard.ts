import { Component, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, combineLatest, of, Subject, startWith, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { computationPolicy } from '../core/computation-policy';
import { Alert, FacilityList, Overview, Status, Supply } from '../core/models';
import { Icon } from '../shared/icon';
import { StatusBadge } from '../shared/status-badge';
import { TrendChart } from '../shared/trend-chart';
import { WarningList } from '../core/resilience-models';
import { WarningCards } from '../shared/warning-cards';
import { ReadNotice } from '../shared/read-notice';

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, DecimalPipe, DatePipe, Icon, StatusBadge, TrendChart, WarningCards, ReadNotice],
  templateUrl: './dashboard.html',
})
export class Dashboard {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private reload$ = new Subject<void>();
  private forceNext = false;
  private context = '';
  cacheKeys = signal<string[]>([]);
  page = signal('overview');
  loading = signal(true);
  error = signal('');
  data = signal<Overview | null>(null);
  facilities = signal<FacilityList | null>(null);
  alerts = signal<Alert[]>([]);
  supply = signal<Supply[]>([]);
  warningSummary = signal<WarningList | null>(null);
  warningError = signal(false);
  districtRequired() { return this.api.districtOnly() && !this.scope['district_id']; }
  search = '';
  status = '';
  offset = 0;
  scope: Record<string, string> = {};
  statuses: Status[] = ['HEALTHY', 'WATCH', 'AT_RISK', 'CRITICAL'];
  titles: Record<string, string> = {
    overview: 'National Health Resilience',
    network: 'Network Intelligence',
    facilities: 'Facility explorer',
    supply: 'Medicine & supply',
    alerts: 'Early warning centre',
  };
  subtitles: Record<string, string> = {
    overview: 'Observe resources. Anticipate pressure. Coordinate a protected response.',
    network: 'Public-data context and simulated resources within the selected country.',
    facilities: 'Explore capacity, medicine cover and operational readiness.',
    supply: 'Track essential medicine stocks and the facilities below their safety reserve.',
    alerts: 'Transparent, rule-based signals that help teams act sooner.',
  };

  constructor() {
    combineLatest([
      this.route.data,
      this.route.queryParamMap.pipe(
        tap(() => {
          this.offset = 0;
        }),
      ),
      this.reload$.pipe(startWith(undefined)),
      computationPolicy(this.api),
    ])
      .pipe(
        tap(([data, params]) => {
          this.page.set(data['page']);
          this.error.set('');
          this.scope = {
            profile: params.get('profile') || 'constrained',
            country_id: params.get('country_id') || 'IN',
            state_id: params.get('state_id') || '',
            district_id: params.get('district_id') || '',
          };
          const context = JSON.stringify([this.page(), this.scope, this.search, this.status, this.offset]);
          if (context !== this.context) {
            this.data.set(null);
            this.facilities.set(null);
            this.warningSummary.set(null);
            this.context = context;
          }
          this.loading.set(!this.data());
        }),
        switchMap(() => {
          const force = this.forceNext;
          this.forceNext = false;
          const facilityScope = {
              ...this.scope,
              search: this.search,
              status: this.status,
              offset: this.offset,
              limit: this.page() === 'overview' ? 5 : 15,
          };
          this.cacheKeys.set([
            this.api.readKey('/api/overview', this.scope),
            this.api.readKey('/api/facilities', facilityScope),
            ...(this.page() === 'alerts' ? [this.api.readKey('/api/alerts', this.scope)] : []),
            ...(this.page() === 'supply' ? [this.api.readKey('/api/inventory', this.scope)] : []),
            ...(this.page() === 'overview' && !this.districtRequired() ? [this.api.readKey('/api/warnings', this.scope)] : []),
          ]);
          this.warningError.set(false);
          return combineLatest({
            overview: this.api.overview(this.scope, force),
            facilities: this.api.facilities(facilityScope, force),
            alerts:
              this.page() === 'alerts'
                ? this.api.alerts(this.scope, force)
                : of({ items: [] as Alert[], total: 0 }),
            supply:
              this.page() === 'supply'
                ? this.api.inventory(this.scope, force)
                : of({ items: [] as Supply[] }),
            warnings: this.page() === 'overview' && !this.districtRequired()
              ? this.api.warnings(this.scope, force).pipe(catchError(() => {
                  this.warningError.set(true); return of(null);
                }), startWith(null)) : of(null),
          }).pipe(
            catchError((error) => {
              this.error.set(
                error.status === 404
                  ? 'This region or district is not in the sample network. Reset the scope to All India.'
                  : 'The healthcare network could not be loaded. Check the backend connection, then retry.',
              );
              return of(null);
            }),
          );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((result) => {
        if (result) {
          this.data.set(result.overview);
          this.facilities.set(result.facilities);
          this.alerts.set(result.alerts.items);
          this.supply.set(result.supply.items);
          this.warningSummary.set(result.warnings);
        }
        this.loading.set(false);
      });
  }
  refresh() {
    this.forceNext = true;
    this.reload$.next();
  }
  apiProfile() { return this.api.profile(); }
  loadDemo(profile: string) {
    this.router.navigate(['/overview'],{queryParams:{country_id:'IN',state_id:'MH',district_id:'MH-PUNE',profile,demo:'1'}});
  }
  applySearch(event: Event) {
    event.preventDefault();
    this.offset = 0;
    this.reload$.next();
  }
  changeSearch(event: Event) {
    this.search = (event.target as HTMLInputElement).value;
  }
  changeStatus(event: Event) {
    this.status = (event.target as HTMLSelectElement).value;
    this.offset = 0;
    this.reload$.next();
  }
  paginate(step: number) {
    this.offset += step * 15;
    this.reload$.next();
  }
  selectRegion(id: string) {
    this.router.navigate(['/overview'], {
      queryParams: { profile: this.api.profile(), country_id: this.scope['country_id'], state_id: id },
    });
  }
  severity(region: Overview['regions'][number]): Status {
    return region.status_counts.CRITICAL
      ? 'CRITICAL'
      : region.status_counts.AT_RISK
        ? 'AT_RISK'
        : region.status_counts.WATCH
          ? 'WATCH'
          : 'HEALTHY';
  }
  scopeName() {
    return this.scope['district_id']
      ? this.scope['district_id'].replaceAll('-', ' ')
      : this.scope['state_id']
        ? this.data()?.regions[0]?.name || this.scope['state_id']
        : 'All ' + (this.data()?.country.name || this.scope['country_id'] || 'India');
  }
  visibleAlerts() {
    return this.page() === 'alerts' ? this.alerts() : this.data()?.alerts || [];
  }
  lastItem() {
    return Math.min(this.offset + 15, this.facilities()?.total || 0);
  }
}
