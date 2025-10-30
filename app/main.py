import json
from enum import Enum
from datetime import datetime
from pathlib import PurePosixPath
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from .resource import Resource, sanitize_url_path
from .lang import select_accept_language
from .config import Settings

app = FastAPI(title=Settings.general.app_title)

if Settings.general.serve_static:
    app.mount("/static", StaticFiles(directory=Settings.paths.static_dir), name="static")

templates = Jinja2Templates(directory=Settings.paths.templates_dir)

# Make url_for() generate HTTPS links behind a reverse proxy
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

templates.env.globals["current_year"] = lambda: datetime.now().year
templates.env.globals["app_version"] = lambda: Settings.general.app_version

def swap_lang(lang, url_path):
    new_lang = "fr" if lang == "en" else "en"
    return new_lang / url_path.relative_to(lang)

def load_locale(path: str):
    with open(Settings.paths.locales_dir / path, 'r') as f:
        return json.load(f)

@app.get("/{raw_path:path}", response_class=HTMLResponse)
async def serve(request: Request, raw_path: str):
    url_path = sanitize_url_path(raw_path) if raw_path else PurePosixPath("home")
    if url_path.parts[0] in Settings.general.languages:
        lang = url_path.parts[0]
    else:
        lang = select_accept_language(request)
        url_path = lang / url_path
    
    resource = Resource(url_path)

    redirect = raw_path != str(url_path)
    alt_url_path = swap_lang(lang, url_path)
    content_found = resource.exists() or Resource(alt_url_path).exists()
    
    if redirect and content_found:
        return RedirectResponse(url=f"/{url_path}", status_code=307)
    
    context = {
        "request": request,
        "locale": load_locale(f"{lang}/base.json"),
        "services": Settings.services,
    }
    context["locale"]["switch_href"] = alt_url_path
    if resource.exists():
        context["content"] = resource.html()
        return templates.TemplateResponse("content.html", context, status_code=200)

    if content_found:
        # 404 with a switch language alternative
        context["locale"]["e404"] = load_locale(f"{lang}/alt_404.json")
        context["locale"]["e404"]["href"] = alt_url_path
    else:
        # Load the standard 404 locale
        context["locale"]["e404"] = load_locale(f"{lang}/404.json")
        context["locale"]["e404"]["href"] = f"{lang}/home"
    
    return templates.TemplateResponse("404.html", context, status_code=404)
