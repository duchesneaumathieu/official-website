import os, string 
from typing import Any
from pathlib import Path
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Paths:
    backend_dir: Path = Path(__file__).resolve().parent.parent
    version_file: Path = backend_dir / "VERSION"
    
    base_dir: Path = Path(os.path.expandvars(os.getenv("WEBSITE_BASE_DIR", "/")))
    frontend_dir: Path = Path(os.path.expandvars(os.getenv("WEBSITE_FRONTEND_DIR", base_dir / "frontend")))
    contents_dir: Path = Path(os.path.expandvars(os.getenv("WEBSITE_CONTENTS_DIR", base_dir / "contents")))

    templates_dir: Path = Path(os.path.expandvars(os.getenv("WEBSITE_TEMPLATES_DIR", frontend_dir / "templates")))
    static_dir: Path = Path(os.path.expandvars(os.getenv("WEBSITE_STATIC_DIR", frontend_dir / "static")))
    locales_dir: Path = Path(os.path.expandvars(os.getenv("WEBSITE_LOCALES_DIR", frontend_dir / "locales")))

    markdown_dir: Path = contents_dir / "markdown"
    assets_dir: Path = contents_dir / "assets"
    html_dir: Path = contents_dir / "html"
Paths = Paths()

@dataclass(frozen=True)
class Service:
    name: str
    url: str

@dataclass(frozen=True)
class Services:
    chatbot: Service = Service(name="Chatbot", url=os.getenv("WEBSITE_SERVICES_CHATBOT_URL", "/services/chatbot"))
    grafana: Service = Service(name="Grafana", url=os.getenv("WEBSITE_SERVICES_GRAFANA_URL", "/services/grafana"))
    mlflow: Service = Service(name="MLflow", url=os.getenv("WEBSITE_SERVICES_MLFLOW_URL", "/services/mlflow"))
Services = Services()

@dataclass(frozen=True)
class URLRules:
    forbidden_strings: tuple[str] = ("\\", "..", "%2e%2e")
    forbidden_nodes: tuple[str] = ("", ".", "..", "index")
    allowed_characters: str = string.ascii_letters + string.digits + "/-?=&"
    max_length: int = 256
    max_depth: int = 5
URLRules = URLRules()

@dataclass(frozen=True)
class CacheSettings:
    html_cache: dict[str, Any] = field(default_factory=lambda:{"maxsize": 128})
    markdown_cache: dict[str, Any] = field(default_factory=lambda:{"maxsize": 128})
    sanitize_url_path: dict[str, Any] = field(default_factory=lambda:{"maxsize": 256})
CacheSettings = CacheSettings()

@dataclass(frozen=True)
class MarkdownSettings:
    extras: tuple[str] = ("metadata", "markdown-in-html", "fenced-code-blocks", "latex", "wiki-tables")
MarkdownSettings = MarkdownSettings()

@dataclass(frozen=True)
class General:
    app_title: str = "Official Website"
    try:
        app_version: str = Paths.version_file.read_text(encoding="utf-8").strip()
    except Exception:
        app_version: str = "0.0.0"
    if "WEBSITE_SERVE_STATIC" in os.environ:
        serve_static: bool = True
    else:
        serve_static: bool = False
    languages: tuple[str] = ("en", "fr")
General = General()

@dataclass(frozen=True)
class Settings:
    general = General
    paths = Paths
    services = Services
    url_rules = URLRules
    cache = CacheSettings
    markdown = MarkdownSettings
Settings = Settings()
