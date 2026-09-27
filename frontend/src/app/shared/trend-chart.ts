import { Component, computed, input } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { Activity } from '../core/models';
@Component({
  selector: 'app-trend-chart',
  imports: [DecimalPipe],
  template: `<div class="trend-chart">
      <div class="chart-axis">
        <span>{{ maximum() | number: '1.0-0' }}</span
        ><span>{{ maximum() / 2 | number: '1.0-0' }}</span
        ><span>0</span>
      </div>
      <svg
        viewBox="0 0 650 175"
        preserveAspectRatio="none"
        role="img"
        aria-label="Daily patient footfall over the last 28 days"
      >
        <path
          d="M0 8H650 M0 85H650 M0 165H650"
          stroke="#e9eef0"
          stroke-dasharray="4 4"
          fill="none"
        />
        <path [attr.d]="area()" fill="#e0f3ed" />
        <path
          [attr.d]="line()"
          stroke="#149b7d"
          stroke-width="2.5"
          fill="none"
          vector-effect="non-scaling-stroke"
        />
        @for (point of points(); track $index) {
          <circle [attr.cx]="point.x" [attr.cy]="point.y" r="3" fill="#149b7d">
            <title>{{ point.label }}</title>
          </circle>
        }
      </svg>
    </div>
    <div class="chart-dates">
      <span>{{ data()[0]?.date }}</span
      ><span>28 days · synthetic observations</span
      ><span>{{ data()[data().length - 1]?.date }}</span>
    </div>`,
  styles: [
    `
      .trend-chart {
        display: flex;
        gap: 14px;
        height: 175px;
      }
      .chart-axis {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-size: 9px;
        color: #71858f;
        min-width: 36px;
      }
      .trend-chart svg {
        width: 100%;
        overflow: visible;
      }
      .chart-dates {
        display: flex;
        justify-content: space-between;
        font-size: 9px;
        color: #71858f;
        margin: 18px 0 0 50px;
      }
      @media (max-width: 500px) {
        .chart-dates span:nth-child(2) {
          display: none;
        }
      }
    `,
  ],
})
export class TrendChart {
  data = input.required<Activity[]>();
  maximum = computed(() => Math.max(1, ...this.data().map((d) => d.footfall)) * 1.15);
  points = computed(() =>
    this.data().map((d, i, all) => ({
      x: (i * 650) / Math.max(1, all.length - 1),
      y: 165 - (d.footfall / this.maximum()) * 157,
      label: `${d.date}: ${d.footfall.toLocaleString('en-IN')} visits`,
    })),
  );
  line = computed(() =>
    this.points()
      .map((p, i) => `${i ? 'L' : 'M'}${p.x},${p.y}`)
      .join(' '),
  );
  area = computed(() => `${this.line()} L650,165 L0,165 Z`);
}
