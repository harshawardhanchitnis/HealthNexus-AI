import { Component, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, of, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Alert, Facility } from '../core/models';
import { StatusBadge } from '../shared/status-badge';
import { TrendChart } from '../shared/trend-chart';
import { Icon } from '../shared/icon';
@Component({
  selector: 'app-facility',
  imports: [RouterLink, DecimalPipe, DatePipe, StatusBadge, TrendChart, Icon],
  template: `
    <a routerLink="/facilities" queryParamsHandling="preserve" class="inline-link back-link"
      >← Back to facilities</a
    >
    @if (error()) {
      <div class="empty-state" role="alert">
        <h1>Facility unavailable</h1>
        <p>{{ error() }}</p>
      </div>
    } @else if (loading()) {
      <div class="loading-state" role="status">Loading facility…</div>
    } @else if (facility(); as f) {
      <div class="page-heading">
        <div>
          <div class="eyebrow">INDIA / {{ f.state_id }} / {{ f.district_name }}</div>
          <h1>{{ f.name }}</h1>
          <p>{{ f.id }} · Synthetic facility · {{ asOf() | date: 'dd MMM yyyy' }}</p>
        </div>
        <app-status [value]="f.status" />
      </div>
      <div class="kpi-grid">
        <article class="kpi">
          <div class="kpi-label">Readiness score</div>
          <div class="kpi-value">{{ f.resilience_score }}<small>/100</small></div>
          <div class="kpi-note">Threshold-based prototype score</div>
        </article>
        <article class="kpi">
          <div class="kpi-label">Patient visits today</div>
          <div class="kpi-value">{{ f.footfall_today | number }}</div>
          <div class="kpi-note">Synthetic daily footfall</div>
        </article>
        <article class="kpi">
          <div class="kpi-label">Beds available</div>
          <div class="kpi-value">
            {{ f.beds.available }}<small>/{{ f.beds.total }}</small>
          </div>
          <div class="kpi-note">
            {{ f.beds.occupied }} occupied · {{ f.beds.reserved }} reserved
          </div>
        </article>
        <article class="kpi">
          <div class="kpi-label">Staff present</div>
          <div class="kpi-value">
            {{ f.staff.present }}<small>/{{ f.staff.scheduled }}</small>
          </div>
          <div class="kpi-note">
            {{ f.staff.doctors_present }} doctors · {{ f.staff.nurses_present }} nurses
          </div>
        </article>
      </div>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>Medicine inventory</h2>
            <p>Reconciled balance: opening + received − consumed = current stock</p>
          </div>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Opening</th>
                <th>Received</th>
                <th>Consumed</th>
                <th>Current</th>
                <th>7-day reserve</th>
                <th>Days of cover</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              @for (i of f.inventory; track i.medicine_id) {
                <tr>
                  <td>
                    <strong>{{ i.name }}</strong
                    ><small>{{ i.unit }}</small>
                  </td>
                  <td>{{ i.opening_stock | number }}</td>
                  <td>{{ i.units_received | number }}</td>
                  <td>{{ i.units_consumed | number }}</td>
                  <td>
                    <strong>{{ i.current_stock | number }}</strong>
                  </td>
                  <td>{{ i.safety_stock | number }}</td>
                  <td>{{ i.days_of_cover }}</td>
                  <td><app-status [value]="i.status" /></td>
                </tr>
              }
            </tbody>
          </table>
        </div>
        <div class="panel-footnote">
          Days of cover = current stock ÷ trailing seven-day average consumption. This is not an ML
          stock-out forecast.
        </div>
      </section>
      <section class="panel detail-trend">
        <div class="panel-heading">
          <div>
            <h2>Patient demand history</h2>
            <p>Visits in the last 28 days</p>
          </div>
        </div>
        <app-trend-chart [data]="f.history" />
      </section>
      <h2 class="section-title">Resource alerts · {{ alerts().length }}</h2>
      <div class="alert-grid">
        @for (a of alerts(); track a.id) {
          <article class="panel alert-card">
            <app-status [value]="a.severity" />
            <h2>{{ a.title }}</h2>
            <p>{{ a.explanation }}</p>
            <div class="recommendation">
              <strong>RECOMMENDED ACTION</strong>
              <p>{{ a.recommended_action }}</p>
            </div>
          </article>
        } @empty {
          <div class="info-banner">
            <app-icon name="check" />No stock or attendance threshold violations in this facility.
          </div>
        }
      </div>
      <div class="data-notice">
        <app-icon name="shield" />
        <p>
          This is a synthetic facility. Its name does not refer to a verified real hospital. No
          patient or employee identities are stored.
        </p>
      </div>
    }
  `,
})
export class FacilityPage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  facility = signal<Facility | null>(null);
  alerts = signal<Alert[]>([]);
  asOf = signal('');
  error = signal('');
  loading = signal(true);
  constructor() {
    this.route.paramMap
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set('');
        }),
        switchMap((params) =>
          this.api.facility(params.get('id') || '').pipe(
            catchError((error) => {
              this.error.set(
                error.status === 404
                  ? 'This facility does not exist in the sample network.'
                  : 'Could not reach the backend. Return to facilities and retry.',
              );
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((data) => {
        if (data) {
          this.facility.set(data.facility);
          this.alerts.set(data.alerts);
          this.asOf.set(data.as_of);
        }
        this.loading.set(false);
      });
  }
}
