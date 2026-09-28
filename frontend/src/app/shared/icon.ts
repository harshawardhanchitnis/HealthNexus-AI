import { Component, input } from '@angular/core';
@Component({
  selector: 'app-icon',
  template: `<svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.6"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path [attr.d]="paths[name()] || paths['layers']" />
  </svg>`,
  styles: [
    `
      :host {
        display: inline-flex;
        width: 19px;
        height: 19px;
        flex-shrink: 0;
      }
      svg {
        width: 100%;
        height: 100%;
      }
    `,
  ],
})
export class Icon {
  name = input('layers');
  paths: Record<string, string> = {
    pulse: 'M2 12h5l3-8 4 16 3-8h5',
    dashboard: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
    network: 'M12 3v6 M5 15v-4h14v4 M9 3h6v4H9z M2 15h6v6H2z M16 15h6v6h-6z',
    hospital: 'M4 21V7h16v14 M9 7V3h6v4 M9 21v-5h6v5 M9 11h6 M12 8v6',
    box: 'M3 7l9-4 9 4v10l-9 4-9-4z M3 7l9 4 9-4 M12 11v10 M8 5l9 4',
    bell: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9 M10 21h4',
    layers: 'M2 7l10-5 10 5-10 5z M2 12l10 5 10-5 M2 17l10 5 10-5',
    arrow: 'M5 12h14 M14 7l5 5-5 5',
    refresh: 'M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 3 M18 18A8 8 0 0 1 5 15',
    bed: 'M3 4v16 M21 10v10 M3 16h18 M3 9h5v7 M8 10h9a4 4 0 0 1 4 4v2',
    users:
      'M16 21v-3a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v3 M9 10a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M17 3a4 4 0 0 1 0 8 M22 21v-3a4 4 0 0 0-4-4',
    filter: 'M3 5h18 M6 12h12 M10 19h4',
    info: 'M12 10v7 M12 7h.01 M22 12a10 10 0 1 0-20 0 10 10 0 0 0 20 0',
    search: 'M21 21l-5-5 M18 10a8 8 0 1 0-16 0 8 8 0 0 0 16 0',
    menu: 'M3 6h18 M3 12h18 M3 18h18',
    close: 'M6 6l12 12 M18 6L6 18',
    check: 'M5 12l4 4L19 6',
    shield: 'M12 2l8 4v6c0 5-8 10-8 10S4 17 4 12V6z M8 12l3 3 5-6',
    clock: 'M12 6v6l4 2 M22 12a10 10 0 1 0-20 0 10 10 0 0 0 20 0',
  };
}
