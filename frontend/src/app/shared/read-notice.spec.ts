import { TestBed } from '@angular/core/testing';
import { of, Subject, throwError } from 'rxjs';
import { ReadCache } from '../core/read-cache';
import { ReadNotice } from './read-notice';

describe('Non-blocking cache refresh notice', () => {
  it('reports only the selected dataset and clears failure after a successful refresh', () => {
    const cache = TestBed.inject(ReadCache); const fixture = TestBed.createComponent(ReadNotice);
    fixture.componentRef.setInput('keys',['Pune']);
    cache.read('Pune', () => of(1)).subscribe(); cache.read('Nagpur', () => of(2)).subscribe();
    cache.read('Nagpur', () => throwError(() => 'offline'),60_000,true).subscribe();
    fixture.detectChanges(); expect(fixture.nativeElement.textContent).not.toContain('unavailable');
    const source = new Subject<number>(); cache.read('Pune', () => source,60_000,true).subscribe(); fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Refreshing');
    source.error('offline'); fixture.detectChanges(); expect(fixture.nativeElement.textContent).toContain('last successfully loaded');
    cache.read('Pune', () => of(3),60_000,true).subscribe(); fixture.detectChanges(); expect(fixture.nativeElement.textContent.trim()).toBe('');
  });
});
