import { ApplicationRef, inject, Injectable } from '@angular/core';
import { PreloadingStrategy, Route } from '@angular/router';
import { catchError, filter, Observable, of, shareReplay, switchMap, take, timer } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SelectivePreloading implements PreloadingStrategy {
  private settled = inject(ApplicationRef).isStable.pipe(
    filter(Boolean), take(1), switchMap(() => timer(1000)),
    shareReplay({ bufferSize: 1, refCount: false }),
  );
  preload(route: Route, load: () => Observable<unknown>): Observable<unknown> {
    if (route.data?.['preload'] !== true) return of(null);
    // Angular 20's RouterPreloader also calls this for standalone loadComponent.
    // Importing a component does not instantiate it or call its API services.
    return this.settled.pipe(switchMap(load), catchError(() => of(null)));
  }
}
