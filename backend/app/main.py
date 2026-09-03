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
user_index_html = workspace_root / "index.html"
user_login_html = workspace_root / "login.html"
user_signup_html = workspace_root / "signup.html"
frontend_dist = workspace_root / "frontend" / "dist"

from fastapi import Request
from fastapi.responses import JSONResponse

# 1. Primary Unified Full-Stack Application
if frontend_dist.exists() and (frontend_dist / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


@app.get("/", tags=["Unified Application"])
async def serve_user_root(request: Request):
    """Serves the complete unified application for browsers, or API metadata for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        if frontend_dist.exists() and (frontend_dist / "index.html").exists():
            return FileResponse(frontend_dist / "index.html")
        elif user_index_html.exists():
            return FileResponse(user_index_html)

    return JSONResponse({
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/healthz",
    })


@app.get("/portal", tags=["User Frontend"], response_class=FileResponse)
@app.get("/portal.html", tags=["User Frontend"], response_class=FileResponse)
async def serve_static_portal():
    """Serves the standalone static dashboard if requested."""
    if user_index_html.exists():
        return FileResponse(user_index_html)
    return FileResponse(frontend_dist / "index.html")


@app.get("/login", tags=["User Frontend"], response_class=FileResponse)
@app.get("/login.html", tags=["User Frontend"], response_class=FileResponse)
async def serve_user_login():
    """Serves the user's login and authentication page."""
    if user_login_html.exists():
        return FileResponse(user_login_html)
    return FileResponse(user_index_html)


@app.get("/signup", tags=["User Frontend"], response_class=FileResponse)
@app.get("/signup.html", tags=["User Frontend"], response_class=FileResponse)
async def serve_user_signup():
    """Serves the user's dedicated registration and sign-up page."""
    if user_signup_html.exists():
        return FileResponse(user_signup_html)
    elif user_login_html.exists():
        return FileResponse(user_login_html)
    return FileResponse(user_index_html)


# 2. Universal Client Routing (all tabs /overview, /schedule, /prescriptions, /safety, /reports, /react)
@app.get("/overview", tags=["Unified Application"])
@app.get("/schedule", tags=["Unified Application"])
@app.get("/prescriptions", tags=["Unified Application"])
@app.get("/safety", tags=["Unified Application"])
@app.get("/reports", tags=["Unified Application"])
@app.get("/history", tags=["Unified Application"])
@app.get("/react", tags=["Unified Application"])
@app.get("/react/{full_path:path}", tags=["Unified Application"])
async def serve_app_tabs(full_path: str = ""):
    """Routes client tabs back to the unified master application."""
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        return FileResponse(frontend_dist / "index.html")
    elif user_index_html.exists():
        return FileResponse(user_index_html)
    return JSONResponse({"message": "Application bundle not found."})

