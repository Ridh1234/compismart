#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate

pip install "setuptools<81" wheel
pip install --no-build-isolation -r requirements.txt
python -c "import whisper; from app.core.config import settings; whisper.load_model(settings.whisper_model_size, download_root=settings.whisper_model_dir)"
