#!/bin/sh
set -eu
exec /usr/bin/wget -q -O /dev/null http://127.0.0.1:8193/healthz
