import { Component, computed, input, signal } from '@angular/core';
import { DecimalPipe, DatePipe } from '@angular/common';
import { Forecast } from '../core/forecast-models';

@Component({
  selector: 'app-forecast-chart',
  imports: [DecimalPipe, DatePipe],
  template: `
    <div class="forecast-legend">
      <span class="actual-key">Historical requested demand</span
      ><span class="forecast-key">Baseline Forecast</span
      ><span class="band-key">80% / 95% intervals</span>
    </div>
    <div class="forecast-plot">
      <svg
        viewBox="0 0 900 300"
        role="img"
        [attr.aria-label]="
          'Historical demand and ' +
          data().horizon +
          '-day forecast with empirical uncertainty intervals'
        "
      >
        @for (tick of [0, 0.5, 1]; track tick) {
          <line
            x1="50"
            x2="880"
            [attr.y1]="250 - tick * 215"
            [attr.y2]="250 - tick * 215"
            stroke="#e5ecec"
          />
          <text x="40" [attr.y]="254 - tick * 215" text-anchor="end" fill="#77858e" font-size="11">
            {{ max() * tick | number: '1.0-0' }}
          </text>
        }
        <path [attr.d]="band('lower95', 'upper95')" fill="#dce9f7" />
        <path [attr.d]="band('lower80', 'upper80')" fill="#b7d2f0" />
        @if (data().horizon === 1) {
          <line
            x1="880"
            x2="880"
            [attr.y1]="y(data().forecast[0].lower95)"
            [attr.y2]="y(data().forecast[0].upper95)"
            stroke="#b7d2f0"
            stroke-width="12"
          />
          <line
            x1="880"
            x2="880"
            [attr.y1]="y(data().forecast[0].lower80)"
            [attr.y2]="y(data().forecast[0].upper80)"
            stroke="#6b9cd2"
            stroke-width="6"
          />
        }
        <path [attr.d]="actualPath()" fill="none" stroke="#405868" stroke-width="2.5" />
        <path [attr.d]="forecastPath()" fill="none" stroke="#2267aa" stroke-width="3" />
        <line
          [attr.x1]="x(data().history.length - 1)"
          [attr.x2]="x(data().history.length - 1)"
          y1="20"
          y2="250"
          stroke="#8caaa2"
          stroke-dasharray="4 5"
        />
        <text
          [attr.x]="x(data().history.length - 1) - 8"
          y="17"
          text-anchor="end"
          font-size="11"
          fill="#667f78"
        >
          Forecast origin
        </text>
        @for(point of data().forecast; track point.date; let i = $index) {
          <circle class="forecast-point" [attr.cx]="x(data().history.length + i)" [attr.cy]="y(point.point)" r="4" fill="#2267aa" tabindex="0" (focus)="selected.set(i)" (mouseenter)="selected.set(i)" [attr.aria-label]="point.date + ': ' + point.point + ' ' + data().unit"><title>{{point.date}} · {{point.point | number:'1.2-2'}} {{data().unit}}</title></circle>
        }
        <text x="50" y="283" fill="#77858e" font-size="11">
          {{ data().history[0].date | date: 'dd MMM' }}
        </text>
        <text x="880" y="283" text-anchor="end" fill="#77858e" font-size="11">
          {{ data().forecast[data().forecast.length - 1].date | date: 'dd MMM yyyy' }}
        </text>
      </svg>
    </div>
    <div class="chart-readout" aria-live="polite">@if(activePoint(); as point) {<strong>{{point.date | date:'dd MMM yyyy'}}</strong><span>{{point.point | number:'1.2-2'}} {{data().unit}}</span><span>80% {{point.lower80 | number:'1.2-2'}}–{{point.upper80 | number:'1.2-2'}}</span><span>95% {{point.lower95 | number:'1.2-2'}}–{{point.upper95 | number:'1.2-2'}}</span>} @else {Hover or focus a forecast point to inspect exact daily ranges.}</div>
    <p class="chart-footnote">
      Intervals are empirical marginal daily ranges. They are not confidence scores or guarantees.
      Exact daily values are available below.
    </p>
  `,
})
export class ForecastChart {
  data = input.required<Forecast>();
  selected = signal<number | null>(null);
  activePoint = computed(() => this.selected() === null ? null : this.data().forecast[this.selected()!] ?? null);
  max = computed(
    () =>
      Math.max(
        1,
        ...this.data().history.map((p) => p.value),
        ...this.data().forecast.map((p) => p.upper95),
      ) * 1.08,
  );
  x(index: number) {
    return 50 + (index * 830) / (this.data().history.length + this.data().forecast.length - 1);
  }
  y(value: number) {
    return 250 - (value / this.max()) * 215;
  }
  actualPath() {
    return this.data()
      .history.map((p, i) => `${i ? 'L' : 'M'}${this.x(i)},${this.y(p.value)}`)
      .join(' ');
  }
  forecastPath() {
    const d = this.data();
    return (
      `M${this.x(d.history.length - 1)},${this.y(d.history[d.history.length - 1].value)} ` +
      d.forecast.map((p, i) => `L${this.x(d.history.length + i)},${this.y(p.point)}`).join(' ')
    );
  }
  band(low: 'lower80' | 'lower95', high: 'upper80' | 'upper95') {
    const d = this.data();
    const upper = d.forecast.map((p, i) => `${this.x(d.history.length + i)},${this.y(p[high])}`);
    const lower = d.forecast
      .map((p, i) => `${this.x(d.history.length + i)},${this.y(p[low])}`)
      .reverse();
    return 'M' + upper.join(' L') + ' L' + lower.join(' L') + ' Z';
  }
}
