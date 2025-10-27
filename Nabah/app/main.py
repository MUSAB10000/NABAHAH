import sys, os
from dotenv import load_dotenv

sys.path.append("/content")
sys.path.append("/content/Nabah")
print("Added /content and /content/Nabah to sys.path")

load_dotenv("/content/Nabah/.env")
print(".env loaded inside main.py")

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from Nabah.app.routes import api_routes, api_stream, api_video
from Nabah.app.routes.auth_routes import router as auth_router
from Nabah.app.routes.dashboard_routes import router as dashboard_router
from Nabah.app.routes.api_routes import router as api_router

PROJECT_ROOT = "/content/Nabah/app"
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")

app = FastAPI(title="Nabah - Intelligent Lab Safety Monitoring System")
app.add_middleware(SessionMiddleware, secret_key="supersecretkey123")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(api_router)
app.include_router(api_routes.router)
app.include_router(api_stream.router)
app.include_router(api_video.router)

print("Nabah FastAPI Server is running successfully!")
