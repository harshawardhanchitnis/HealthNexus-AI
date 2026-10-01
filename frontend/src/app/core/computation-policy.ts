import { toObservable } from '@angular/core/rxjs-interop';
import { distinctUntilChanged, startWith } from 'rxjs';
import { NetworkApi } from './network-api';

// Start conservatively, then reload automatic reads when the server confirms
// unrestricted local mode. Repeated identical capability responses do not reload.
export function computationPolicy(api: NetworkApi) {
  return toObservable(api.districtOnly).pipe(startWith(api.districtOnly()), distinctUntilChanged());
}
