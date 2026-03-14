from __future__ import annotations

from .analysis import IncidentAnalysis, build_mitigation_plan, build_rollback_recommendation
from .models import Incident


def build_prompt(incident: Incident, analysis: IncidentAnalysis) -> str:
    suspects = "\n".join(
        f"- {suspect.title} (score {suspect.score}): {suspect.rationale}"
        for suspect in analysis.suspects
    )
    actions = "\n".join(f"- {action}" for action in analysis.recommended_actions)
    symptoms = "\n".join(f"- {symptom}" for symptom in incident.symptoms)
    runbooks = "\n".join(
        f"- {runbook.title} ({runbook.path}): {runbook.summary}"
        for runbook in incident.runbooks
    )
    commits = "\n".join(
        f"- {commit.sha} by {commit.author}: {commit.message}"
        for commit in incident.commits[:5]
    ) or "- None available"
    pull_requests = "\n".join(
        f"- #{pr.number} {pr.title} by {pr.author} [{pr.state}] updated {pr.updated_at}"
        for pr in incident.pull_requests[:5]
    ) or "- None available"
    mitigation = "\n".join(
        f"- {item.title} [{item.priority}, confidence: {item.confidence}]: {item.rationale}"
        for item in build_mitigation_plan(incident, analysis)
    )
    rollback = build_rollback_recommendation(incident, analysis)
    timeline = "\n".join(f"- {entry}" for entry in analysis.timeline)

    return f"""You are acting as an incident commander and senior SRE.

Investigate this production incident and produce:
1. likely root cause
2. immediate mitigation options
3. safest next action
4. a concrete verification plan
5. if useful, a rollback recommendation and PR plan

Incident:
- ID: {incident.incident_id}
- Title: {incident.title}
- Service: {incident.service}
- Started: {incident.started_at}
- Severity: {analysis.severity}
- Customer impact: {incident.customer_impact}

Symptoms:
{symptoms}

Top suspects:
{suspects}

Recommended next actions:
{actions}

Relevant runbooks:
{runbooks}

Recent repository activity:
Commits:
{commits}

Pull requests:
{pull_requests}

Mitigation options:
{mitigation}

Rollback recommendation:
- Decision: {rollback.decision}
- Confidence: {rollback.confidence}
- Rationale: {rollback.rationale}
- Verification:
{chr(10).join(f"  - {step}" for step in rollback.verification_steps)}

Timeline:
{timeline}

Please reason from the evidence above, call out uncertainties, and keep the answer optimized for an on-call engineer under time pressure.
""".strip()
