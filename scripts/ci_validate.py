#!/usr/bin/env python3
"""Repository validation checks used by GitHub Actions."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "nepal_compliance/hooks.py",
    "nepal_compliance/modules.txt",
    "nepal_compliance/patches.txt",
    "frappe_patches/fix_jmap_connection.py",
    "frappe_patches/fix_jmap_user_settings.py",
    "frappe_patches/fix_jmap_account_api.py",
    "frappe_patches/fix_pwa_setup.py",
    "frappe_patches/fix_mail_member_domain_layout.py",
    "scripts/install-required-apps.sh",
    "scripts/install-required-apps-in-container.sh",
]
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


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def validate_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def validate_python_syntax() -> None:
    for path in ROOT.glob("nepal_compliance/**/*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for path in ROOT.glob("frappe_patches/*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def validate_json_files() -> None:
    for path in ROOT.glob("nepal_compliance/**/*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def validate_frappe_metadata() -> None:
    modules = (ROOT / "nepal_compliance/modules.txt").read_text(encoding="utf-8")
    if "Nepal Compliance" not in modules:
        fail("nepal_compliance/modules.txt must include 'Nepal Compliance'")

    hooks = (ROOT / "nepal_compliance/hooks.py").read_text(encoding="utf-8")
    required_hooks = [
        "nepal_compliance.integrations.raven.auto_add_raven_user",
        "nepal_compliance.integrations.raven.sync_raven_user",
        "nepal_compliance.install.install",
    ]
    missing_hooks = [hook for hook in required_hooks if hook not in hooks]
    if missing_hooks:
        fail(f"missing required hooks: {', '.join(missing_hooks)}")

    patches = (ROOT / "nepal_compliance/patches.txt").read_text(encoding="utf-8")
    if "nepal_compliance.patches" not in patches:
        fail("nepal_compliance/patches.txt must include app patches")


def validate_apps_json() -> None:
    apps_json = ROOT / ".github/apps-version-16.json"
    apps = json.loads(apps_json.read_text(encoding="utf-8"))
    found = {Path(app["url"]).stem.replace("-", "_") for app in apps}
    found.update({Path(app["url"]).stem for app in apps})
    missing = sorted(REQUIRED_APPS - found)
    if missing:
        fail(f".github/apps-version-16.json missing apps: {', '.join(missing)}")


def validate_workflow_routing() -> None:
    docker_workflow = (ROOT / ".github/workflows/docker-build.yml").read_text(encoding="utf-8")
    release_workflow = (ROOT / ".github/workflows/release-deploy.yml").read_text(encoding="utf-8")
    if "version-16" not in docker_workflow:
        fail("docker-build.yml must build Frappe version-16")
    if 'PYTHON_VERSION: "3.14.2"' not in docker_workflow:
        fail("docker-build.yml must use Python 3.14 for frappe/mail")
    if "refs/heads/development" not in docker_workflow:
        fail("docker-build.yml must handle development branch tagging")
    if "refs/heads/main" not in docker_workflow:
        fail("docker-build.yml must handle main branch tagging")
    if "release_tag" not in docker_workflow:
        fail("docker-build.yml must support release tag builds")
    if "release:" not in release_workflow or "published" not in release_workflow:
        fail("release-deploy.yml must deploy only from published releases")
    if "SSH production preflight" not in release_workflow:
        fail("release-deploy.yml must include explicit SSH production preflight checks")
    if "push:" in release_workflow:
        fail("release-deploy.yml must not deploy on push")


def main() -> None:
    validate_required_files()
    validate_python_syntax()
    validate_json_files()
    validate_frappe_metadata()
    validate_apps_json()
    validate_workflow_routing()
    print("Repository validation passed.")


if __name__ == "__main__":
    main()
