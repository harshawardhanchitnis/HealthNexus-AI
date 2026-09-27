import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Icon } from '../shared/icon';
@Component({
  selector: 'app-about',
  imports: [RouterLink, Icon],
  template: `
    <div class="page-heading">
      <div>
        <div class="eyebrow">TRANSPARENCY / INDIA</div>
        <h1>Built for a more resilient India.</h1>
        <p>A clear account of our scope, our data and what works today.</p>
      </div>
    </div>
    <div class="about-hero">
      <app-icon name="network" />
      <h2>National visibility.<br />Local responsibility.</h2>
      <p>
        HealthNexus AI is an India-only healthcare resource resilience prototype. The product scope
        includes every state and union territory, with a hierarchy of India → State / UT → District
        → Facility.
      </p>
      <span
        >28 states &nbsp; / &nbsp; 8 union territories &nbsp; / &nbsp; One national network</span
      >
    </div>
    <div class="about-grid">
      <section class="panel prose">
        <h2>What works today</h2>
        <ul>
          <li>Angular command centre connected to a FastAPI backend.</li>
          <li>Sample facilities in every Indian state and union territory.</li>
          <li>Regional filters, facility search, inventory, beds, staff and patient footfall.</li>
          <li>Reconciled synthetic data and explainable stock / attendance alerts.</li>
          <li>Local data mode, with an optional Firestore repository.</li>
        </ul>
        <a routerLink="/overview" class="inline-link"
          >Explore the network <app-icon name="arrow"
        /></a>
      </section>
      <section class="panel prose">
        <h2>Next implementation milestones</h2>
        <ol>
          <li>Evaluated demand forecasting and predictive warnings.</li>
          <li>Emergency scenarios with causal resource effects.</li>
          <li>OR-Tools redistribution within and between Indian states.</li>
          <li>Backend-grounded Gemini administrative assistance.</li>
          <li>Federated learning across Indian state / regional nodes.</li>
        </ol>
        <p>
          These capabilities are planned. The current prototype does not run AI inference or
          federated training.
        </p>
      </section>
    </div>
    <section class="panel prose">
      <h2>Prototype data notice</h2>
      <p>
        All facility-level operational data is synthetic, generated from explicit assumptions about
        weekly seasonality, seasonal demand, facility capacity and resource consumption. It has not
        yet been statistically calibrated against verified government health datasets. No patient or
        employee personally identifiable information is used.
      </p>
      <p>
        All 36 states and union territories are represented. The selected districts are illustrative
        and do not form an exhaustive or current administrative registry. Facility identifiers,
        coordinates and capacities are fictional. No real government hospital integration is
        claimed.
      </p>
      <h3>Public references</h3>
      <p>
        <a
          href="https://www.india.gov.in/explore-india/facts-of-india/states-ut-districts"
          target="_blank"
          rel="noopener noreferrer"
          >National Portal of India — states, union territories and districts ↗</a
        >
      </p>
      <p>
        Future public-data imports must record their source URL, access date, fields and provenance.
        Government health data and international comparisons have not been imported into this
        prototype.
      </p>
      <h3>Federation stays within India</h3>
      <p>
        The planned federation will train models locally at Indian regional nodes and aggregate
        model updates nationally. Raw records should stay at their source. Federated learning alone
        does not guarantee privacy; secure aggregation, access control and update leakage need
        separate evaluation.
      </p>
    </section>
  `,
})
export class AboutPage {}
