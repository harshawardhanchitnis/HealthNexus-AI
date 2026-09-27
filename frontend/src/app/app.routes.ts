import { Routes } from '@angular/router';
export const routes: Routes = [
  {
    path: 'data-sources',
    loadComponent: () => import('./pages/data-sources').then((m) => m.DataSourcesPage),
  },
  { path: 'brics', loadComponent: () => import('./pages/brics').then((m) => m.BricsPage) },
  { path: '', redirectTo: 'overview', pathMatch: 'full' },
  ...['overview', 'network', 'facilities', 'supply', 'alerts'].map((page) => ({
    path: page,
    loadComponent: () => import('./pages/dashboard').then((m) => m.Dashboard),
    data: { page },
  })),
  {
    path: 'facilities/:id',
    loadComponent: () => import('./pages/facility').then((m) => m.FacilityPage),
  },
  { path: 'about', loadComponent: () => import('./pages/about').then((m) => m.AboutPage) },
  { path: '**', redirectTo: 'overview' },
];
