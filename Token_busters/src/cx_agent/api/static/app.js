const state = {
  scenarios: [],
  presentation: null,
};

const elements = {
  healthStatus: document.getElementById("health-status"),
  scenarioCount: document.getElementById("scenario-count"),
  judgeScorePill: document.getElementById("judge-score-pill"),
  execGovernance: document.getElementById("exec-governance"),
  presentationSummary: document.getElementById("presentation-summary"),
  execCustomer: document.getElementById("exec-customer"),
  execStage: document.getElementById("exec-stage"),
  execJourney: document.getElementById("exec-journey"),
  execCoverage: document.getElementById("exec-coverage"),
  execAction: document.getElementById("exec-action"),
  execActionDetail: document.getElementById("exec-action-detail"),
  execJudge: document.getElementById("exec-judge"),
  execJudgeDetail: document.getElementById("exec-judge-detail"),
  judgeOrbRing: document.getElementById("judge-orb-ring"),
  judgeOrbScore: document.getElementById("judge-orb-score"),
  scenarioSelect: document.getElementById("scenario-select"),
  roleSelect: document.getElementById("role-select"),
  regionSelect: document.getElementById("region-select"),
  llmToggle: document.getElementById("llm-toggle"),
  refreshButton: document.getElementById("refresh-button"),
  loadButton: document.getElementById("load-button"),
  scenarioCustomer: document.getElementById("scenario-customer"),
  scenarioStage: document.getElementById("scenario-stage"),
  scenarioCategory: document.getElementById("scenario-category"),
  governanceChip: document.getElementById("governance-chip"),
  journeyStage: document.getElementById("journey-stage"),
  journeyRisk: document.getElementById("journey-risk"),
  journeyTraceSummary: document.getElementById("journey-trace-summary"),
  journeyStrip: document.getElementById("journey-strip"),
  recommendedAction: document.getElementById("recommended-action"),
  recommendationRationale: document.getElementById("recommendation-rationale"),
  judgeSummary: document.getElementById("judge-summary"),
  judgeDetails: document.getElementById("judge-details"),
  evidenceList: document.getElementById("evidence-list"),
  gateList: document.getElementById("gate-list"),
  analyticsSummary: document.getElementById("analytics-summary"),
  metricCustomers: document.getElementById("metric-customers"),
  metricEvents: document.getElementById("metric-events"),
  metricSources: document.getElementById("metric-sources"),
  metricScore: document.getElementById("metric-score"),
  sourceBars: document.getElementById("source-bars"),
  patternBars: document.getElementById("pattern-bars"),
  auditTrail: document.getElementById("audit-trail"),
};

init().catch((error) => {
  renderError(error);
});

async function init() {
  wireEvents();
  await loadHealth();
  await loadScenarios();
  await loadPresentation();
}

function wireEvents() {
  elements.refreshButton.addEventListener("click", () => {
    loadPresentation();
  });
  elements.loadButton.addEventListener("click", () => {
    loadPresentation();
  });
  elements.scenarioSelect.addEventListener("change", () => {
    updateScenarioMeta();
    loadPresentation();
  });
  elements.roleSelect.addEventListener("change", () => loadPresentation());
  elements.regionSelect.addEventListener("change", () => loadPresentation());
  elements.llmToggle.addEventListener("change", () => loadPresentation());
}

async function loadHealth() {
  const response = await fetch("/health");
  if (!response.ok) {
    throw new Error("Unable to load health status.");
  }
  const health = await response.json();
  elements.healthStatus.textContent = health.status === "ok" ? "Healthy" : health.status;
}

async function loadScenarios() {
  const response = await fetch("/scenarios");
  if (!response.ok) {
    throw new Error("Unable to load scenarios.");
  }
  const payload = await response.json();
  state.scenarios = payload.scenarios || [];
  elements.scenarioCount.textContent = String(state.scenarios.length);
  elements.scenarioSelect.innerHTML = state.scenarios
    .map(
      (scenario, index) =>
        `<option value="${scenario.scenario_id}" ${index === 0 ? "selected" : ""}>${scenario.scenario_id} - ${scenario.customer_id}</option>`
    )
    .join("");
  updateScenarioMeta();
}

