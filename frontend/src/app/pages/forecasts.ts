import { Component, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { catchError, of, switchMap, tap } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Facility } from '../core/models';
import { Forecast } from '../core/forecast-models';
import { ForecastChart } from '../shared/forecast-chart';
import { ReadNotice } from '../shared/read-notice';

@Component({
  selector: 'app-forecasts',
  imports: [DatePipe, DecimalPipe, PercentPipe, RouterLink, ForecastChart, ReadNotice],
  templateUrl: './forecasts.html',
})
export class ForecastsPage {
  private api = inject(NetworkApi);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  facilities = signal<Facility[]>([]);
  selected = signal('');
  resource = signal('PCM');
  horizon = signal(14);
  data = signal<Forecast | null>(null);
  error = signal('');
  loading = signal(true);
  resources = [
    { id: 'footfall', name: 'Patient footfall' },
    { id: 'admissions', name: 'Admissions requested' },
    { id: 'PCM', name: 'Paracetamol 500 mg' },
    { id: 'IVF', name: 'IV fluids' },
    { id: 'ORS', name: 'Oral rehydration salts' },
    { id: 'AMX', name: 'Amoxicillin 500 mg' },
    { id: 'IFA', name: 'Iron and folic acid' },
  ];
  constructor() {
    this.route.queryParamMap
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set('');
          this.data.set(null);
        }),
        switchMap((params) => {
          const country = params.get('country_id') || 'IN';
          this.resource.set(params.get('resource') || 'PCM');
          this.horizon.set(Number(params.get('horizon') || 14));
          return this.api
            .facilities({
              country_id: country,
              state_id: params.get('state_id') || '',
              district_id: params.get('district_id') || '',
              limit: 250,
            })
            .pipe(
              switchMap((list) => {
                this.facilities.set(list.items);
                const wanted = params.get('facility_id');
                const id = wanted || list.items[0]?.id || '';
                this.selected.set(id);
                if (!list.items.some((f) => f.id === id)) {
                  this.error.set(
                    'No matching facility in this geographic scope. Select a facility above.',
                  );
                  return of(null);
                }
                return this.api.forecast(id, this.resource(), country, this.horizon());
              }),
              catchError((err) => {
                this.error.set(
                  err.error?.detail ||
                    'Forecast unavailable. Check that historical data and models have been built.',
                );
                return of(null);
              }),
            );
        }),
        takeUntilDestroyed(),
      )
      .subscribe((data) => {
        this.data.set(data);
        this.loading.set(false);
      });
  }
  change(key: string, event: Event) {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { [key]: (event.target as HTMLSelectElement).value },
      queryParamsHandling: 'merge',
    });
  }
  facilityName() { return this.facilities().find(f => f.id === this.selected())?.name || this.selected(); }
  readKeys() {
    const p = this.route.snapshot.queryParamMap;
    return [this.api.readKey('/api/facilities', {country_id: p.get('country_id') || 'IN', state_id: p.get('state_id') || '', district_id: p.get('district_id') || '', limit:250}),
      this.api.forecastKey(this.selected(), this.resource(), p.get('country_id') || 'IN', this.horizon())];
  }
  label() {
    return this.resources.find((r) => r.id === this.resource())?.name || this.resource();
  }
}
