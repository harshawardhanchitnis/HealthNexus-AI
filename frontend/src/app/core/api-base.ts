import { HttpInterceptorFn } from '@angular/common/http';
import { retry, throwError, timer } from 'rxjs';

declare global { interface Window { HEALTHNEXUS_CONFIG?: {apiBaseUrl?: string}; } }
export const apiBaseInterceptor: HttpInterceptorFn = (request, next) => {
  const base = (window.HEALTHNEXUS_CONFIG?.apiBaseUrl || '').replace(/\/$/, '');
  if (base && !/^https:\/\//.test(base)) throw new Error('Production API base must use HTTPS.');
  return next(base && request.url.startsWith('/api/') ? request.clone({url:base+request.url}) : request).pipe(
    // Retry only a read explicitly rejected BEFORE it started. Never retry provider
    // quota errors, writes or ambiguous network failures.
    retry({count:3,delay:error => request.method === 'GET' && error.status === 429 &&
      error.error?.detail?.code === 'operational_busy' ? timer(2000) : throwError(() => error)}));
};
