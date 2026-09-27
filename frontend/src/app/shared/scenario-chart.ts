import { Component, computed, input } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Forecast } from '../core/forecast-models';
@Component({
  selector: 'app-scenario-chart',
  imports: [DecimalPipe],
  template: `<div class="twin-legend">
      @if (history().length) {
        <span class="history-key">History</span>
      }
      <span class="baseline-key">Baseline forecast</span
      ><span class="scenario-key">Scenario projection</span
      ><span class="uncertainty-key">Conditional 95% ranges</span>
    </div>
    <svg
      class="twin-chart"
      viewBox="0 0 900 290"
      role="img"
      [attr.aria-label]="
        label() +
        ': baseline and scenario with conditional uncertainty. Exact values in the timeline below.'
      "
    >
      @for (t of [0, 0.5, 1]; track t) {
        <line x1="55" x2="875" [attr.y1]="y(max() * t)" [attr.y2]="y(max() * t)" stroke="#e2ebed" />
        <text x="45" [attr.y]="y(max() * t) + 4" text-anchor="end" fill="#64777f" font-size="12">
          {{ max() * t | number: '1.0-0' }}
        </text>
      }
      <path [attr.d]="band(baseline())" fill="#d0e9e1" />
      <path [attr.d]="band(scenario())" fill="#f4d9cf" opacity=".65" />
      <path [attr.d]="historyPath()" stroke="#637580" stroke-width="2.5" fill="none" />
      <path [attr.d]="line(baseline())" stroke="#118a71" stroke-width="3" fill="none" />
      <path
        [attr.d]="line(scenario())"
        stroke="#bd5933"
        stroke-width="3"
        stroke-dasharray="7 4"
        fill="none"
      />
      <line
        [attr.x1]="x(history().length - 1)"
        [attr.x2]="x(history().length - 1)"
        y1="20"
        y2="245"
        stroke="#8e9fa2"
        stroke-dasharray="3 5"
      />
      <text x="55" y="276" fill="#64777f" font-size="12">
        {{ history()[0]?.date || baseline()[0]?.date }}
      </text>
      <text x="875" y="276" text-anchor="end" fill="#64777f" font-size="12">
        {{ baseline()[baseline().length - 1]?.date }}
      </text>
    </svg>`,
})
export class ScenarioChart {
  history = input<Forecast['history']>([]);
  baseline = input.required<Forecast['forecast']>();
  scenario = input.required<Forecast['forecast']>();
  label = input('Patient demand');
  max = computed(
    () =>
      Math.max(
        1,
        ...this.history().map((p) => p.value),
        ...this.baseline().map((p) => p.upper95),
        ...this.scenario().map((p) => p.upper95),
      ) * 1.08,
  );
  x(i: number) {
    return (
      55 + (820 * Math.max(0, i)) / Math.max(1, this.history().length + this.baseline().length - 1)
    );
  }
  y(v: number) {
    return 245 - (v / this.max()) * 215;
  }
  historyPath() {
    return this.history()
      .map((p, i) => `${i ? 'L' : 'M'}${this.x(i)},${this.y(p.value)}`)
      .join(' ');
  }
  line(points: Forecast['forecast']) {
    return points
      .map((p, i) => `${i ? 'L' : 'M'}${this.x(this.history().length + i)},${this.y(p.point)}`)
      .join(' ');
  }
  band(points: Forecast['forecast']) {
    const up = points.map((p, i) => `${this.x(this.history().length + i)},${this.y(p.upper95)}`);
    const lo = points
      .map((p, i) => `${this.x(this.history().length + i)},${this.y(p.lower95)}`)
      .reverse();
    return 'M' + up.join(' L') + ' L' + lo.join(' L') + ' Z';
  }
}
