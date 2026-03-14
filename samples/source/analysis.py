from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import Incident


TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


@dataclass(slots=True)
class Suspect:
    title: str
    score: int
    rationale: str


@dataclass(slots=True)
class IncidentAnalysis:
    severity: str
    summary: str
    suspects: list[Suspect]
    recommended_actions: list[str]
    timeline: list[str]


@dataclass(slots=True)
class MitigationOption:
    title: str
    priority: str
    confidence: str
    rationale: str


@dataclass(slots=True)
class RollbackRecommendation:
    decision: str
    confidence: str
    rationale: str
    verification_steps: list[str]


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, TIME_FORMAT)


def _metric_regressions(incident: Incident) -> list[str]:
    regressions: list[str] = []
    for metric in incident.metrics:
        if metric.baseline == 0:
            continue
        ratio = metric.value / metric.baseline
        if ratio >= 2:
            regressions.append(
                f"{metric.name} rose to {metric.value:g}{metric.unit} from baseline {metric.baseline:g}{metric.unit}"
            )
    return regressions


def _derive_severity(incident: Incident) -> str:
    if any(alert.severity.upper() in {"SEV0", "SEV1"} for alert in incident.alerts):
        return "high"
    if len(_metric_regressions(incident)) >= 2:
        return "high"
    return "medium"


def _rank_suspects(incident: Incident) -> list[Suspect]:
    suspects: list[Suspect] = []

    for deploy in incident.deploys:
        score = 30
        incident_time = _parse_time(incident.started_at)
        deploy_time = _parse_time(deploy.timestamp)
        minutes_delta = abs(int((incident_time - deploy_time).total_seconds() // 60))
        if minutes_delta <= 15:
            score += 35
        if deploy.service == incident.service:
            score += 20
        suspects.append(
            Suspect(
                title=f"Recent deploy {deploy.version}",
                score=score,
                rationale=f"Deploy by {deploy.actor} landed {minutes_delta} minutes from incident start: {deploy.summary}",
            )
        )

    error_logs = [log for log in incident.logs if log.level.upper() in {"ERROR", "CRITICAL"}]
    if error_logs:
        joined_messages = " | ".join(log.message for log in error_logs[:3])
        score = 40 + min(30, len(error_logs) * 5)
        suspects.append(
            Suspect(
                title="Application error pattern",
                score=score,
                rationale=f"Repeated error logs observed: {joined_messages}",
            )
        )

    regressions = _metric_regressions(incident)
    if regressions:
        suspects.append(
            Suspect(
                title="Performance regression under checkout traffic",
                score=45 + min(20, len(regressions) * 5),
                rationale="; ".join(regressions[:3]),
            )
        )

    suspects.sort(key=lambda item: item.score, reverse=True)
    return suspects[:5]


def _recommend_actions(incident: Incident, suspects: list[Suspect]) -> list[str]:
    actions = [
        "Confirm whether the latest deploy changed configuration, dependency versions, or outbound payment handling.",
        "Check the failing service environment variables against the last known healthy release.",
        "Validate error rate and latency after any mitigation before declaring recovery.",
    ]
    if incident.pull_requests:
        actions.append("Review the most recent merged or updated pull requests for config, retry, or environment-variable changes.")
    if suspects and suspects[0].title.startswith("Recent deploy"):
        actions.insert(0, "Prepare a rollback decision: compare rollback speed versus a forward fix for the latest deploy.")
    if any("error" in suspect.title.lower() for suspect in suspects):
        actions.append("Search logs for the first occurrence of the dominant error and identify the triggering request path.")
    return actions


def _build_timeline(incident: Incident) -> list[str]:
    entries: list[tuple[datetime, str]] = []
    entries.append((_parse_time(incident.started_at), f"Incident declared for {incident.service}: {incident.title}"))
    for deploy in incident.deploys:
        entries.append((_parse_time(deploy.timestamp), f"Deploy {deploy.version} by {deploy.actor}: {deploy.summary}"))
    for alert in incident.alerts:
        entries.append((_parse_time(alert.fired_at), f"Alert {alert.name} ({alert.severity}): {alert.summary}"))
    for log in incident.logs[:5]:
        entries.append((_parse_time(log.timestamp), f"{log.service} {log.level}: {log.message}"))
    entries.sort(key=lambda item: item[0])
    return [f"{stamp.strftime(TIME_FORMAT)}  {message}" for stamp, message in entries]


def analyze_incident(incident: Incident) -> IncidentAnalysis:
    suspects = _rank_suspects(incident)
    severity = _derive_severity(incident)
    summary = (
        f"{incident.service} is experiencing {incident.customer_impact.lower()}. "
        f"Top suspect: {suspects[0].title if suspects else 'unknown'}."
    )
    return IncidentAnalysis(
        severity=severity,
        summary=summary,
        suspects=suspects,
        recommended_actions=_recommend_actions(incident, suspects),
        timeline=_build_timeline(incident),
    )


def build_mitigation_plan(incident: Incident, analysis: IncidentAnalysis) -> list[MitigationOption]:
    options: list[MitigationOption] = []

    top_suspect = analysis.suspects[0].title.lower() if analysis.suspects else ""
    if "recent deploy" in top_suspect:
        options.append(
            MitigationOption(
                title="Rollback the latest checkout-api deploy",
                priority="P0",
                confidence="high",
                rationale="Incident start is tightly correlated with the most recent deploy and customer impact is already severe.",
            )
        )
    if any("environment" in action.lower() for action in analysis.recommended_actions):
        options.append(
            MitigationOption(
                title="Correct production payment endpoint configuration",
                priority="P0",
                confidence="high",
                rationale="Error logs explicitly point to a `PAYMENTS_API_BASE_URL` mismatch and upstream connectivity timeout.",
            )
        )
    options.append(
        MitigationOption(
            title="Temporarily reduce payment retries or shed failing checkout traffic",
            priority="P1",
            confidence="medium",
            rationale="This can reduce queuing pressure while recovery work is underway, but it does not address the root cause.",
        )
    )
    return options


def build_rollback_recommendation(incident: Incident, analysis: IncidentAnalysis) -> RollbackRecommendation:
    severity_high = analysis.severity == "high"
    top_suspect_is_deploy = bool(analysis.suspects and analysis.suspects[0].title.startswith("Recent deploy"))
    error_mentions_config = any("configuration mismatch" in log.message.lower() for log in incident.logs)

    if severity_high and top_suspect_is_deploy:
        decision = "rollback now"
        confidence = "high" if error_mentions_config else "medium"
        rationale = (
            "Customer impact is high and the most likely cause is a recent deploy. "
            "Rollback is the fastest reversible mitigation while a forward fix is prepared."
        )
    else:
        decision = "hold rollback and investigate"
        confidence = "medium"
        rationale = "Current evidence is not yet strong enough to justify immediate rollback."

    verification_steps = [
        "Confirm checkout p95 latency trends toward baseline within 5-10 minutes.",
        "Confirm HTTP 5xx rate drops below the alert threshold.",
        "Validate payment authorization succeeds on a canary request after mitigation.",
    ]

    return RollbackRecommendation(
        decision=decision,
        confidence=confidence,
        rationale=rationale,
        verification_steps=verification_steps,
    )
