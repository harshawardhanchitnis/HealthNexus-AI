import { Component, input, signal } from '@angular/core';
import { DatePipe, DecimalPipe, PercentPipe } from '@angular/common';
import { WarningItem } from '../core/resilience-models';
@Component({
  selector: 'app-warning-cards',
  imports: [DatePipe, DecimalPipe, PercentPipe],
  template: ` <div class="warning-list">
    @for (w of items().slice(0, limit()); track w.warning_id) {
      <article class="warning-card" [attr.data-severity]="w.severity">
        <button
          class="warning-toggle"
          [attr.aria-expanded]="open() === w.warning_id"
          (click)="open.set(open() === w.warning_id ? '' : w.warning_id)"
        >
          <span class="severity-chip" [attr.data-severity]="w.severity">{{ w.severity }}</span>
          <span class="warning-main"
            ><strong
              >{{ label(w.warning_type) }}
              @if (w.resource_id) {
                · {{ w.resource_id }}
              }</strong
            ><small>{{ w.facility_name }}</small></span
          >
          <span class="warning-timing"
            >{{
              w.estimated_event_date ? (w.estimated_event_date | date: 'dd MMM') : 'Within 14 days'
            }}<small>{{
              w.model_based_probability === null
                ? 'Rule-derived'
                : (w.model_based_probability | percent: '1.1-1') + ' conditional risk'
            }}</small></span
          >
          <span class="warning-expand">{{ open() === w.warning_id ? '−' : '+' }}</span>
        </button>
        <p class="warning-reason">
          {{ w.explanation_factors[0]?.description }}
          <strong>{{ format(w.explanation_factors[0]?.value) }}</strong>
        </p>
        @if (open() === w.warning_id) {
          <div class="warning-details">
            <p>
              <strong>{{
                w.baseline_or_scenario === 'scenario' ? 'Scenario projection' : 'Baseline forecast'
              }}</strong>
              · {{ w.transition }}
              @if (w.baseline_severity) {
                (baseline {{ w.baseline_severity }})
              }
              · priority {{ w.priority_score | number: '1.1-1' }}
            </p>
            <dl class="warning-facts">
              <div>
                <dt>Current</dt>
                <dd>{{ w.current_value === null ? '—' : (w.current_value | number: '1.2-2') }}</dd>
              </div>
              <div>
                <dt>Threshold</dt>
                <dd>{{ w.threshold === null ? '—' : (w.threshold | number: '1.2-2') }}</dd>
              </div>
              <div>
                <dt>Projected</dt>
                <dd>
                  {{ w.predicted_value === null ? '—' : (w.predicted_value | number: '1.2-2') }}
                </dd>
              </div>
            </dl>
            <ul>
              @for (f of w.explanation_factors; track f.factor) {
                <li>
                  <strong>{{ label(f.factor) }}: {{ format(f.value) }}</strong>
                  <p>{{ f.description }}</p>
                </li>
              }
            </ul>
            <p>{{ w.recommended_next_step }}</p>
            <small
              >Origin {{ w.forecast_origin }} · {{ w.model_version }} ·
              {{ w.provenance['config_version'] }} · simulated operations</small
            >
          </div>
        }
      </article>
    } @empty {
      <div class="empty-state">No active warnings match these filters.</div>
    }
    @if (items().length > limit()) {
      <button class="button secondary" (click)="limit.set(limit() + 50)">
        Showing {{ limit() }} of {{ items().length }} · Show 50 more warnings
      </button>
    }
  </div>`,
})
export class WarningCards {
  items = input.required<WarningItem[]>();
  limit = signal(50);
  open = signal('');
  label(s: string) {
    return s.replaceAll('_', ' ').toLowerCase();
  }
  format(value: number | string | undefined) {
    return typeof value === 'number'
      ? value.toLocaleString('en-IN', { maximumFractionDigits: 2 })
      : value;
  }
}
