import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NetworkApi } from './core/network-api';
import { Region, District, Country } from './core/models';
import { Subscription } from 'rxjs';
import { Icon } from './shared/icon';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icon],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private api = inject(NetworkApi);
  private router = inject(Router);
  private regionRequest?: Subscription;
  countries = signal<Country[]>([]);
  country = signal('IN');
  profile = signal('constrained');
  regions = signal<Region[]>([]);
  districts = signal<District[]>([]);
  state = signal('');
  district = signal('');
  menuOpen = signal(false);
  regionsError = signal(false);
  nav = [
    { path: '/overview', icon: 'dashboard', label: 'Overview' },
    { path: '/network', icon: 'network', label: 'Country network' },
    { path: '/facilities', icon: 'hospital', label: 'Facilities' },
    { path: '/supply', icon: 'box', label: 'Medicine & supply' },
    { path: '/warnings', icon: 'bell', label: 'Early Warning Centre' },
    { path: '/emergency', icon: 'pulse', label: 'Emergency Simulator' },
    { path: '/redistribution', icon: 'box', label: 'Redistribution Planner' },
    { path: '/copilot', icon: 'network', label: 'Resilience Copilot' },
    { path: '/forecasts', icon: 'chart', label: 'Forecasts' },
    { path: '/model-performance', icon: 'shield', label: 'Model performance' },
    { path: '/brics', icon: 'network', label: 'BRICS nodes' },
    { path: '/data-sources', icon: 'layers', label: 'Data sources' },
  ];
  constructor() {
    this.router.routerState.root.queryParamMap.subscribe((params) => {
      const nextCountry = params.get('country_id') || 'IN';
      const changed = nextCountry !== this.country();
      this.profile.set(params.get('profile') || 'constrained');
      this.country.set(nextCountry);
      this.state.set(params.get('state_id') || '');
      this.district.set(params.get('district_id') || '');
      if (changed || !this.regions().length) this.loadRegions();
    });
  }
  loadRegions() {
    this.regionsError.set(false);
    this.regionRequest?.unsubscribe();
    this.regions.set([]);
    this.districts.set([]);
    if (!this.countries().length)
      this.api.countries().subscribe({
        next: (data) => this.countries.set(data.items),
        error: () => this.regionsError.set(true),
      });
    this.regionRequest = this.api.regions(this.country()).subscribe({
      next: (data) => {
        this.regions.set(data.regions);
        this.districts.set(data.districts);
      },
      error: () => this.regionsError.set(true),
    });
  }
  changeProfile(event: Event) {
    this.router.navigate([], { queryParams: { profile: (event.target as HTMLSelectElement).value,
      scenario_id: null, run_id: null }, queryParamsHandling: 'merge' });
  }
  countryName() {
    return this.countries().find((c) => c.id === this.country())?.name || this.country();
  }
  changeCountry(event: Event) {
    this.router.navigate([this.scopeRoute()], {
      queryParams: { profile: this.profile(), country_id: (event.target as HTMLSelectElement).value },
    });
  }
  availableDistricts() {
    return this.districts().filter((d) => d.state_id === this.state());
  }
  changeState(event: Event) {
    this.router.navigate([this.scopeRoute()], {
      queryParams: {
        profile: this.profile(),
        country_id: this.country(),
        state_id: (event.target as HTMLSelectElement).value || null,
      },
    });
  }
  changeDistrict(event: Event) {
    this.router.navigate([this.scopeRoute()], {
      queryParams: {
        profile: this.profile(),
        country_id: this.country(),
        state_id: this.state() || null,
        district_id: (event.target as HTMLSelectElement).value || null,
      },
    });
  }
  private scopeRoute() {
    const path = this.router.url.split('?')[0];
    return [
      '/forecasts',
      '/model-performance',
      '/emergency',
      '/warnings',
      '/redistribution',
    ].includes(path)
      ? path
      : '/overview';
  }
}
