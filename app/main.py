from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
from pathlib import Path

VERSION_FILE = Path(__file__).parent.parent / "VERSION"


# Create FastAPI app
app = FastAPI(title="My Portfolio Website")

# Mount static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates directory
templates = Jinja2Templates(directory="templates")

def app_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "0.0.0"

templates.env.globals["current_year"] = lambda: datetime.now().year
templates.env.globals["app_version"] = app_version

# TODO: user language redirect
# /, /home --> /user-lang/home (default en)
# /path --> /user-lang/path (default en)

PAGES = ["home", "blog", "grafana", "mlflow"]
LANGUAGES = ['en', 'fr']

@app.get("/", response_class=HTMLResponse)
async def redirect_home(request: Request):
    return RedirectResponse(url="/en/home", status_code=307)

@app.get("/{string}", response_class=HTMLResponse)
async def redirect(request: Request, string: str):
    if string in LANGUAGES:
        return RedirectResponse(url=f"/{string}/home", status_code=307)
    return RedirectResponse(url=f"/en/{string}", status_code=307)

# Home page route
@app.get("/{lang}/{page}", response_class=HTMLResponse)
async def get(request: Request, lang: str, page: str):
    if lang not in LANGUAGES or page not in PAGES:
        raise HTTPException(status_code=404, detail="Page not found")

    other_lang = 'fr' if lang=='en' else 'en'
    other_language = "Français" if lang=='en' else "English"
    
    context = {
        "request": request,
        "lang": lang,
        "other_language": other_language,
        "other_lang_path": f"{other_lang}/{page}",
    }

    if not Path(f"templates/{page}.html").exists():
        return templates.TemplateResponse("under-construction.html", context)
        
    return templates.TemplateResponse(f"{page}.html", context)

