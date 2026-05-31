#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip "setuptools<81" wheel
python -m pip install --no-build-isolation -r requirements.txt
