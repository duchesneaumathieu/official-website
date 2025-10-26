import os, json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

LOCALES_DIR = BASE_DIR / "locales"

VERSION_FILE = BASE_DIR.parent / "VERSION"
APP_VERSION = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "0.0.0"

CONTENTS_DIR = (BASE_DIR / "contents").resolve()
MARKDOWN_DIR = CONTENTS_DIR / "markdown"
ASSETS_DIR = CONTENTS_DIR / "assets"
HTML_DIR = CONTENTS_DIR / "html"

SERVICES_DATA = {
    "chatbot": {"url": os.getenv("SERVICES_CHATBOT_URL", "http://localhost:8080")},
    "grafana": {"url": os.getenv("SERVICES_GRAFANA_URL", "http://localhost:3000")},
    "mlflow": {"url": os.getenv("SERVICES_MLFLOW_URL", "http://localhost:5000")},
}

CONFIG_FILE = BASE_DIR / "config.json"
CONFIG = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        CONFIG = json.load(f)
