import { Component, inject, input, signal, effect } from '@angular/core';
import { DecimalPipe, PercentPipe, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Forecast } from '../core/forecast-models';

@Component({
  selector: 'app-predictive-outlook',
  imports: [DecimalPipe, PercentPipe, DatePipe, RouterLink],
  template: `
    <section class="panel predictive-outlook">
      <div class="panel-heading">
        <div>
          <div class="eyebrow">PREDICTIVE OUTLOOK</div>
          <h2>Ahead of the next shift.</h2>
          <p>Evaluated models on calibrated simulated history.</p>
        </div>
        <a
          routerLink="/forecasts"
          [queryParams]="{ country_id: country(), facility_id: facility(), resource: 'IVF' }"
          class="inline-link"
          >Explore forecasts →</a
        >
      </div>
      @if (error()) {
        <p class="forecast-notice">{{ error() }}</p>
      } @else if (footfall(); as f) {
        <div class="outlook-grid">
          <p>
            Next 7 days:
            <strong>{{ f.summary.forecast_total | number: '1.0-0' }} patient visits</strong>, a
            <strong>{{ f.summary.change_percent | number: '1.1-1' }}%</strong> change in daily
            demand from the recent week.
          </p>
          @if (medicine()?.stockout; as s) {
            <p>
              IV fluids: <strong>{{ s.probabilities['7'] | percent: '1.1-1' }}</strong> estimated
              7-day model-based stock-out risk. Safety reserve breach:
              <strong>{{
                s.safety_breach_date ? (s.safety_breach_date | date: 'dd MMM') : 'beyond 14 days'
              }}</strong
              >.
            </p>
          }
        </div>
      } @else {
        <p class="forecast-notice">Loading predictive outlook…</p>
      }
    </section>
  `,
})
export class PredictiveOutlook {
  facility = input.required<string>();
  country = input.required<string>();
  private api = inject(NetworkApi);
  footfall = signal<Forecast | null>(null);
  medicine = signal<Forecast | null>(null);
  error = signal('');
  constructor() {
    effect((cleanup) => {
      this.footfall.set(null);
      this.medicine.set(null);
      this.error.set('');
      const sub = forkJoin({
        footfall: this.api.forecast(this.facility(), 'footfall', this.country(), 7),
        medicine: this.api.forecast(this.facility(), 'IVF', this.country(), 14),
      }).subscribe({
        next: (r) => {
          this.footfall.set(r.footfall);
          this.medicine.set(r.medicine);
        },
        error: (e) =>
          this.error.set(
            e.error?.detail || 'Predictive outlook unavailable. Build matching forecast artifacts.',
          ),
      });
      cleanup(() => sub.unsubscribe());
    });
  }
}
