import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({selector:'app-computation-notice',imports:[RouterLink],template:`
  <section class="empty-state" role="status">
    <h2>Select a district for live calculations</h2>
    <p>Nationwide browsing and the network map remain available. Live warnings, simulations and planning run within a district; cross-district planning can include another district in the same state.</p>
    <p>Choose a district above, or open the Pune demonstration.</p>
    <a class="button primary" routerLink="." [queryParams]="{country_id:'IN',state_id:'MH',district_id:'MH-PUNE',facility_id:null,scenario_id:null,run_id:null,donor_scope:'district'}" queryParamsHandling="merge">Select Pune</a>
    <a class="button secondary" routerLink="/geospatial" [queryParams]="{mode:'network',scenario_id:null,run_id:null,resource:null}" queryParamsHandling="merge">Browse network map</a>
  </section>`})
export class ComputationNotice {}
