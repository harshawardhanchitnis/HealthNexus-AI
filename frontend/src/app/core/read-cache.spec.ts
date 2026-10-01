import { HttpParams } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { ReadCache } from './read-cache';

describe('Bounded session read cache', () => {
  let cache: ReadCache;
  let now: number;
  beforeEach(() => {
    cache = TestBed.inject(ReadCache); now = 100_000;
    spyOn(Date, 'now').and.callFake(() => now);
  });
  it('canonicalizes keys while retaining every response parameter', () => {
    const p = new HttpParams().set('district_id', 'MH-PUNE').set('profile', 'constrained');
    expect(cache.key('/api/overview', p)).toBe(cache.key('/api/overview', new HttpParams().set('profile', 'constrained').set('district_id', 'MH-PUNE')));
    for (const [name, value] of Object.entries({profile:'redistribution-ready', country_id:'IN', state_id:'MH', district_id:'MH-NAGPUR', search:'hospital', status:'WATCH', offset:15, limit:5, resource:'PCM', horizon:7})) {
      expect(cache.key('/api/overview', p.set(name, value))).not.toBe(cache.key('/api/overview', p));
    }
    expect(cache.key('/api/facilities', p)).not.toBe(cache.key('/api/overview', p));
  });
  it('deduplicates concurrent subscriptions, even when the first consumer leaves', () => {
    const source = new Subject<number>(); const load = jasmine.createSpy().and.returnValue(source);
    const first = cache.read('pune', load).subscribe(); first.unsubscribe();
    const received: number[] = []; cache.read<number>('pune', load).subscribe(v => received.push(v));
    expect(load).toHaveBeenCalledTimes(1); source.next(42); source.complete();
    expect(received).toEqual([42]);
  });
  it('serves a fresh cached value synchronously with no request', () => {
    const load = jasmine.createSpy().and.returnValue(of(42)); cache.read('pune', load).subscribe();
    const received: number[] = []; cache.read<number>('pune', load).subscribe(v => received.push(v));
    expect(received).toEqual([42]); expect(load).toHaveBeenCalledTimes(1);
  });
  it('emits stale data immediately, shares one refresh, then replaces it', () => {
    cache.read('pune', () => of(42)).subscribe(); now += 60_001;
    const source = new Subject<number>(); const load = jasmine.createSpy().and.returnValue(source);
    const values: number[] = []; cache.read<number>('pune', load).subscribe(v => values.push(v));
    cache.read('pune', load).subscribe();
    expect(values).toEqual([42]); expect(cache.state('pune').refreshing).toBeTrue();
    source.next(43); source.complete(); expect(values).toEqual([42, 43]);
    expect(load).toHaveBeenCalledTimes(1);
    cache.read<number>('pune', load).subscribe(v => expect(v).toBe(43));
  });
  it('retains stale data on refresh error and cools down repeated failed reads', () => {
    cache.read('pune', () => of(42)).subscribe(); now += 60_001;
    const load = jasmine.createSpy().and.returnValue(throwError(() => new Error('offline')));
    const values: number[] = []; let failed = false;
    cache.read<number>('pune', load).subscribe({next:v => values.push(v), error:() => failed = true});
    expect(values).toEqual([42]); expect(failed).toBeFalse(); expect(cache.state('pune').failed).toBeTrue();
    cache.read('pune', load).subscribe(); expect(load).toHaveBeenCalledTimes(1);
    now += 15_001; cache.read('pune', () => of(43)).subscribe();
    expect(cache.state('pune').failed).toBeFalse();
  });
  it('explicit refresh bypasses fresh TTL and failure cooldown while retaining visible data', () => {
    cache.read('pune', () => of(42)).subscribe();
    const values: number[] = [];
    cache.read<number>('pune', () => of(43), 60_000, true).subscribe(v => values.push(v));
    expect(values).toEqual([42, 43]);
    cache.read('pune', () => throwError(() => 'offline'), 60_000, true).subscribe();
    cache.read<number>('pune', () => of(44), 60_000, true).subscribe(v => values.push(v));
    expect(values.slice(-2)).toEqual([43, 44]);
  });
  it('isolates profiles and districts rather than reinterpreting another selection', () => {
    for (const key of ['constrained:Pune', 'ready:Pune', 'ready:Nagpur']) cache.read(key, () => of(key)).subscribe();
    for (const key of ['constrained:Pune', 'ready:Pune', 'ready:Nagpur']) cache.read<string>(key, () => { throw new Error('should be cached'); }).subscribe(v => expect(v).toBe(key));
  });
  it('never retains mutable reads with TTL zero', () => {
    const load = jasmine.createSpy().and.returnValue(of(1));
    cache.read('run:actual', load, 0).subscribe(); cache.read('run:actual', load, 0).subscribe();
    expect(load).toHaveBeenCalledTimes(2);
  });
  it('propagates first-load failures and permits a new attempt', () => {
    let failed = false; cache.read('new', () => throwError(() => 'bad')).subscribe({error:() => failed = true});
    expect(failed).toBeTrue(); cache.read('new', () => of(42)).subscribe(v => expect(v).toBe(42));
  });
  it('sequences actual reads without prefetch, capturing the requested scope', () => {
    const a = new Subject<number>(); const b = new Subject<number>(); const loadB = jasmine.createSpy().and.returnValue(b);
    const unread = jasmine.createSpy().and.returnValue(of(99)); cache.read('unvisited', unread);
    cache.read('Pune', () => a).subscribe(); cache.read('Nagpur', loadB).subscribe();
    expect(loadB).not.toHaveBeenCalled(); expect(unread).not.toHaveBeenCalled();
    a.next(1); a.complete(); expect(loadB).toHaveBeenCalledTimes(1); b.next(2); b.complete();
  });
  it('bounds entries using LRU and does not retain oversized values', () => {
    const load = jasmine.createSpy().and.returnValue(of('value'));
    for (let i = 0; i < 32; i++) cache.read(String(i), load).subscribe();
    cache.read('0', load).subscribe(); cache.read('32', load).subscribe();
    cache.read('0', load).subscribe(); expect(load).toHaveBeenCalledTimes(33);
    cache.read('1', load).subscribe(); expect(load).toHaveBeenCalledTimes(34);
    const huge = jasmine.createSpy().and.returnValue(of('x'.repeat(cache.maxEntryBytes)));
    cache.read('huge', huge).subscribe(); cache.read('huge', huge).subscribe(); expect(huge).toHaveBeenCalledTimes(2);
  });
  it('bounds total UTF-8 payload bytes as well as entry count', () => {
    const load = jasmine.createSpy().and.returnValue(of('é'.repeat(400_000)));
    for (let i = 0; i < 6; i++) cache.read(String(i), load).subscribe();
    cache.read('5', load).subscribe(); expect(load).toHaveBeenCalledTimes(6);
    cache.read('0', load).subscribe(); expect(load).toHaveBeenCalledTimes(7);
  });
});
