#!/bin/sh

cat <<'EOF'

These commands are to be normally put in pyproject.toml
For now run them manually.

for linting checks run:
    ruff check --select I .

to apply linting fixes and formatting run:
    ruff check --select I --fix .
    ruff format

EOF
