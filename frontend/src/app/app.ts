import { afterNextRender, Component, HostListener, Injector, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { NetworkApi } from './core/network-api';
import { Region, District, Country } from './core/models';
import { Subscription } from 'rxjs';
import { Icon } from './shared/icon';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, Icon],
  templateUrl: './app.html',
  styleUrl: './shell.scss',
})
export class App {
  private api = inject(NetworkApi);
  private router = inject(Router);
  private injector = inject(Injector);
  private regionRequest?: Subscription;
  countries = signal<Country[]>([]);
  country = signal('IN');
  profile = signal('constrained');
  regions = signal<Region[]>([]);
  districts = signal<District[]>([]);
  state = signal('');
  district = signal('');
  menuOpen = signal(false);
  filtersOpen = signal(false);
  mobile = signal(window.innerWidth < 1100);
  regionsError = signal(false);
  demo = signal(false);
  journey = [
    {path:'/overview',label:'1 · Network'}, {path:'/forecasts',label:'2 · Forecast'},
    {path:'/emergency',label:'3 · Stress-test'}, {path:'/warnings',label:'4 · Warnings'},
    {path:'/redistribution',label:'5 · Redistribute'}, {path:'/brics',label:'6 · Federation'},
    {path:'/copilot',label:'7 · Offline summary'},
  ];
  nav = [
    { path: '/geospatial', icon: 'layers', label: 'Geospatial Command' },
    { path: '/overview', icon: 'dashboard', label: 'Command Centre' },
    { path: '/network', icon: 'network', label: 'Country network' },
    { path: '/facilities', icon: 'hospital', label: 'Facilities' },
    { path: '/supply', icon: 'box', label: 'Medicine & supply' },
    { path: '/forecasts', icon: 'chart', label: 'Forecasts' },
    { path: '/warnings', icon: 'bell', label: 'Early Warnings' },
    { path: '/emergency', icon: 'pulse', label: 'Emergency Simulator' },
    { path: '/redistribution', icon: 'box', label: 'Redistribution Planner' },
    { path: '/copilot', icon: 'network', label: 'Resilience Copilot' },
    { path: '/brics', icon: 'network', label: 'Federated Intelligence' },
    { path: '/model-performance', icon: 'shield', label: 'Model Performance' },
    { path: '/data-sources', icon: 'layers', label: 'Data Sources' },
  ];
  constructor() {
    this.router.routerState.root.queryParamMap.subscribe((params) => {
      const nextCountry = params.get('country_id') || 'IN';
      const changed = nextCountry !== this.country();
      this.profile.set(params.get('profile') || 'constrained');
      this.demo.set(params.get('demo') === '1');
      this.country.set(nextCountry);
      this.state.set(params.get('state_id') || '');
      this.district.set(params.get('district_id') || '');
      if (changed || !this.regions().length) this.loadRegions();
    });
  }
  loadDemo(profile: string) {
    this.router.navigate(['/overview'], {queryParams:{country_id:'IN',state_id:'MH',district_id:'MH-PUNE',profile,demo:'1'}});
  }
  exitDemo() { this.router.navigate([], {queryParams:{demo:null},queryParamsHandling:'merge'}); }
  nextStep() {
    const index = this.journey.findIndex(step => this.router.url.split('?')[0] === step.path);
    return this.journey[index + 1] || null;
  }
  @HostListener('window:resize') resize() { this.mobile.set(window.innerWidth < 1100); }
  toggleMenu() {
    this.menuOpen.set(!this.menuOpen());
    afterNextRender(() => {
      if (this.menuOpen()) (document.querySelector('.sidebar a') as HTMLElement)?.focus();
      else (document.querySelector('.menu-button') as HTMLElement)?.focus();
    }, {injector:this.injector});
  }
  @HostListener('document:keydown', ['$event']) keyNavigation(event: KeyboardEvent) {
    if (!this.mobile() || !this.menuOpen()) return;
    if (event.key === 'Escape') { event.preventDefault(); this.toggleMenu(); }
    if (event.key === 'Tab') {
      const links = Array.from(document.querySelectorAll<HTMLElement>('.sidebar a, .drawer-close'));
      const first = links[0], last = links[links.length-1];
      if (event.shiftKey && document.activeElement === first) {event.preventDefault(); last?.focus();}
      else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
    }
  }
  skipToContent(event: Event) {
    event.preventDefault();
    const main = document.getElementById('main');
    main?.focus();
    main?.scrollIntoView({block:'start'});
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
  scopeName() {
    return this.districts().find(d => d.id === this.district())?.name ||
      this.regions().find(r => r.id === this.state())?.name || 'National scope';
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
      '/geospatial',
    ].includes(path)
      ? path
      : '/overview';
  }
}
