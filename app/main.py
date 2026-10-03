from fastapi import FastAPI

from app.api.panel import router as panel_router
from app.api.panel_event import router as panel_event_router


app = FastAPI(
    title="LibreAffiche API",
    version="0.1.0",
)

app.include_router(panel_router)
app.include_router(panel_event_router)


@app.get("/")
def root():
    return {"message": "LibreAffiche API"}
