#!/usr/bin/env bash
set -euo pipefail

deploy_path="${PROD_DEPLOY_PATH:-/home/flagforge/nepal-compliance}"
stalwart_url="${STALWART_ADMIN_URL:-http://127.0.0.1:8181}"
certificate_name="${STALWART_CERTIFICATE_NAME:-mail.flagforgectf.com}"
certificate_path="${STALWART_CERTIFICATE_PATH:-/etc/letsencrypt/live/${certificate_name}/fullchain.pem}"
private_key_path="${STALWART_PRIVATE_KEY_PATH:-/etc/letsencrypt/live/${certificate_name}/privkey.pem}"

cd "$deploy_path"

for command_name in curl jq docker; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Missing required command: $command_name" >&2
    exit 1
  }
done

recovery_admin="$(grep '^STALWART_RECOVERY_ADMIN=' .env | tail -n1 | cut -d= -f2-)"
if [[ "$recovery_admin" != *:* ]]; then
  echo "STALWART_RECOVERY_ADMIN must use username:password form" >&2
  exit 1
fi

admin_user="${recovery_admin%%:*}"
admin_password="${recovery_admin#*:}"

device="$(curl -fsS -X POST "$stalwart_url/auth/device" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=stalwart-web-admin')"
user_code="$(jq -r .user_code <<<"$device")"
device_code="$(jq -r .device_code <<<"$device")"

auth_payload="$(jq -nc \
  --arg username "$admin_user" \
  --arg password "$admin_password" \
  --arg code "$user_code" \
  '{type:"authDevice",accountName:$username,accountSecret:$password,code:$code}')"
curl -fsS -X POST "$stalwart_url/api/auth" \
  -H 'Content-Type: application/json' \
  -d "$auth_payload" >/dev/null

sleep 2
token="$(curl -fsS -X POST "$stalwart_url/auth/token" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:device_code' \
  --data-urlencode "device_code=$device_code" \
  --data-urlencode 'client_id=stalwart-web-admin' | jq -r .access_token)"

query_payload="$(jq -nc \
  --arg hostname "$certificate_name" \
  '{using:["urn:ietf:params:jmap:core","urn:stalwart:jmap"],methodCalls:[["x:Certificate/query",{filter:{subjectAlternativeNames:$hostname}},"q1"]]}')"
certificate_id="$(curl -fsS \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  "$stalwart_url/jmap/" \
  -d "$query_payload" | jq -r '.methodResponses[0][1].ids[0] // empty')"

certificate="$(<"$certificate_path")"
private_key="$(<"$private_key_path")"

if [[ -n "$certificate_id" ]]; then
  set_payload="$(jq -nc \
    --arg id "$certificate_id" \
    --arg certificate "$certificate" \
    --arg private_key "$private_key" \
    '{using:["urn:ietf:params:jmap:core","urn:stalwart:jmap"],methodCalls:[["x:Certificate/set",{update:{($id):{certificate:{"@type":"Text",value:$certificate},privateKey:{"@type":"Text",secret:$private_key}}}},"s1"]]}')"
else
  set_payload="$(jq -nc \
    --arg certificate "$certificate" \
    --arg private_key "$private_key" \
    '{using:["urn:ietf:params:jmap:core","urn:stalwart:jmap"],methodCalls:[["x:Certificate/set",{create:{mail:{certificate:{"@type":"Text",value:$certificate},privateKey:{"@type":"Text",secret:$private_key}}}},"s1"]]}')"
fi

unset certificate private_key admin_password recovery_admin

response="$(curl -fsS \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  "$stalwart_url/jmap/" \
  -d "$set_payload")"

if jq -e '.methodResponses[0][1].notUpdated // .methodResponses[0][1].notCreated // empty' >/dev/null <<<"$response"; then
  jq '.methodResponses[0][1].notUpdated // .methodResponses[0][1].notCreated' <<<"$response" >&2
  exit 1
fi

docker compose restart stalwart >/dev/null
echo "Stalwart TLS certificate synchronized for $certificate_name"
