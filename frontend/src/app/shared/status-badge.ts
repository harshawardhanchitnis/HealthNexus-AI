import { Component, input } from '@angular/core';
import { Status } from '../core/models';
@Component({
  selector: 'app-status',
  template: `<span [class]="'status ' + value().toLowerCase()"
    ><i></i>{{ value().replace('_', ' ') }}</span
  >`,
})
export class StatusBadge {
  value = input.required<Status>();
}
