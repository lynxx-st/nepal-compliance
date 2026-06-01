#!/usr/bin/env python3
"""Lightweight secret-pattern scan for CI.

This intentionally scans only tracked source/config files so local ignored files
like .env are never reported or uploaded by CI.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", "node_modules", "__pycache__"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".lock"}
ALLOWLIST = {
    "STALWART_RECOVERY_ADMIN",
    "--admin-password=${ADMIN_PASSWORD}",
    "--db-root-password=${DB_ROOT_PASSWORD}",
    "token = stalwart_token()",
    "your-admin-password",
    "your-db-root-password",
    "your-mysql-root-password",
}
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "oracle auth token": re.compile(r"ocid1\.user\.oc1\.\.[A-Za-z0-9_.@-]{60,}"),
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"),
    "generic assignment secret": re.compile(
        r"(?i)\b(?:password|passwd|secret|token|api[_-]?key)\b\s*[:=]\s*['\"]?[^'\"\s]{16,}"
    ),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    files: list[Path] = []
    for line in result.stdout.splitlines():
        path = ROOT / line
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.is_file():
            files.append(path)
    return files


def is_allowed(line: str) -> bool:
    return any(item in line for item in ALLOWLIST)


def main() -> None:
    findings: list[str] = []
    for path in tracked_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, 1):
            if is_allowed(line):
                continue
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    rel = path.relative_to(ROOT).as_posix()
                    findings.append(f"{rel}:{lineno}: possible {name}")

    if findings:
        print("\n".join(findings))
        raise SystemExit("Secret-pattern scan failed.")
    print("Secret-pattern scan passed.")


if __name__ == "__main__":
    main()
