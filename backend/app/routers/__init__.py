from fastapi import APIRouter

from app.routers import dashboard, day_pass, edges, fares, history, quote, settings, stations

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, fares, quote, history, settings, day_pass):
    api.include_router(r.router)
