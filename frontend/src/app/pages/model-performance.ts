import { Component, inject, signal } from '@angular/core';
import { DecimalPipe, PercentPipe, DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, of, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Performance } from '../core/forecast-models';
import { ReadNotice } from '../shared/read-notice';

@Component({
  selector: 'app-model-performance',
  imports: [DecimalPipe, PercentPipe, DatePipe, RouterLink, ReadNotice],
  template: `
    <div class="page-heading">
      <div>
        <div class="eyebrow">MODEL PERFORMANCE / MEASURED, NOT ASSUMED</div>
        <h1>Model Performance</h1>
        <p>Three baselines, one trained candidate, and an untouched chronological test window.</p>
      </div>
      <a class="button secondary" routerLink="/forecasts" queryParamsHandling="preserve"
        >Explore forecasts →</a
      >
    </div>
    <section class="info-banner"><div><strong>Operational forecasting</strong><br />Country-local demand models power the operational tools. WAPE is forecast error, not accuracy.<br /><a routerLink="/brics" queryParamsHandling="preserve">Inspect the separate federated footfall experiment →</a></div></section>
    @if (loading()) {
      <div class="loading-state" role="status">Loading held-out evaluation…</div>
    } @else if (error()) {
      <div class="empty-state" role="alert">
        <h2>Evaluation unavailable</h2>
        <p>{{ error() }}</p>
      </div>
    } @else if (data(); as d) {
      <app-read-notice [keys]="readKeys()" />
      <div class="forecast-notice">
        {{ d.data_type }} · {{ d.country_id }} · Evaluated
        {{ d.evaluated_at | date: 'dd MMM yyyy' }}. Results measure this simulator, not real-world
        clinical predictive performance.
      </div>
      <div class="split-grid">
        @for (name of windows; track name) {
          <article>
            <small>{{ name }}</small
            ><strong>{{ d.windows[name].start | date: 'dd MMM yyyy' }}</strong
            ><span>to {{ d.windows[name].end | date: 'dd MMM yyyy' }}</span>
          </article>
        }
      </div>
      <p>{{ d.selection_rule }}</p>
      @for (target of targets; track target.id) {
        <section class="panel">
          <div class="panel-heading">
            <div>
              <h2>{{ target.name }}</h2>
              <p>
                {{ d.targets[target.id].train_rows | number }} training rows ·
                {{ d.targets[target.id].test_rows | number }} test predictions · all 14 daily
                horizons
              </p>
            </div>
            <span class="tag"
              >Champion: {{ d.targets[target.id].champion.replaceAll('_', ' ') }}</span
            >
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Selection WAPE</th>
                  <th>Test MAE</th>
                  <th>Test RMSE</th>
                  <th>Test WAPE</th>
                  <th>Day 1 WAPE</th>
                  <th>Day 7 WAPE</th>
                  <th>Day 14 WAPE</th>
                </tr>
              </thead>
              <tbody>
                @for (model of models; track model) {
                  @let m = d.targets[target.id].models[model];
                  <tr [class.champion-row]="d.targets[target.id].champion === model">
                    <td>
                      <strong>{{ model.replaceAll('_', ' ') }}</strong>
                    </td>
                    <td>{{ m.selection.wape | percent: '1.3-3' }}</td>
                    <td>{{ m.test.mae | number: '1.4-4' }}</td>
                    <td>{{ m.test.rmse | number: '1.4-4' }}</td>
                    <td>{{ m.test.wape | percent: '1.3-3' }}</td>
                    <td>{{ m.test_by_horizon['1'].wape | percent: '1.3-3' }}</td>
                    <td>{{ m.test_by_horizon['7'].wape | percent: '1.3-3' }}</td>
                    <td>{{ m.test_by_horizon['14'].wape | percent: '1.3-3' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
          <div class="coverage-list">
            @for (resource of keys(d.targets[target.id].coverage); track resource) {
              @let c = d.targets[target.id].coverage[resource];
              <p>
                <strong>{{ resource }}</strong
                ><span>80% band: {{ c['0.8'].coverage | percent: '1.2-2' }} observed coverage</span
                ><span
                  >95% band: {{ c['0.95'].coverage | percent: '1.2-2' }} observed coverage</span
                >
              </p>
            }
          </div>
        </section>
      }
      <section class="panel provenance-details">
        <h2>How to read these results</h2>
        <p>
          Lower errors are better. MAE and RMSE use target units. Medicine errors pool different
          medicine units; compare models within the same target, not between targets. WAPE weights
          higher-volume series more heavily.
        </p>
        <p>
          Baselines can win. Champion selection uses the selection period only; later test
          performance never changes the winner. Models stay frozen after training.
        </p>
        <p>{{ d.uncertainty_method }}</p>
        <p>{{ d.source_vintage_note }}</p>
        <p>{{ d.model_version }}</p>
      </section>
    }
  `,
})
export class ModelPerformancePage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  data = signal<Performance | null>(null);
  error = signal('');
  loading = signal(true);
  windows = ['train', 'selection', 'calibration', 'test'];
  targets = [
    { id: 'footfall', name: 'Patient footfall' },
    { id: 'medicine', name: 'Requested medicine demand' },
    { id: 'admissions', name: 'Requested admissions' },
  ];
  models = ['naive', 'seasonal_naive', 'moving_average', 'hist_gradient_boosting'];
  keys = Object.keys;
  readKeys() { return [this.api.readKey('/api/models/forecasting/metrics', { country_id: this.route.snapshot.queryParamMap.get('country_id') || 'IN' })]; }
  constructor() {
    this.route.queryParamMap
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set('');
        }),
        switchMap((p) =>
          this.api.performance(p.get('country_id') || 'IN').pipe(
            catchError((e) => {
              this.error.set(e.error?.detail || 'Could not load model evaluation.');
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((d) => {
        this.data.set(d);
        this.loading.set(false);
      });
  }
}
