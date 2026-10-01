import { Injectable, signal } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { catchError, concat, defer, EMPTY, finalize, Observable, of, ReplaySubject, shareReplay, tap, throwError } from 'rxjs';

interface Entry {
  value: unknown;
  loadedAt: number;
  bytes: number;
  failedAt?: number;
}
export interface ReadState { refreshing: boolean; failed: boolean; }

/** Session-only reads. No provider conversations or mutable run handles belong here. */
@Injectable({ providedIn: 'root' })
export class ReadCache {
  private entries = new Map<string, Entry>();
  private flights = new Map<string, Observable<unknown>>();
  private revision = signal(0);
  private bytes = 0;
  private queue: Array<() => void> = [];
  private active = false;
  readonly maxEntries = 32;
  readonly maxBytes = 4 * 1024 * 1024;
  readonly maxEntryBytes = 1024 * 1024;

  key(url: string, params: HttpParams): string {
    // Preserve repeated parameter order, but canonicalize parameter-name order.
    return url + '?' + params.keys().sort().map(name =>
      (params.getAll(name) || []).map(value => encodeURIComponent(name) + '=' + encodeURIComponent(value)).join('&'),
    ).join('&');
  }

  state(key: string): ReadState {
    this.revision();
    return { refreshing: this.flights.has(key), failed: this.entries.get(key)?.failedAt !== undefined };
  }

  read<T>(key: string, load: () => Observable<T>, ttl = 60_000, force = false): Observable<T> {
    return defer(() => {
      const cached = ttl > 0 ? this.entries.get(key) : undefined;
      if (cached) {
        this.entries.delete(key);
        this.entries.set(key, cached); // LRU; scope changes select another key, never reinterpret a value.
        const fresh = Date.now() - cached.loadedAt < ttl;
        const coolingDown = cached.failedAt !== undefined && Date.now() - cached.failedAt < 15_000;
        if (!force && (fresh || coolingDown)) return of(cached.value as T);
      }
      const request = this.fetch(key, load, ttl).pipe(catchError(error => {
        // Only this key's last successful value may survive a refresh failure.
        return cached ? EMPTY : throwError(() => error);
      }));
      return cached ? concat(of(cached.value as T), request) : request;
    });
  }

  private fetch<T>(key: string, load: () => Observable<T>, ttl: number): Observable<T> {
    const existing = this.flights.get(key);
    if (existing) return existing as Observable<T>;
    // Sequence requested GETs through the low-memory server's single admission slot.
    // This schedules no prefetch and never retries a write or starts a computation.
    const result = new ReplaySubject<T>(1);
    const request = result.asObservable().pipe(shareReplay({ bufferSize: 1, refCount: false }));
    this.flights.set(key, request);
    this.changed();
    this.queue.push(() => {
      defer(load).pipe(
        tap(value => { if (ttl > 0) this.save(key, value); }),
        finalize(() => {
          this.flights.delete(key);
          this.active = false;
          this.changed();
          this.next();
        }),
      ).subscribe({
        next: value => result.next(value),
        complete: () => result.complete(),
        error: error => {
          const entry = this.entries.get(key);
          if (entry) entry.failedAt = Date.now();
          this.changed();
          result.error(error);
        },
      });
    });
    this.next();
    return request;
  }

  private next() {
    if (!this.active && this.queue.length) {
      this.active = true;
      this.queue.shift()!();
    }
  }

  private save(key: string, value: unknown) {
    const size = new TextEncoder().encode(JSON.stringify(value)).byteLength;
    const previous = this.entries.get(key);
    if (previous) this.bytes -= previous.bytes;
    this.entries.delete(key);
    if (size <= this.maxEntryBytes) {
      this.entries.set(key, { value, bytes: size, loadedAt: Date.now() });
      this.bytes += size;
    }
    while (this.entries.size > this.maxEntries || this.bytes > this.maxBytes) {
      const oldest = this.entries.keys().next().value!;
      this.bytes -= this.entries.get(oldest)!.bytes;
      this.entries.delete(oldest);
    }
    this.changed();
  }
  private changed() { this.revision.update(value => value + 1); }
}
