#!/usr/bin/env python3
"""Validate deployment-facing configuration without contacting production."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_APPS = {
    "erpnext",
    "hrms",
    "crm",
    "print_designer",
    "insights",
    "mail",
    "raven",
    "nepal_compliance",
}
REQUIRED_IMAGE_SERVICES = {
    "backend",
    "configurator",
    "create-site",
    "frontend",
    "queue-long",
    "queue-short",
    "scheduler",
    "websocket",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def validate_compose() -> None:
    text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    service_names = set(re.findall(r"^  ([A-Za-z0-9_-]+):\n", text, flags=re.MULTILINE))
    missing = REQUIRED_IMAGE_SERVICES - service_names
    if missing:
        fail(f"compose.yaml missing services: {', '.join(sorted(missing))}")

    for service in sorted(REQUIRED_IMAGE_SERVICES):
        pattern = (
            rf"^  {re.escape(service)}:\n"
            r"(?:(?:    .*)\n)*?"
            r"    image: lynxxstein/nepal-compliance:\$\{VERSION_TAG:-latest\}"
        )
        if not re.search(pattern, text, flags=re.MULTILINE):
            fail(f"{service} must use VERSION_TAG-pinned nepal-compliance image")

    command_match = re.search(r"^  create-site:\n(?P<body>(?:    .*\n)+)", text, flags=re.MULTILINE)
    command_text = command_match.group("body") if command_match else ""
    if "install-required-apps-in-container.sh" not in command_text:
        fail("create-site must reconcile required apps for new and existing sites")

    default_apps = re.search(r"REQUIRED_FRAPPE_APPS: \$\{REQUIRED_FRAPPE_APPS:-([^}]+)\}", command_text)
    configured_apps = set(default_apps.group(1).split(",")) if default_apps else set()
    missing_apps = REQUIRED_APPS - configured_apps
    if missing_apps:
        fail(f"create-site required app list is missing: {', '.join(sorted(missing_apps))}")

    if not re.search(r"^  stalwart:\n", text, flags=re.MULTILINE):
        fail("compose.yaml must include the Stalwart mail service")
    if "ghcr.io/stalwartlabs/stalwart:" not in text:
        fail("Stalwart must use the official container image")
    if "STALWART_RECOVERY_ADMIN: ${STALWART_RECOVERY_ADMIN}" not in text:
        fail("Stalwart recovery credentials must come from the deployment environment")


def validate_apps_file() -> None:
    apps = json.loads((ROOT / ".github/apps-version-16.json").read_text(encoding="utf-8"))
    by_url = {item["url"]: item["branch"] for item in apps}
    expected = {
        "https://github.com/frappe/erpnext": "version-16",
        "https://github.com/frappe/hrms": "version-16",
        "https://github.com/frappe/crm": "main",
        "https://github.com/frappe/print_designer": "main",
        "https://github.com/frappe/insights": "version-3",
        "https://github.com/frappe/mail": "develop",
        "https://github.com/The-Commit-Company/raven": "main",
        "https://github.com/lynxx-st/nepal-compliance": "development",
    }
    for url, branch in expected.items():
        if by_url.get(url) != branch:
            fail(f".github/apps-version-16.json must pin {url} to {branch}")


def validate_release_workflow() -> None:
    text = (ROOT / ".github/workflows/release-deploy.yml").read_text(encoding="utf-8")
    required_snippets = [
        "types:",
        "- published",
        "environment: production",
        "scripts/install-required-apps.sh",
        "backup --with-files --compress",
        "trap rollback ERR",
        "docker pull \"$IMAGE_REF\"",
        "IMAGE_REF: docker.io/",
        "RELEASE_TAG:",
        "SSH production preflight",
        "secrets.SERVER_SSH_PASSWORD",
        "Deploy to self-hosted server",
        "docker compose ps",
        "User\", \"Administrator",
    ]
    missing = [snippet for snippet in required_snippets if snippet not in text]
    if missing:
        fail(f"release-deploy.yml missing required deployment guards: {missing}")

    if re.search(r"Deploy to self-hosted server.*push:", text, re.DOTALL):
        fail("release-deploy.yml must not deploy on push events")


def main() -> None:
    validate_compose()
    validate_apps_file()
    validate_release_workflow()
    print("Deployment configuration checks passed.")


if __name__ == "__main__":
    main()
