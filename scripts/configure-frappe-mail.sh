#!/usr/bin/env bash
set -euo pipefail

deploy_path="${PROD_DEPLOY_PATH:-/home/flagforge/nepal-compliance}"
backend_service="${FRAPPE_BACKEND_SERVICE:-backend}"
stalwart_url="${STALWART_PUBLIC_URL:-https://mail.flagforgectf.com}"

cd "$deploy_path"

recovery_admin="$(grep '^STALWART_RECOVERY_ADMIN=' .env | tail -n1 | cut -d= -f2-)"
if [[ "$recovery_admin" != *:* ]]; then
  echo "STALWART_RECOVERY_ADMIN must use username:password form" >&2
  exit 1
fi

mapfile -t sites < <(
  docker compose exec -T "$backend_service" bench list-sites \
    | sed -E 's/^[*[:space:]]+//' \
    | grep -E '^[A-Za-z0-9.-]+$'
)

for site in "${sites[@]}"; do
  if ! docker compose exec -T "$backend_service" bench --site "$site" list-apps \
    | awk '{print $1}' \
    | grep -qx mail; then
    continue
  fi

  docker compose exec -T \
    -e MAIL_ADMIN_CONFIG="$recovery_admin" \
    -e MAIL_SERVER_URL="$stalwart_url" \
    "$backend_service" bash -lc "cd /home/frappe/frappe-bench && bench --site '$site' console" <<'PY'
import os

import frappe

credential = os.environ.pop("MAIL_ADMIN_CONFIG")
server_url = os.environ.pop("MAIL_SERVER_URL")
username, admin_credential = credential.split(":", 1)

settings = frappe.get_single("Mail Settings")
settings.server_url = server_url
settings.username = username
settings.set("password", admin_credential)
settings.flags.ignore_mandatory = True
settings.save(ignore_permissions=True)
frappe.db.commit()
frappe.clear_cache()
print("Frappe Mail connection configured")
PY
done

unset recovery_admin
echo "Frappe Mail settings synchronized for installed sites"
