from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import actions, auth, intentions
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Intention Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(intentions.router)
app.include_router(actions.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
