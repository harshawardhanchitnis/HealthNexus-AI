import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, of, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { SourcesResponse } from '../core/models';
import { Icon } from '../shared/icon';

@Component({
  selector: 'app-data-sources',
  imports: [DatePipe, DecimalPipe, Icon],
  template: `
    <div class="page-heading">
      <div>
        <div class="eyebrow">EVIDENCE / PROVENANCE</div>
        <h1>Know what powers the numbers.</h1>
        <p>Official observations, transparent derivations and clearly labelled simulation.</p>
      </div>
    </div>
    @if (error()) {
      <div class="empty-state" role="alert">
        <h2>Source data unavailable</h2>
        <p>{{ error() }}</p>
      </div>
    } @else if (!data()) {
      <div class="loading-state" role="status">Loading public source catalogue…</div>
    } @else if (data(); as sources) {
      <div class="evidence-hero">
        <div>
          <span class="eyebrow">PUBLIC DATA → CALIBRATION → SIMULATED OPERATIONS</span>
          <h2>Real context.<br />Honest operational modelling.</h2>
          <p>{{ sources.notice }}</p>
        </div>
        <div class="evidence-number">
          <strong>{{ sources.records.length }}</strong
          ><span>public observations in view</span
          ><b>{{ sources.datasets.length }} connected public sources</b>
        </div>
      </div>
      @if (!sources.datasets.length) {
        <div class="info-banner">
          No public cache is available. Run the documented import command. Operations use labelled
          fallback assumptions until the cache is restored.
        </div>
      }
      <div class="source-grid">
        @for (source of sources.datasets; track source.provenance.id) {
          <section class="panel source-card">
            <div class="source-card-top">
              <span class="source-badge">{{
                source.provenance.source_type.replaceAll('_', ' ')
              }}</span
              ><span class="source-integrated"><i></i>INTEGRATED</span>
            </div>
            <h2>{{ source.provenance.source_name }}</h2>
            <p>{{ source.status }}</p>
            <dl>
              <div>
                <dt>Geography</dt>
                <dd>{{ source.provenance.geography.join(' · ') }}</dd>
              </div>
              <div>
                <dt>Reference years</dt>
                <dd>{{ source.reference_years.join(', ') }}</dd>
              </div>
              <div>
                <dt>Accessed</dt>
                <dd>{{ source.provenance.accessed_at | date: 'dd MMM yyyy' }}</dd>
              </div>
              <div>
                <dt>Cached records, all countries</dt>
                <dd>{{ source.record_count }}</dd>
              </div>
            </dl>
            <a
              [href]="source.provenance.source_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-link"
              >View publisher source ↗</a
            >
            <details>
              <summary>Methodology, terms & version</summary>
              <p>{{ source.provenance.methodology }}</p>
              <p>{{ source.provenance.license }}</p>
              <p>
                Adapter {{ source.adapter_version }} · source version
                {{ source.provenance.version }}
              </p>
              <code>SHA-256 {{ source.provenance.checksum_sha256 }}</code>
            </details>
          </section>
        }
      </div>
      <section class="panel public-records">
        <div class="panel-heading">
          <div>
            <h2>Imported public observations</h2>
            <p>
              Values are publisher aggregates. Their years and units are preserved; no missing
              values are fabricated.
            </p>
          </div>
          <span class="subtle-tag">OFFLINE CACHE</span>
        </div>
        <div class="table-filters">
          <label class="search-field"
            ><app-icon name="search" /><input
              aria-label="Filter public observations"
              placeholder="Filter indicator, country or year…"
              (input)="filter.set($any($event.target).value)"
          /></label>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Country</th>
                <th>Indicator</th>
                <th>Reference year</th>
                <th>Value</th>
                <th>Unit</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              @for (row of filteredRecords(); track row.id) {
                <tr>
                  <td>{{ row.country_id }}</td>
                  <td>
                    <strong>{{ row.label }}</strong
                    ><small>{{ row.indicator }}</small>
                  </td>
                  <td>{{ row.year }}</td>
                  <td>{{ row.value | number: '1.0-3' }}</td>
                  <td>{{ row.unit.replaceAll('_', ' ') }}</td>
                  <td>{{ row.provenance_id }}</td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="6" class="no-results">No observations match this filter.</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </section>
      <section class="panel prose calibration-panel">
        <span class="source-badge derived-badge">DERIVED / SYNTHETIC</span>
        <h2>How public data anchors the {{ sources.calibration.country_id }} simulation</h2>
        <div class="calibration-metrics">
          <div>
            <strong>{{ sources.calibration.beds_per_10000 | number: '1.0-2' }}</strong
            ><span>country bed-density anchor / 10,000</span>
          </div>
          <div>
            <strong>{{ sources.calibration.doctors_per_10000 | number: '1.0-2' }}</strong
            ><span>country doctor-density anchor / 10,000</span>
          </div>
          <div>
            <strong>{{ sources.calibration.doctors_by_type?.[0] | number: '1.0-2' }}</strong
            ><span>India PHC doctors / facility baseline</span>
          </div>
        </div>
        <ul>
          @for (assumption of sources.calibration.assumptions; track assumption) {
            <li>{{ assumption }}</li>
          }
        </ul>
        @for (fallback of sources.calibration.fallbacks; track fallback) {
          <p class="risk-count">{{ fallback }}</p>
        }
        <p>
          These are transparent modelling choices, not a statistically validated fit. Public
          aggregates do not identify the real catchment, staff or inventory of any sample facility.
        </p>
      </section>
      <div class="provenance-layers">
        <article>
          <span>01 / PUBLIC</span>
          <h3>Official & international</h3>
          <p>
            Source URLs, access dates, reference years, units, publisher IDs and checksums retained.
          </p>
        </article>
        <article>
          <span>02 / DERIVED</span>
          <h3>Calibration & risk</h3>
          <p>
            Ratios and threshold results trace their input observations. Derivation does not confer
            official status.
          </p>
        </article>
        <article>
          <span>03 / SYNTHETIC</span>
          <h3>Facility operations</h3>
          <p>
            Demand, inventory, beds and attendance fill unavailable real-time feeds. No real patient
            data.
          </p>
        </article>
        <article>
          <span>04 / SIMULATION</span>
          <h3>Emergency scenarios</h3>
          <p>
            A separate provenance type is reserved. Emergency scenario execution is a later
            milestone.
          </p>
        </article>
      </div>
    }
  `,
})
export class DataSourcesPage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  data = signal<SourcesResponse | null>(null);
  error = signal('');
  filter = signal('');
  filteredRecords = computed(() =>
    (this.data()?.records || []).filter((row) =>
      `${row.country_id} ${row.label} ${row.indicator} ${row.year}`
        .toLowerCase()
        .includes(this.filter().toLowerCase()),
    ),
  );
  constructor() {
    this.route.queryParamMap
      .pipe(
        tap(() => {
          this.data.set(null);
          this.error.set('');
        }),
        switchMap((params) =>
          this.api.sources(params.get('country_id') || '').pipe(
            catchError(() => {
              this.error.set(
                'The public source cache could not be read. Check the backend and re-import the verified snapshots.',
              );
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((data) => this.data.set(data));
  }
}
