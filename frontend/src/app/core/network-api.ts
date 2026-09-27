import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Alert, District, Facility, FacilityList, Overview, Region, Supply } from './models';
@Injectable({ providedIn: 'root' })
export class NetworkApi {
  private http = inject(HttpClient);
  private params(scope: Record<string, string | number>) {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(scope))
      if (value !== '') params = params.set(key, value);
    return params;
  }
  regions() {
    return this.http.get<{ regions: Region[]; districts: District[] }>('/api/regions');
  }
  overview(scope: Record<string, string>) {
    return this.http.get<Overview>('/api/overview', { params: this.params(scope) });
  }
  facilities(scope: Record<string, string | number>) {
    return this.http.get<FacilityList>('/api/facilities', { params: this.params(scope) });
  }
  facility(id: string) {
    return this.http.get<{ facility: Facility; alerts: Alert[]; as_of: string }>(
      '/api/facilities/' + encodeURIComponent(id),
    );
  }
  alerts(scope: Record<string, string>) {
    return this.http.get<{ items: Alert[]; total: number }>('/api/alerts', {
      params: this.params(scope),
    });
  }
  inventory(scope: Record<string, string>) {
    return this.http.get<{ items: Supply[] }>('/api/inventory', { params: this.params(scope) });
  }
}
