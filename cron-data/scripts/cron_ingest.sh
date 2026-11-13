#!/bin/sh
# POST /api/v1/ingest for each configured location (weather_snapshots upsert).
set -eu

BASE_URL="${WEATHER_API_BASE_URL:-http://weather-api:7500}"
API_KEY="${WEATHER_API_KEY:-}"
LOCATIONS="${INGEST_CRON_LOCATIONS:-da_nang,sai_gon}"
GAP_SEC="${INGEST_CRON_GAP_SEC:-2}"
MAX_ATTEMPTS="${INGEST_CRON_MAX_ATTEMPTS:-2}"

if [ -z "${API_KEY}" ]; then
  echo "cron_ingest: WEATHER_API_KEY is required" >&2
  exit 1
fi

BASE_URL="${BASE_URL%/}"
fail=0
first=1

# BusyBox/ash: split on commas without requiring bash.
old_ifs=${IFS}
IFS=,
set -- ${LOCATIONS}
IFS=${old_ifs}

for location in "$@"; do
  location=$(printf '%s' "${location}" | tr -d '[:space:]')
  if [ -z "${location}" ]; then
    continue
  fi

  if [ "${first}" -eq 0 ] && [ "${GAP_SEC}" -gt 0 ] 2>/dev/null; then
    echo "cron_ingest: sleep ${GAP_SEC}s before next location"
    sleep "${GAP_SEC}"
  fi
  first=0

  echo "cron_ingest: POST location=${location}"
  attempt=1
  location_ok=0

  while [ "${attempt}" -le "${MAX_ATTEMPTS}" ]; do
    if [ "${attempt}" -gt 1 ]; then
      echo "cron_ingest: retry location=${location} attempt=${attempt}" >&2
      sleep 2
    fi

    body_file=$(mktemp)
    set +e
    status=$(
      curl -sS -o "${body_file}" -w "%{http_code}" \
        -X POST \
        -H "X-API-Key: ${API_KEY}" \
        -H "Accept: application/json" \
        "${BASE_URL}/api/v1/ingest?location=${location}"
    )
    curl_rc=$?
    set -e

    if [ "${curl_rc}" -ne 0 ] && { [ -z "${status}" ] || [ "${status}" = "000" ]; }; then
      echo "cron_ingest: failed location=${location} transport curl_rc=${curl_rc}" >&2
      rm -f "${body_file}"
      attempt=$((attempt + 1))
      continue
    fi

    case "${status}" in
      2??)
        cat "${body_file}"
        printf '\n'
        location_ok=1
        rm -f "${body_file}"
        break
        ;;
      502|504)
        echo "cron_ingest: failed location=${location} status=${status}" >&2
        code=$(
          sed -n 's/.*"code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${body_file}" \
            | head -n 1
        )
        if [ -n "${code}" ]; then
          echo "cron_ingest: error.code=${code}" >&2
        fi
        echo "cron_ingest: response=$(head -c 1000 "${body_file}")" >&2
        rm -f "${body_file}"
        attempt=$((attempt + 1))
        continue
        ;;
      *)
        echo "cron_ingest: failed location=${location} status=${status}" >&2
        code=$(
          sed -n 's/.*"code"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "${body_file}" \
            | head -n 1
        )
        if [ -n "${code}" ]; then
          echo "cron_ingest: error.code=${code}" >&2
        fi
        echo "cron_ingest: response=$(head -c 1000 "${body_file}")" >&2
        rm -f "${body_file}"
        break
        ;;
    esac
  done

  if [ "${location_ok}" -ne 1 ]; then
    fail=1
  fi
done

exit "${fail}"
