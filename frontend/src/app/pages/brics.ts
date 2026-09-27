import { Component, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Country, Observation } from '../core/models';
import { Icon } from '../shared/icon';
@Component({
  selector: 'app-brics',
  imports: [RouterLink, DecimalPipe, Icon],
  template: `
    <div class="page-heading">
      <div>
        <div class="eyebrow">BRICS / COUNTRY NODES</div>
        <h1>Five perspectives. Shared learning ahead.</h1>
        <p>
          India leads the detailed showcase. Each country keeps its own operational data partition.
        </p>
      </div>
      <span class="subtle-tag">COUNTRY-LOCAL FORECASTING · PHASE 3</span>
    </div>
    <div class="info-banner">
      <app-icon name="network" />
      <div>
        <strong>Domestic resources. International model collaboration.</strong><br />Physical
        redistribution will stay within each nation. Future federated rounds will exchange model
        updates between country nodes. Local forecasting is implemented; federated training and
        aggregation are not.
      </div>
    </div>
    @if (error()) {
      <div class="empty-state" role="alert">{{ error() }}</div>
    } @else if (!countries().length) {
      <div class="loading-state">Loading country nodes…</div>
    }
    <div class="node-grid">
      @for (country of countries(); track country.id) {
        <section class="panel node-card">
          <div class="node-header">
            <span class="node-code">{{ country.id }}</span
            ><span class="subtle-tag">{{
              country.detailed ? 'DETAILED SHOWCASE' : 'REPRESENTATIVE NODE'
            }}</span>
          </div>
          <h2>{{ country.name }}</h2>
          <p>
            {{
              country.detailed
                ? 'All 36 states / UTs · 207 fictional facilities'
                : 'Two sample regions · six fictional facilities'
            }}
          </p>
          <dl>
            @for (indicator of ['WHS6_102', 'HWF_0001']; track indicator) {
              @if (latest(country.id, indicator); as row) {
                <div>
                  <dt>
                    {{ indicator === 'WHS6_102' ? 'Beds / 10,000' : 'Doctors / 10,000'
                    }}<small>WHO · {{ row.year }}</small>
                  </dt>
                  <dd>{{ row.value | number: '1.0-2' }}</dd>
                </div>
              }
            }
          </dl>
          <p class="node-training">
            Federated rounds: not started<br />Local forecast evaluation:
            <a routerLink="/model-performance" [queryParams]="{ country_id: country.id }"
              >view saved metrics →</a
            >
          </p>
          <a
            routerLink="/overview"
            [queryParams]="{ country_id: country.id }"
            class="button secondary"
            >Explore {{ country.name }} <app-icon name="arrow"
          /></a>
        </section>
      }
    </div>
    <section class="panel prose calibration-panel">
      <h2>A federation-ready data layout</h2>
      <p>
        These are logical nodes in one local prototype, not deployed national infrastructure. Public
        aggregate indicators may be shared for calibration. Generated operational snapshots are kept
        separately per country and no global raw training dataset is created.
      </p>
      <p>
        The five countries are the configured hackathon scope, not an exhaustive representation of
        current BRICS membership. A later FedAvg demonstration will report real round metrics and
        update-only transfers.
      </p>
    </section>
  `,
})
export class BricsPage {
  private api = inject(NetworkApi);
  countries = signal<Country[]>([]);
  records = signal<Observation[]>([]);
  error = signal('');
  constructor() {
    forkJoin({ countries: this.api.countries(), sources: this.api.sources() }).subscribe({
      next: (data) => {
        this.countries.set(data.countries.items);
        this.records.set(data.sources.records);
      },
      error: () =>
        this.error.set(
          'Country nodes or public sources could not be loaded. Check the backend and source cache.',
        ),
    });
  }
  latest(country: string, indicator: string) {
    return this.records()
      .filter((row) => row.country_id === country && row.indicator === indicator)
      .sort((a, b) => b.year - a.year)[0];
  }
}