async function loadPresentation() {
  const scenarioId = elements.scenarioSelect.value;
  if (!scenarioId) {
    return;
  }
  elements.loadButton.disabled = true;
  elements.loadButton.textContent = "Loading...";
  try {
    const params = new URLSearchParams({
      scenario_id: scenarioId,
      actor_role: elements.roleSelect.value,
      actor_region: elements.regionSelect.value,
      include_llm: String(elements.llmToggle.checked),
    });
    const response = await fetch(`/presentation?${params.toString()}`);
    if (!response.ok) {
      throw new Error("Presentation request failed.");
    }
    state.presentation = await response.json();
    renderPresentation(state.presentation);
  } catch (error) {
    renderError(error);
  } finally {
    elements.loadButton.disabled = false;
    elements.loadButton.textContent = "Run presentation";
  }
}

function updateScenarioMeta() {
  const scenario = state.scenarios.find((item) => item.scenario_id === elements.scenarioSelect.value);
  elements.scenarioCustomer.textContent = scenario ? scenario.customer_id : "-";
  elements.scenarioStage.textContent = scenario ? scenario.expected_stage : "-";
  elements.scenarioCategory.textContent = scenario ? scenario.expected_category : "-";
}

function renderPresentation(bundle) {
  const demo = bundle.demo;
  const analytics = bundle.analytics;
  const judge = bundle.judge || {};

  elements.governanceChip.textContent = demo.governance_status === "allowed" ? "Allowed" : "Blocked";
  elements.governanceChip.style.background =
    demo.governance_status === "allowed" ? "rgba(110, 231, 166, 0.16)" : "rgba(255, 123, 123, 0.16)";
  elements.governanceChip.style.color = demo.governance_status === "allowed" ? "var(--good)" : "var(--bad)";
  elements.execGovernance.textContent = demo.governance_status === "allowed" ? "Allowed" : "Blocked";
  elements.execGovernance.style.background =
    demo.governance_status === "allowed" ? "rgba(110, 231, 166, 0.16)" : "rgba(255, 123, 123, 0.16)";
  elements.execGovernance.style.color = demo.governance_status === "allowed" ? "var(--good)" : "var(--bad)";

  elements.journeyStage.textContent = demo.journey.journey_stage;
  elements.journeyRisk.textContent = `Risk: ${demo.journey.risk_label} | Friction: ${demo.journey.friction_points.join(", ")}`;
  elements.recommendedAction.textContent = demo.recommendation.recommended_action;
  elements.recommendationRationale.textContent = demo.recommendation.rationale;
  elements.judgeSummary.textContent = `Judge score ${judge.score ?? "-"} / 100`;
  elements.judgeDetails.textContent = bundle.presentation_summary;
  elements.presentationSummary.textContent = bundle.presentation_summary;
  elements.judgeScorePill.textContent = `${judge.score ?? "-"} / 100`;
  elements.metricScore.textContent = `${judge.score ?? "-"} / 100`;
  elements.judgeOrbScore.textContent = `${judge.score ?? "-"}`;
  updateScoreRing(Number(judge.score ?? 0));
  elements.journeyTraceSummary.textContent = `${demo.timeline.length} events`;
  elements.execCustomer.textContent = demo.customer_id || "-";
  elements.execStage.textContent = `${demo.journey.journey_stage} - ${demo.journey.risk_label}`;
  elements.execJourney.textContent = `${demo.timeline.length} touchpoints`;
  elements.execCoverage.textContent = `${analytics.totals.customers} customers, ${analytics.totals.source_buckets} source buckets`;
  elements.execAction.textContent = demo.recommendation.recommended_action;
  elements.execActionDetail.textContent = demo.recommendation.rationale;
  elements.execJudge.textContent = `${judge.score ?? "-"} / 100`;
  elements.execJudgeDetail.textContent = `${demo.governance_status === "allowed" ? "Governance passed" : "Governance blocked"} - ${demo.recommendation.recommendation_category}`;

  renderEvidence(demo.journey.evidence || []);
  renderGates(demo.gates || []);
  renderJourneyTrace(demo.timeline || []);
  renderAnalytics(analytics);
  renderAuditTrail(demo.audit_trail || []);
  elements.analyticsSummary.textContent = `${analytics.totals.customers} customers, ${analytics.totals.events} events`;
}

