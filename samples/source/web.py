from __future__ import annotations

import argparse
import json
import mimetypes
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .analysis import analyze_incident, build_mitigation_plan, build_rollback_recommendation
from .azure_connector import enrich_incident_from_app_insights
from .copilot_runner import run_copilot
from .github_connector import enrich_incident_from_github
from .loader import load_incident, load_incident_dict, save_incident_dict
from .prompt_builder import build_prompt


def _incident_payload(incident_path: str) -> dict:
    incident_dict = load_incident_dict(incident_path)
    incident = load_incident(incident_path)
    analysis = analyze_incident(incident)
    mitigation = build_mitigation_plan(incident, analysis)
    rollback = build_rollback_recommendation(incident, analysis)

    return {
        "incident": {
            "id": incident.incident_id,
            "title": incident.title,
            "service": incident.service,
            "started_at": incident.started_at,
            "customer_impact": incident.customer_impact,
            "symptoms": incident.symptoms,
            "alerts": [asdict(alert) for alert in incident.alerts],
            "metrics": [asdict(metric) for metric in incident.metrics],
            "logs": [asdict(log) for log in incident.logs],
            "deploys": [asdict(deploy) for deploy in incident.deploys],
            "commits": [asdict(commit) for commit in incident.commits],
            "pull_requests": [asdict(pr) for pr in incident.pull_requests],
            "runbooks": [asdict(runbook) for runbook in incident.runbooks],
        },
        "analysis": {
            "severity": analysis.severity,
            "summary": analysis.summary,
            "suspects": [asdict(suspect) for suspect in analysis.suspects],
            "recommended_actions": analysis.recommended_actions,
            "timeline": analysis.timeline,
        },
        "mitigation": [asdict(item) for item in mitigation],
        "rollback": asdict(rollback),
        "prompt": build_prompt(incident, analysis),
        "dashboard": incident_dict.get("app_insights_dashboard"),
        "app_insights_demo": incident_dict.get("app_insights_demo", False),
        "source_app_insights_app_id": incident_dict.get("source_app_insights_app_id"),
    }


def _serve_ui(incident_path: str, host: str, port: int) -> None:
    static_root = Path(__file__).resolve().parent / "ui"

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, file_path: Path) -> None:
            if not file_path.exists() or not file_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            body = file_path.read_bytes()
            content_type, _ = mimetypes.guess_type(file_path.name)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type or "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                self._send_json(_incident_payload(incident_path))
                return
            if parsed.path == "/" or parsed.path == "/index.html":
                self._send_file(static_root / "index.html")
                return
            target = (static_root / parsed.path.lstrip("/")).resolve()
            if static_root not in target.parents and target != static_root:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            self._send_file(target)

        def do_POST(self) -> None:
            try:
                if self.path == "/api/enrich/github":
                    body = self._read_json_body()
                    incident_data = load_incident_dict(incident_path)
                    enriched = enrich_incident_from_github(
                        incident_data=incident_data,
                        repo=body["repo"],
                        token_env=body.get("token_env", "GITHUB_TOKEN"),
                        lookback_hours=int(body.get("lookback_hours", 24)),
                    )
                    save_incident_dict(incident_path, enriched)
                    self._send_json(_incident_payload(incident_path))
                    return

                if self.path == "/api/enrich/azure":
                    body = self._read_json_body()
                    incident_data = load_incident_dict(incident_path)
                    enriched = enrich_incident_from_app_insights(
                        incident_data=incident_data,
                        app_id=body["app_id"],
                        api_key_env=body.get("api_key_env", "APPINSIGHTS_API_KEY"),
                        lookback_minutes=int(body.get("lookback_minutes", 30)),
                    )
                    save_incident_dict(incident_path, enriched)
                    self._send_json(_incident_payload(incident_path))
                    return

                if self.path == "/api/copilot/run":
                    body = self._read_json_body()
                    code, output = run_copilot(body["prompt"])
                    self._send_json({"exit_code": code, "output": output})
                    return

                self.send_error(HTTPStatus.NOT_FOUND)
            except Exception as exc:  # noqa: BLE001
                self._send_json({"error": str(exc)}, status=500)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Copilot SRE UI running at http://{host}:{port}")
    print(f"Incident source: {incident_path}")
    server.serve_forever()


def build_web_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="copilot-sre ui")
    parser.add_argument("--incident", required=True, help="Path to an incident directory")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_web_parser()
    args = parser.parse_args(argv)
    _serve_ui(args.incident, args.host, args.port)
    return 0
