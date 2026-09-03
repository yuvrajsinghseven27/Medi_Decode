from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.api.v1.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered prescription parsing and medication safety platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set up CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Register API routes under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/healthz", tags=["System"])
async def health_check():
    """System health and readiness verification endpoint."""
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Mount uploads directory for prescription files
uploads_dir = Path("uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Paths to user's frontend files and compiled React app
workspace_root = Path(__file__).resolve().parent.parent.parent
static_dir = Path(__file__).resolve().parent / "static"


def resolve_frontend_file(filename: str):
    for candidate in [workspace_root / filename, static_dir / filename, Path("/app") / filename]:
        if candidate.exists():
            return candidate
    return workspace_root / filename


user_index_html = resolve_frontend_file("index.html")
user_login_html = resolve_frontend_file("login.html")
user_signup_html = resolve_frontend_file("signup.html")
frontend_dist = workspace_root / "frontend" / "dist"

# 1. Primary User Frontend Routes (index.html, login.html & signup.html)
@app.get("/", tags=["User Frontend"], response_class=FileResponse)
async def serve_user_root():
    """Serves the user's primary customized dashboard (index.html)."""
    idx = resolve_frontend_file("index.html")
    if idx and idx.exists():
        return FileResponse(idx)
    elif frontend_dist.exists() and (frontend_dist / "index.html").exists():
        return FileResponse(frontend_dist / "index.html")
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


@app.get("/index.html", tags=["User Frontend"], response_class=FileResponse)
async def serve_user_index_file():
    """Serves user's index.html directly."""
    idx = resolve_frontend_file("index.html")
    if idx and idx.exists():
        return FileResponse(idx)
    return FileResponse(frontend_dist / "index.html")


@app.get("/login", tags=["User Frontend"], response_class=FileResponse)
@app.get("/login.html", tags=["User Frontend"], response_class=FileResponse)
async def serve_user_login():
    """Serves the user's login and authentication page."""
    log = resolve_frontend_file("login.html")
    if log and log.exists():
        return FileResponse(log)
    idx = resolve_frontend_file("index.html")
    if idx and idx.exists():
        return FileResponse(idx)
    return FileResponse(frontend_dist / "index.html")


@app.get("/signup", tags=["User Frontend"], response_class=FileResponse)
@app.get("/signup.html", tags=["User Frontend"], response_class=FileResponse)
async def serve_user_signup():
    """Serves the user's dedicated registration and sign-up page."""
    sup = resolve_frontend_file("signup.html")
    if sup and sup.exists():
        return FileResponse(sup)
    log = resolve_frontend_file("login.html")
    if log and log.exists():
        return FileResponse(log)
    idx = resolve_frontend_file("index.html")
    if idx and idx.exists():
        return FileResponse(idx)
    return FileResponse(frontend_dist / "index.html")


# 2. Secondary React Client (available at /react)
if frontend_dist.exists():
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/react", tags=["React Frontend"])
    @app.get("/react/{full_path:path}", tags=["React Frontend"])
    async def serve_react_frontend(full_path: str = ""):
        """Serves the secondary React / Vite client application."""
        return FileResponse(frontend_dist / "index.html")
