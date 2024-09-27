#!/usr/bin/env bash

set -euo pipefail

if ! command -v ruff >/dev/null 2>&1; then
	echo ruff is not installed.
	exit 1
fi

ruff check --select I --fix .
ruff format