function renderEvidence(evidence) {
  elements.evidenceList.innerHTML = evidence.length
    ? evidence.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")
    : "<li>No evidence available.</li>";
}

function renderGates(gates) {
  elements.gateList.innerHTML = gates
    .map((gate) => {
      const statusClass = gate.passed ? "chip" : "chip chip-muted";
      const statusLabel = gate.passed ? "PASS" : "BLOCK";
      return `
        <li>
          <div class="audit-item-top">
            <strong>${escapeHtml(gate.gate_name)}</strong>
            <span class="${statusClass}">${statusLabel}</span>
          </div>
          <div class="audit-message">${escapeHtml(gate.reason)}</div>
        </li>
      `;
    })
    .join("");
}

function renderAnalytics(analytics) {
  const totals = analytics.totals || {};
  elements.metricCustomers.textContent = String(totals.customers ?? "-");
  elements.metricEvents.textContent = String(totals.events ?? "-");
  elements.metricSources.textContent = String(totals.source_buckets ?? "-");

  renderBars(elements.sourceBars, analytics.source_counts || {}, "Source");
  renderBars(elements.patternBars, analytics.stage_counts || {}, "Stage");
}

function renderJourneyTrace(timeline) {
  elements.journeyStrip.innerHTML = timeline.length
    ? timeline
        .map((event, index) => {
          const channelClass = (event.channel || "unknown").toLowerCase();
          return `
            <article class="journey-node ${channelClass}" style="--delay:${index * 70}ms">
              <span>${escapeHtml(event.timestamp)}</span>
              <strong>${escapeHtml(event.channel)} - ${escapeHtml(event.event_type)}</strong>
              <div>${escapeHtml(event.outcome)}</div>
            </article>
          `;
        })
        .join("")
    : "<article class='journey-node'><strong>No journey events</strong></article>";
}

function renderBars(container, data, titleLabel) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, value]) => value));
  container.innerHTML = entries.length
    ? entries
        .map(([label, value]) => {
          const width = Math.max(8, Math.round((value / max) * 100));
          return `
            <div class="bar-row">
              <div class="bar-label">${escapeHtml(label)}</div>
              <div class="bar-track">
                <div class="bar-fill" style="width: ${width}%"></div>
              </div>
              <div class="bar-value">${value}</div>
            </div>
          `;
        })
        .join("")
    : `<div class="bar-row"><div class="bar-label">No ${escapeHtml(titleLabel.toLowerCase())} data</div><div class="bar-track"></div><div class="bar-value">0</div></div>`;
}

function renderAuditTrail(entries) {
  elements.auditTrail.innerHTML = entries.length
    ? entries
        .map((entry) => {
          const details = entry.details && Object.keys(entry.details).length
            ? `<div class="audit-details">${escapeHtml(JSON.stringify(entry.details, null, 2))}</div>`
            : "";
          return `
            <article class="audit-item">
              <div class="audit-item-top">
                <strong class="audit-step">${escapeHtml(entry.step)}</strong>
                <span class="audit-time">${escapeHtml(entry.timestamp)}</span>
              </div>
              <p class="audit-message">${escapeHtml(entry.message)}</p>
              ${details}
            </article>
          `;
        })
        .join("")
    : "<article class='audit-item'>No audit trail available.</article>";
}

function updateScoreRing(score) {
  const normalizedScore = Math.max(0, Math.min(100, Number(score) || 0));
  const angle = `${Math.round((normalizedScore / 100) * 360)}deg`;
  elements.judgeOrbRing?.style.setProperty("--score-angle", angle);
}

function renderError(error) {
  console.error(error);
  const message = typeof error === "string" ? error : error?.message || "An unknown error occurred.";
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div class="error" style="padding:16px 32px;">${escapeHtml(message)}</div>`
  );
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
