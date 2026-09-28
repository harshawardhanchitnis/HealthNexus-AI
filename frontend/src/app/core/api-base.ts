import { HttpInterceptorFn } from '@angular/common/http';

declare global { interface Window { HEALTHNEXUS_CONFIG?: {apiBaseUrl?: string}; } }
export const apiBaseInterceptor: HttpInterceptorFn = (request, next) => {
  const base = (window.HEALTHNEXUS_CONFIG?.apiBaseUrl || '').replace(/\/$/, '');
  if (base && !/^https:\/\//.test(base)) throw new Error('Production API base must use HTTPS.');
  return next(base && request.url.startsWith('/api/') ? request.clone({url:base+request.url}) : request);
};
