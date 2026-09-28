import { Component, inject, signal, OnDestroy } from '@angular/core';
import { DecimalPipe, PercentPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { NetworkApi } from '../core/network-api';
import { Country } from '../core/models';
import { FederationNode, FederationRun, FederationStatus, FederationRequest } from '../core/federation-models';
import { Icon } from '../shared/icon';

@Component({
  selector: 'app-brics',
  imports: [RouterLink, DecimalPipe, PercentPipe, FormsModule, Icon],
  styleUrl: './brics.scss',
  template: `
    <div class="page-heading">
      <div><div class="eyebrow">BRICS / EXPERIMENTAL COLLABORATION</div>
        <h1>Federated Intelligence</h1>
        <p>Five country models learn together. Operational records stay at each logical node.</p>
      </div><span class="subtle-tag">MODEL UPDATES ONLY</span>
    </div>
    <div class="info-banner"><app-icon name="network" /><div>
      <strong>Shared learning. Domestic redistribution.</strong><br />
      This separate footfall MLP exchanges parameters and aggregate metadata. Existing operational
      forecasts and medicine redistribution remain country-local and unchanged.
    </div></div>
    @if (error()) { <div class="empty-state" role="alert">{{ error() }}</div> }
    <details class="panel federation-controls" [open]="!run() || busy()"><summary>Federation controls · inspect or run an explicit local experiment</summary>
      <div class="controls-title"><h2>Train across five logical nodes</h2>
        <p>Seed 42 · CPU PyTorch · {{ status()?.parameter_count | number }} parameters</p></div>
      <div class="forecast-controls">
        <label>Rounds<select [(ngModel)]="roundCount" [disabled]="busy()">
          @for (n of [1,2,3,4,5,6,7,8,9,10]; track n) { <option [ngValue]="n">{{n}}</option> }
        </select></label>
        <label>Local epochs<select [(ngModel)]="localEpochs" [disabled]="busy()">
          @for (n of [1,2,3,4,5]; track n) { <option [ngValue]="n">{{n}}</option> }
        </select></label>
        <label>Aggregation<select [(ngModel)]="policy" [disabled]="busy()">
          <option value="sample-weighted">Standard FedAvg · sample weighted</option>
          <option value="balanced-country">Balanced country · equal weights</option>
        </select></label>
        <button class="button primary" (click)="start()" [disabled]="busy() || !status()?.available || !ready()">
          <app-icon name="network" /> {{ busy() ? 'Training locally…' : 'Run Federated Training' }}
        </button>
      </div>
      @if (!status()) { <p role="status">Loading local federation capabilities and saved evidence…</p> }
      @else if (!status()?.available) { <p class="muted">CPU training runtime unavailable. Install the documented federation dependency on the backend.</p> }
      @if (run(); as current) {
        <div class="run-progress" aria-live="polite"><strong>{{ current.status === 'completed' ? 'Global model updated' : 'Round ' + current.current_round + '/' + current.config.rounds }}</strong>
          <span>{{ current.message }}</span><small>{{ current.policy === 'sample-weighted' ? 'Standard sample-weighted FedAvg' : 'Balanced-country averaging' }} · {{current.config.rounds}} rounds / {{current.config.local_epochs}} local epoch(s)</small><details><summary>Run identity</summary>{{current.run_id}}</details>
        </div>
      }
    </details>
    @if(run(); as measured) {<section class="federation-summary" aria-label="Measured federation summary">
      <article><span>Logical nodes</span><strong>{{measured.nodes.length}}</strong><small>Country-local training</small></article>
      <article><span>Rounds / epochs</span><strong>{{measured.config.rounds}} / {{measured.config.local_epochs}}</strong><small>Seed {{measured.config.seed}}</small></article>
      <article><span>Model parameters</span><strong>{{measured.parameter_count | number}}</strong><small>Experimental footfall MLP</small></article>
      <article><span>Raw records shared</span><strong>{{measured.raw_records_shared}}</strong><small>Parameter updates only</small></article>
    </section>}
    <section class="federation-flow panel" aria-label="Five countries send model parameters to FedAvg and receive global parameters">
      <div class="flow-nodes">@for (country of countries(); track country.id) {<span>{{country.name}}</span>}</div>
      <div class="flow-arrow"><span>Parameter updates →</span><small>← Global weights</small></div>
      <div class="flow-global"><app-icon name="network"/><strong>{{run()?.policy === 'balanced-country' ? 'Balanced averaging' : 'FedAvg'}}</strong><span>Global footfall model</span></div>
      <div class="privacy-counter"><strong>{{ run()?.raw_records_shared ?? status()?.raw_records_shared ?? '—' }}</strong><span>Raw operational records shared</span></div>
    </section>
    <div class="node-grid">
      @for (country of countries(); track country.id) {
        <section class="panel node-card"><div class="node-header"><span class="node-code">{{country.id}}</span>
          <span class="subtle-tag">{{country.detailed ? 'DETAILED SHOWCASE' : 'REPRESENTATIVE NODE'}}</span></div>
          <h2>{{country.name}}</h2>
          @if (node(country.id); as n) {
            <p>{{n.facility_count | number}} fictional facilities · {{n.history_days}} historical days</p>
            <dl><div><dt>Local training examples</dt><dd>{{n.local_samples | number}}</dd></div>
              <div><dt>Local-only test WAPE</dt><dd>{{n.local_only?.wape == null ? 'Not trained' : (n.local_only?.wape | percent:'1.4-4')}}</dd></div>
              <div><dt>Federated test WAPE</dt><dd>{{n.federated_global?.wape == null ? 'Not trained' : (n.federated_global?.wape | percent:'1.4-4')}}</dd></div>
              <div><dt>Latest model update</dt><dd>{{latestBytes(country.id) | number}} B</dd></div>
              <div><dt>Raw records shared</dt><dd>{{n.raw_records_shared}}</dd></div></dl>
          }
          @if(node(country.id); as measured) {@if(measured.wape_change_vs_local != null) {<p class="node-outcome" [class.degraded]="measured.change === 'degraded'"><strong>{{measured.change}}</strong> {{measured.wape_change_vs_local! * 100 | number:'1.4-4'}} pp vs local</p>}}
          <p class="node-training">{{nodeState(country.id)}}</p>
          <a routerLink="/overview" [queryParams]="{profile:api.profile(),country_id:country.id}" class="button secondary">Explore {{country.name}} <app-icon name="arrow"/></a>
        </section>
      }
    </div>
    @if (run(); as current) {
      <section class="panel federation-results"><div class="results-heading"><div><h2>Measured collaboration</h2>
        <p>{{current.model_version}} · {{current.policy}}</p></div>
        @if (current.saved_demo) { <span class="subtle-tag">SAVED MEASURED RUN · SEED 42</span> }
        @else if (current.status === 'completed') { <button class="button secondary" (click)="discard()">Discard run</button> }
      </div>
      <div class="run-totals"><span><strong>{{current.training_seconds == null ? 'In progress' : (current.training_seconds | number:'1.2-2') + ' s'}}</strong>Total local run</span>
        <span><strong>{{current.bytes_exchanged | number}} B</strong>Logical boundary traffic</span>
        <span><strong>{{current.global_test?.wape | percent:'1.2-2'}}</strong>Global held-out test WAPE</span></div>
      @if (current.rounds.length) {
        <div class="round-timeline" aria-label="Measured federation rounds">@for(round of current.rounds; track round.round) {<div><small>Round {{round.round}}</small><strong>{{round.global_validation.wape | percent:'1.2-2'}}</strong><span>Validation WAPE</span></div>}</div>
        <svg class="round-chart" viewBox="0 0 640 130" role="img" aria-label="Measured global validation WAPE over federation rounds">
          <line x1="20" y1="112" x2="620" y2="112" stroke="#d5e2e3" />
          <polyline [attr.points]="chartPoints()" fill="none" stroke="#266caa" stroke-width="3" />
          <text x="20" y="128">Round 0</text><text x="535" y="128">Round {{current.rounds.length-1}}</text>
        </svg>
        <div class="table-wrap"><table><thead><tr><th>Round</th><th>Global validation WAPE</th><th>Global MAE (visits)</th><th>Update bytes</th><th>Raw records shared</th></tr></thead><tbody>
          @for (r of current.rounds; track r.round) {<tr><td>{{r.round}}</td><td>{{r.global_validation.wape | percent:'1.2-2'}}</td><td>{{r.global_validation.mae | number:'1.2-2'}}</td><td>{{r.update_bytes | number}}</td><td>{{r.raw_records_shared}}</td></tr>}
        </tbody></table></div>
      }
      @if (current.status === 'completed') {
        <h2 class="comparison-title">Country test comparison · lower WAPE is better</h2>
        <div class="table-wrap"><table><thead><tr><th>Country</th><th>Local-only WAPE</th><th>Initial-global WAPE</th><th>Federated-global WAPE</th><th>Change vs local</th><th>Federation weight</th></tr></thead><tbody>
          @for (n of current.nodes; track n.country_id) {<tr><td>{{countryName(n.country_id)}}</td><td>{{n.local_only?.wape | percent:'1.4-4'}}</td><td>{{n.initial_global?.wape | percent:'1.4-4'}}</td><td>{{n.federated_global?.wape | percent:'1.4-4'}}</td><td>{{n.change}} ({{(n.wape_change_vs_local ?? 0)*100 | number:'1.4-4'}} pp)</td><td>{{weight(n.country_id) | percent:'1.2-2'}}</td></tr>}
        </tbody></table></div>
        <p class="muted">Local-only models receive the same total local epochs. Test data never selects weights. Global metrics combine aggregate errors; India has substantially more samples. Foreign nodes have six representative facilities each.</p>
        <p>Federated learning does not guarantee that every participant improves in every run. India's slight degradation remains visible above.</p>
      }
      <details class="training-trace"><summary>Actual training events ({{current.events.length}})</summary>
        <ol>@for (event of current.events; track $index) {<li><strong>Round {{event.round}} · {{event.stage}}</strong> {{event.message}}</li>}</ol>
      </details>
      </section>
    }
    <section class="panel prose calibration-panel"><h2>Prototype boundaries</h2>
      <p>Raw operational training records remain local in this prototype; model parameters and aggregate metadata are exchanged. No global raw training dataset is created. These are five logical nodes in one local service, using simulated/calibrated operations, not connected government infrastructure.</p>
      <p>Model updates may leak information. Differential privacy, secure aggregation, encrypted network transport and adversarial-client defenses are not implemented. This experimental global model does not replace the existing operational forecasting models. Physical medicine redistribution remains domestic.</p>
      <p class="muted">Gemini: {{status()?.phase6_status}} No live Gemini request is made by this page.</p>
    </section>
  `,
})
export class BricsPage implements OnDestroy {
  api = inject(NetworkApi);
  countries = signal<Country[]>([]); nodes = signal<FederationNode[]>([]);
  status = signal<FederationStatus | null>(null);run = signal<FederationRun | null>(null);
  error = signal('');pending = signal(false);private poll?: ReturnType<typeof setInterval>;
  private polling = false;
  roundCount = 5;localEpochs = 1;policy: FederationRequest['policy'] = 'sample-weighted';
  constructor() {
    forkJoin({countries:this.api.countries(),nodes:this.api.federationNodes(),status:this.api.federationStatus()}).subscribe({
      next: data => {this.countries.set(data.countries.items);this.nodes.set(data.nodes.items);this.status.set(data.status);
        if(data.status.active_run_id)this.watch(data.status.active_run_id);
        else this.api.savedFederation().subscribe({next:r=>this.run.set(r),error:()=>this.error.set('Saved measured federation evidence is unavailable. Local training remains available when country tables are ready.')});},
      error: () => this.error.set('Federation service is unavailable. Check the backend and country-local training tables.'),
    });
  }
  ngOnDestroy() {if(this.poll)clearInterval(this.poll);}
  busy() {return this.pending() || ['queued','running'].includes(this.run()?.status || '');}
  ready() {return this.nodes().length === 5 && this.nodes().every(n => n.status === 'ready');}
  node(id:string) {return this.run()?.nodes.find(n=>n.country_id===id) || this.nodes().find(n=>n.country_id===id);}
  countryName(id:string) {return this.countries().find(c=>c.id===id)?.name || id;}
  nodeState(id:string) {
    const r = this.run();if(!r)return this.node(id)?.status === 'ready' ? 'Ready for local training' : 'Local table unavailable';
    if(r.status==='completed')return 'Global model received · '+(this.node(id)?.change || 'evaluated');
    return r.current_country===id ? r.message : 'Round '+r.current_round+' · '+r.status;
  }
  latestBytes(id:string) {return this.run()?.rounds.at(-1)?.clients.find(n=>n.country_id===id)?.bytes_transferred ?? this.node(id)?.latest_update_bytes ?? 0;}
  weight(id:string) {return this.run()?.rounds.at(-1)?.weights[id] ?? 0;}
  start() {
    this.error.set('');this.pending.set(true);
    this.api.startFederation({rounds:this.roundCount,local_epochs:this.localEpochs,policy:this.policy,seed:42}).subscribe({
      next:r=>{this.run.set(r);this.pending.set(false);this.watch(r.run_id);},
      error:e=>{this.pending.set(false);this.error.set(e.error?.detail || 'Could not start federation.');},
    });
  }
  private watch(id:string) {
    if(this.poll)clearInterval(this.poll);
    const update=()=>{if(this.polling)return;this.polling=true;this.api.federationRun(id).subscribe({
      next:r=>{this.polling=false;this.run.set(r);if(['completed','failed'].includes(r.status)){if(this.poll)clearInterval(this.poll);if(r.status==='failed')this.error.set(r.message);}},
      error:()=>{this.polling=false;if(this.poll)clearInterval(this.poll);this.error.set('Run progress could not be loaded. Training may still be running on the backend.');},
    });};
    this.poll=setInterval(update,700);update();
  }
  discard() {const r=this.run();if(!r)return;this.api.discardFederation(r.run_id).subscribe({next:()=>this.run.set(null),error:()=>this.error.set('Run could not be discarded.')});}
  chartPoints() {const rows=this.run()?.rounds || [];const max=Math.max(.01,...rows.map(r=>r.global_validation.wape ?? 0));return rows.map((r,i)=>`${20+i*600/Math.max(1,rows.length-1)},${110-(r.global_validation.wape ?? 0)*95/max}`).join(' ');}
}
