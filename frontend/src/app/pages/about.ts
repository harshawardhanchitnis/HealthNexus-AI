import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from '../shared/icon';
@Component({
  selector: 'app-about',
  imports: [RouterLink, Icon],
  template: `
    <div class="page-heading">
      <div>
        <div class="eyebrow">HEALTHNEXUS AI / PROJECT SCOPE</div>
        <h1>Built for Resource Resilience</h1>
        <p>
          A national health resource and supply-chain decision-support platform with transparent evidence and country-local response.
        </p>
      </div>
    </div>
    <div class="about-hero">
      <app-icon name="network" />
      <h2>India operational resilience.<br />Evidence from collaborative learning.</h2>
      <p>
        India retains all 36 states and union territories and its 207-facility operational showcase.
        The public deployment operates India only. Brazil, Russia, China and South Africa
        appear solely in the preserved five-node experimental federation evidence.
      </p>
      <span>Public health datasets / Calibrated simulation / Traceable provenance</span>
    </div>
    <section class="architecture-grid" aria-label="System architecture">
      <article><small>01 / OBSERVE</small><strong>Public evidence & simulation</strong><p>Public aggregates calibrate fictional operational profiles. Source lineage stays attached.</p></article>
      <article><small>02 / ANTICIPATE</small><strong>Forecast & stress-test</strong><p>Saved models, uncertainty paths and warning rules measure baseline and conditional pressure.</p></article>
      <article><small>03 / COORDINATE</small><strong>Safe domestic response</strong><p>Google OR-Tools selects protected transfers. Shortages and donor reserves remain visible.</p></article>
      <article><small>04 / INTERPRET & LEARN</small><strong>Copilot & federation</strong><p>Gemini interprets validated tool evidence. A separate five-node experiment shares model updates.</p></article>
    </section>
    <div class="about-grid">
      <section class="panel prose">
        <h2>Connected decision-support capabilities</h2>
        <ul>
          <li>India operational geography and state/district drill-down.</li>
          <li>Two real public-source adapters: MoHFW / PIB Health Dynamics summary and WHO GHO.</li>
          <li>Small verified caches, normalized observations, provenance and offline re-import.</li>
          <li>Aggregate-anchored workforce and capacity assumptions.</li>
          <li>
            Patient syndrome mixes, admissions / discharges and stock ledgers with explicit unmet
            demand.
          </li>
          <li>Resource views and transparent threshold alerts.</li>
          <li>540-day histories, evaluated country-local forecasting and empirical uncertainty.</li>
          <li>Requested-demand targets and reproducible model-based stock-out estimates.</li>
          <li>
            Early Warning Centre and four non-destructive emergency scenarios with baseline
            comparisons.
          </li>
          <li>
            Domestic OR-Tools redistribution planning, protected donor reserves and before/after
            stock simulation.
          </li>
          <li>Reproducible constrained and redistribution-ready inventory simulations.</li>
          <li>Validated forecast preparation and profile-isolated planning caches.</li>
          <li>Server-side Gemini integration with thirteen validated operational tools and typed evidence.</li>
          <li>Explicit offline summaries, tool traces and separate credentialed live verification.</li>
        </ul>
        <a routerLink="/data-sources" queryParamsHandling="preserve" class="inline-link"
          >Inspect the evidence <app-icon name="arrow"
        /></a>
      </section>
      <section class="panel prose">
        <h2>Verification and deployment status</h2>
        <ol>
          <li>Credentialed live Gemini verification and operational acceptance.</li>
          <li>Five-country FedAvg locally verified; raw training records shared: 0.</li>
          <li>Cloud deployment is a target, subject to the ₹0 billing constraint.</li>
        </ol>
        <p>
          Live Gemini availability depends on backend credentials and runtime verification. Forecasts,
          scenarios, optimizer plans and labelled offline summaries are available with saved artifacts.
        </p>
      </section>
    </div>
    <section class="panel prose"><h2>Google technology in HealthNexus</h2>
      <p><strong>Google OR-Tools:</strong> implemented domestic redistribution, with engine-derived donor reserves and genuine CP-SAT plans.</p>
      <p><strong>Gemini API:</strong> implemented native tool orchestration, structured responses and a five-model availability fallback chain. Implementation complete; live provider acceptance pending due to Gemini service availability.</p>
      <p><strong>Deployment targets:</strong> Firebase Hosting for Angular and Google Cloud Run for FastAPI. Neither is claimed deployed. Cloud Run requires billing; billing is not enabled for this task. Firestore is an optional snapshot adapter, not required by the local demo.</p>
    </section>
    <section class="panel prose">
      <h2>What is real, and what is simulated?</h2>
      <p>
        The imported public observations are historical, national-level statistics with publisher
        URLs and reference years. They do not provide live medicine inventory, staff attendance or
        bed occupancy for the sample facilities.
      </p>
      <p>
        Facility-level operational values are simulated where real-time public feeds are
        unavailable. Calibration attaches real aggregate anchors but does not convert generated data
        into official observations. Names, locations, demand, medicine profiles and delivery
        behaviour remain illustrative; no real patient or employee identities are used.
      </p>
      <h3>Resource transfers and federation are different</h3>
      <p>
        Physical redistribution planning is enforced within each country. Five logical country
        nodes train a separate footfall MLP locally and exchange model parameters and aggregate
        metadata through FedAvg. No raw operational training records are shared with the aggregator.
        This local prototype has no secure aggregation or differential privacy and does not
        guarantee privacy. The existing operational forecasting models remain authoritative.
      </p>
      <h3>Coverage and limitations</h3>
      <p>
        India's districts and facilities are sampled. The saved experiment used five logical
        country nodes; foreign operational networks are not available in the public deployment.
        Public source years and coverage differ. HMIS live
        feeds, data.gov.in dataset imports and additional national portals remain planned.
      </p>
    </section>
  `,
})
export class AboutPage {}
