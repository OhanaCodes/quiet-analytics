#!/bin/bash
# Installs the files. Does NOT edit your nginx configuration — that one edit is yours to make,
# because a script that rewrites a stranger's vhost is a worse idea than two lines of copy-paste.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run with sudo.'; exit 1; }
here=$(cd "$(dirname "$0")/.." && pwd)

install -D -m 644 "$here/nginx/00-quiet-analytics.conf" /etc/nginx/conf.d/00-quiet-analytics.conf
install -D -m 644 "$here/bin/qa-input.py"               /usr/local/lib/quiet-analytics/qa-input.py
install -D -m 750 "$here/bin/quiet-report"              /usr/local/sbin/quiet-report
install -D -m 644 "$here/cron/quiet-analytics"          /etc/cron.d/quiet-analytics
install -d -m 700 /var/lib/quiet-analytics

touch /var/log/nginx/quiet.access.log
chmod 640 /var/log/nginx/quiet.access.log
chown www-data:adm /var/log/nginx/quiet.access.log 2>/dev/null || true

cat <<'NEXT'

Files installed. Two steps left, both yours:

  1. Edit /etc/nginx/conf.d/00-quiet-analytics.conf — section 3, the list of pages to count.
  2. Add the two lines from nginx/server-block.example.conf to your server { } block.

Then:  nginx -t && systemctl reload nginx
Test:  python3 tests/test-masking.py
Report: /var/lib/quiet-analytics/report.html  (root-only; copy it to your machine to read)
NEXT
