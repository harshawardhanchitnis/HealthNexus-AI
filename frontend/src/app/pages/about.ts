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
        <h1>Public evidence. Local resilience.</h1>
        <p>
          A real-data-backed platform foundation for healthcare resilience and federated
          intelligence.
        </p>
      </div>
    </div>
    <div class="about-hero">
      <app-icon name="network" />
      <h2>India in depth.<br />BRICS in collaboration.</h2>
      <p>
        India retains all 36 states and union territories and its 207-facility operational showcase.
        Brazil, Russia, China and South Africa each have representative regional nodes, with
        country-specific data partitions for future federated learning.
      </p>
      <span>Public health datasets / Calibrated simulation / Traceable provenance</span>
    </div>
    <div class="about-grid">
      <section class="panel prose">
        <h2>Implemented through Phase 5.5</h2>
        <ul>
          <li>Five-country geography and the existing India drill-down.</li>
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
        </ul>
        <a routerLink="/data-sources" queryParamsHandling="preserve" class="inline-link"
          >Inspect the evidence <app-icon name="arrow"
        /></a>
      </section>
      <section class="panel prose">
        <h2>Next milestones</h2>
        <ol>
          <li>Grounded, server-side Gemini explanations.</li>
          <li>Genuine country-node FedAvg with measured metrics.</li>
        </ol>
        <p>
          These next services remain future work. Forecasts and measured model comparisons are
          available now when trained artifacts are installed.
        </p>
      </section>
    </div>
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
        Physical redistribution planning is enforced within each country. BRICS collaboration will
        exchange model updates, with operational training data kept at its country node. The local
        prototype currently demonstrates data partitions, not production national infrastructure or
        privacy guarantees.
      </p>
      <h3>Coverage and limitations</h3>
      <p>
        India's districts and facilities are sampled. Other countries have two representative
        regions each. The five configured countries are the requested hackathon scope, not an
        exhaustive list of current BRICS members. Public source years and coverage differ. HMIS live
        feeds, data.gov.in dataset imports and additional national portals remain planned.
      </p>
    </section>
  `,
})
export class AboutPage {}
