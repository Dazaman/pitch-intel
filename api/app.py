from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import compare, explore, health, players, search, teams

app = FastAPI(title="Pitch Intel API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(players.router, prefix="/api")
app.include_router(teams.router, prefix="/api")
app.include_router(compare.router, prefix="/api")
app.include_router(explore.router, prefix="/api")
