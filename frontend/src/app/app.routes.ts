import { Routes } from '@angular/router';
export const routes: Routes = [
  {path:'geospatial',loadComponent:()=>import('./pages/geospatial').then(m=>m.GeospatialPage)},
  { path: 'copilot', loadComponent: () => import('./pages/copilot').then((m) => m.CopilotPage) },
  {
    path: 'redistribution',
    loadComponent: () => import('./pages/redistribution').then((m) => m.RedistributionPage),
  },
  {
    path: 'emergency',
    loadComponent: () => import('./pages/emergency').then((m) => m.EmergencyPage),
  },
  { path: 'warnings', data: { preload: true }, loadComponent: () => import('./pages/warnings').then((m) => m.WarningsPage) },
  {
    path: 'forecasts',
    data: { preload: true },
    loadComponent: () => import('./pages/forecasts').then((m) => m.ForecastsPage),
  },
  {
    path: 'model-performance',
    data: { preload: true },
    loadComponent: () => import('./pages/model-performance').then((m) => m.ModelPerformancePage),
  },
  {
    path: 'data-sources',
    data: { preload: true },
    loadComponent: () => import('./pages/data-sources').then((m) => m.DataSourcesPage),
  },
  { path: 'brics', loadComponent: () => import('./pages/brics').then((m) => m.BricsPage) },
  { path: '', redirectTo: 'overview', pathMatch: 'full' },
  ...['overview', 'network', 'facilities', 'supply', 'alerts'].map((page) => ({
    path: page,
    loadComponent: () => import('./pages/dashboard').then((m) => m.Dashboard),
    data: { page, preload: true },
  })),
  {
    path: 'facilities/:id',
    data: { preload: true },
    loadComponent: () => import('./pages/facility').then((m) => m.FacilityPage),
  },
  { path: 'about', loadComponent: () => import('./pages/about').then((m) => m.AboutPage) },
  { path: '**', redirectTo: 'overview' },
];
