import { Component, computed, inject, input } from '@angular/core';
import { ReadCache } from '../core/read-cache';

@Component({
  selector: 'app-read-notice',
  template: `@if (failed()) { <p class="cache-status" role="status">Refresh unavailable. Showing the last successfully loaded data for this selection.</p> }
    @else if (refreshing()) { <p class="cache-status" role="status">Refreshing…</p> }`,
  styles: `.cache-status { color: #526d83; font-size: .8rem; margin: .35rem 0 .75rem; }`,
})
export class ReadNotice {
  keys = input.required<string[]>();
  private cache = inject(ReadCache);
  failed = computed(() => this.keys().some(key => this.cache.state(key).failed));
  refreshing = computed(() => this.keys().some(key => this.cache.state(key).refreshing));
}
