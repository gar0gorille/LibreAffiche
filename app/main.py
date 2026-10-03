from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.panel import router as panel_router
from app.api.panel_event import router as panel_event_router


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="LibreAffiche API",
    version="0.1.0",
)


# API
app.include_router(panel_router)
app.include_router(panel_event_router)


# Static files
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# HTML templates
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


@app.get("/", response_class=HTMLResponse)
def map_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="map.html",
    )