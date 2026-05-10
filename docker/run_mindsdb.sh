#!/usr/bin/env bash
set -euo pipefail

docker run --name visionguard_mindsdb \
  -e MINDSDB_APIS=http,mysql \
  -p 47334:47334 \
  -p 47335:47335 \
  mindsdb/mindsdb:latest
