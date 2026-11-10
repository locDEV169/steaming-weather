#!/bin/sh
# Install crontab from CURRENT_WEATHER_CRON_SCHEDULE, then run crond in foreground.
set -eu

SCHEDULE="${CURRENT_WEATHER_CRON_SCHEDULE:-0 * * * *}"
printf '%s\t/usr/local/bin/cron_current_weather.sh\n' "${SCHEDULE}" \
  > /etc/crontabs/root

echo "current-weather-cron: schedule='${SCHEDULE}' locations='${CURRENT_WEATHER_CRON_LOCATIONS:-da_nang,sai_gon}' base='${WEATHER_API_BASE_URL:-http://localhost:7500}'"

exec crond -f -l 2
