#!/usr/bin/env bash
set -euo pipefail

deploy_path="${PROD_DEPLOY_PATH:-/home/flagforge/nepal-compliance}"
stalwart_url="${STALWART_ADMIN_URL:-http://127.0.0.1:8181}"

cd "$deploy_path"

for command_name in curl docker jq; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Missing required command: $command_name" >&2
    exit 1
  }
done

stalwart_container="$(docker compose ps -q stalwart)"
if [[ -z "$stalwart_container" ]]; then
  echo "The Stalwart container is not running" >&2
  exit 1
fi

# Connections to a Docker-published port arrive from the Compose network's
# gateway. Allowing that exact address prevents Stalwart's scanner protection
# from banning Nginx and thereby locking every web user out.
proxy_address="$(docker inspect "$stalwart_container" | jq -r '
  .[0].NetworkSettings.Networks
  | to_entries
  | map(select(.key | endswith("_frappe_network")) | .value.Gateway)
  | first // empty
')"
if [[ -z "$proxy_address" ]]; then
  echo "Could not determine the Stalwart proxy gateway address" >&2
  exit 1
fi

recovery_admin="$(grep '^STALWART_RECOVERY_ADMIN=' .env | tail -n1 | cut -d= -f2-)"
if [[ "$recovery_admin" != *:* ]]; then
  echo "STALWART_RECOVERY_ADMIN must use username:password form" >&2
  exit 1
fi

admin_user="${recovery_admin%%:*}"
admin_password="${recovery_admin#*:}"

for _ in {1..30}; do
  if curl -fsS --max-time 3 "$stalwart_url/admin/" >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS --max-time 3 "$stalwart_url/admin/" >/dev/null

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

unset admin_password recovery_admin

read_payload='{"using":["urn:ietf:params:jmap:core","urn:stalwart:jmap"],"methodCalls":[["x:AllowedIp/query",{},"q1"],["x:AllowedIp/get",{"#ids":{"resultOf":"q1","name":"x:AllowedIp/query","path":"/ids/*"}},"g1"],["x:Http/get",{"ids":["singleton"]},"h1"]]}'
current="$(curl -fsS \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  "$stalwart_url/jmap/" \
  -d "$read_payload")"

allowed_exists="$(jq -r --arg address "$proxy_address" \
  '[.methodResponses[] | select(.[0] == "x:AllowedIp/get") | .[1].list[]? | select(.address == $address)] | length' \
  <<<"$current")"
http_exists="$(jq -r \
  '[.methodResponses[] | select(.[0] == "x:Http/get") | .[1].list[]? | select(.id == "singleton")] | length' \
  <<<"$current")"

if [[ "$http_exists" == "0" ]]; then
  http_set='{"create":{"proxy":{"useXForwarded":true}}}'
else
  http_set='{"update":{"singleton":{"useXForwarded":true}}}'
fi

if [[ "$allowed_exists" == "0" ]]; then
  allowed_set="$(jq -nc --arg address "$proxy_address" '{create:{nginx:{address:$address}}}')"
else
  allowed_set='{}'
fi

# proxyTrustedNetworks controls the binary PROXY protocol and must remain empty
# for an HTTP reverse proxy. X-Forwarded-For is handled by the Http setting.
set_payload="$(jq -nc \
  --argjson http "$http_set" \
  --argjson allowed "$allowed_set" \
  '{using:["urn:ietf:params:jmap:core","urn:stalwart:jmap"],methodCalls:[
    ["x:SystemSettings/set",{update:{singleton:{proxyTrustedNetworks:{}}}},"s1"],
    ["x:Http/set",$http,"h1"],
    ["x:AllowedIp/set",$allowed,"a1"]
  ]}')"

response="$(curl -fsS \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  "$stalwart_url/jmap/" \
  -d "$set_payload")"

if jq -e '[.methodResponses[][1] | .notCreated?, .notUpdated?] | any(. != null and . != {})' >/dev/null <<<"$response"; then
  jq '[.methodResponses[][1] | .notCreated?, .notUpdated?] | map(select(. != null and . != {}))' <<<"$response" >&2
  exit 1
fi

echo "Stalwart HTTP reverse proxy trust configured"
