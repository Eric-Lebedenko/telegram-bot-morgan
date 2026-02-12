$ErrorActionPreference = "Stop"

# Ensure EN/RU models are present (downloads on first run).
libretranslate --host 127.0.0.1 --port 5000 --update-models --load-only en,ru
