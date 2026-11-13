#!/bin/sh
# Install crontab for current-weather + snapshot ingest, then run crond.
set -eu

CW_SCHEDULE="${CURRENT_WEATHER_CRON_SCHEDULE:-0 * * * *}"
INGEST_SCHEDULE="${INGEST_CRON_SCHEDULE:-5 * * * *}"

{
  printf '%s\t/usr/local/bin/cron_current_weather.sh\n' "${CW_SCHEDULE}"
  printf '%s\t/usr/local/bin/cron_ingest.sh\n' "${INGEST_SCHEDULE}"
} > /etc/crontabs/root

echo "cron: current-weather schedule='${CW_SCHEDULE}' locations='${CURRENT_WEATHER_CRON_LOCATIONS:-da_nang,sai_gon}'"
echo "cron: ingest schedule='${INGEST_SCHEDULE}' locations='${INGEST_CRON_LOCATIONS:-da_nang,sai_gon}' base='${WEATHER_API_BASE_URL:-http://localhost:7500}'"

exec crond -f -l 2
