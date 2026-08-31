#!/usr/bin/env bash
set -euo pipefail

site="${1:?Usage: install-required-apps-in-container.sh SITE REQUIRED_APPS_CSV}"
required_apps_csv="${2:?Usage: install-required-apps-in-container.sh SITE REQUIRED_APPS_CSV}"

cd /home/frappe/frappe-bench

installed_apps() {
  bench --site "$site" list-apps | awk 'NF { print $1 }'
}

IFS=',' read -ra required_apps <<< "$required_apps_csv"
for raw_app in "${required_apps[@]}"; do
  app="${raw_app//[[:space:]]/}"
  [[ -n "$app" ]] || continue
  [[ "$app" =~ ^[a-z0-9_]+$ ]] || {
    echo "Invalid Frappe app name: $app" >&2
    exit 1
  }

  if [[ ! -d "apps/$app" ]]; then
    echo "Required app is not bundled in the image: $app" >&2
    exit 1
  fi

  if installed_apps | grep -qx "$app"; then
    echo "Frappe app already installed: $app"
    continue
  fi

  echo "Installing required Frappe app: $app"
  bench --site "$site" install-app "$app"
done

bench --site "$site" migrate
bench --site "$site" clear-cache

current_apps="$(installed_apps)"
for raw_app in "${required_apps[@]}"; do
  app="${raw_app//[[:space:]]/}"
  [[ -n "$app" ]] || continue
  grep -qx "$app" <<< "$current_apps" || {
    echo "Required app is still missing after installation: $app" >&2
    exit 1
  }
done

echo "All required Frappe apps are installed on site: $site"
