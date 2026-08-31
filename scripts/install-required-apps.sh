#!/usr/bin/env bash
set -euo pipefail

site="${1:-${FRAPPE_SITE:-frontend}}"
required_apps="${2:-${REQUIRED_FRAPPE_APPS:-erpnext,hrms,crm,print_designer,insights,mail,raven,nepal_compliance}}"
backend_service="${FRAPPE_BACKEND_SERVICE:-backend}"

docker compose exec -T "$backend_service" \
  bash apps/nepal_compliance/scripts/install-required-apps-in-container.sh \
  "$site" "$required_apps"
