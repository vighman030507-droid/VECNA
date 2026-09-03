from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.local_actions import router as local_actions_router
from app.api.nexus_tools import router as nexus_tools_router
from app.api.speech import router as speech_router
from app.api.web_actions import router as web_actions_router
from app.services.telegram_service import start_telegram_uplink
from app.settings import settings

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="VECNA Intelligence Backend", version="0.2.0")

@app.on_event("startup")
async def on_startup() -> None:
    start_telegram_uplink()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    print(f"VALIDATION ERROR for {request.method} {request.url.path}: {exc.errors()}", flush=True)
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Restrict CORS strictly to local frontend origins (never use wildcard *)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(chat_router)
app.include_router(local_actions_router)
app.include_router(nexus_tools_router)
app.include_router(speech_router)
app.include_router(web_actions_router)


# ==============================================================================
# PHASE 0: THE HEARTBEAT (Health Check Endpoint)
# ==============================================================================
@app.get("/api/health")
async def health() -> dict[str, str]:
    # TODO (Phase 0): Return {"status": "ok"} so the frontend knows the backend is alive
    return {"status": "ok"}
