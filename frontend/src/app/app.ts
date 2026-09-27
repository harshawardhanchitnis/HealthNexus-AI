import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NetworkApi } from './core/network-api';
import { Region, District } from './core/models';
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
  regions = signal<Region[]>([]);
  districts = signal<District[]>([]);
  state = signal('');
  district = signal('');
  menuOpen = signal(false);
  regionsError = signal(false);
  nav = [
    { path: '/overview', icon: 'dashboard', label: 'Overview' },
    { path: '/network', icon: 'network', label: 'India network' },
    { path: '/facilities', icon: 'hospital', label: 'Facilities' },
    { path: '/supply', icon: 'box', label: 'Medicine & supply' },
    { path: '/alerts', icon: 'bell', label: 'Early warnings' },
  ];
  constructor() {
    this.loadRegions();
    this.router.routerState.root.queryParamMap.subscribe((params) => {
      this.state.set(params.get('state_id') || '');
      this.district.set(params.get('district_id') || '');
    });
  }
  loadRegions() {
    this.regionsError.set(false);
    this.api.regions().subscribe({
      next: (data) => {
        this.regions.set(data.regions);
        this.districts.set(data.districts);
      },
      error: () => this.regionsError.set(true),
    });
  }
  availableDistricts() {
    return this.districts().filter((d) => d.state_id === this.state());
  }
  changeState(event: Event) {
    this.router.navigate(['/overview'], {
      queryParams: { state_id: (event.target as HTMLSelectElement).value || null },
    });
  }
  changeDistrict(event: Event) {
    this.router.navigate(['/overview'], {
      queryParams: {
        state_id: this.state() || null,
        district_id: (event.target as HTMLSelectElement).value || null,
      },
    });
  }
}
