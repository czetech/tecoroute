#!/bin/sh
set -e

entrypoint=tecoroute

if [ $# -eq 0 ]; then
  set -- $entrypoint
fi

if [ "${1:0:1}" = '-' ] || [ "$1" = 'connector' ]; then
  set -- $entrypoint "$@"
fi

exec "$@"
