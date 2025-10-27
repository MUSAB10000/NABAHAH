from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="/content/Nabah/app/templates")


@router.get("/dashboard/overview", response_class=HTMLResponse)
async def overview_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/signin", status_code=303)
    return templates.TemplateResponse("dashboard_overview.html", {"request": request, "user": user})


@router.get("/dashboard/live", response_class=HTMLResponse)
async def live_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/signin", status_code=303)
    return templates.TemplateResponse("dashboard_live.html", {"request": request, "user": user})


@router.get("/dashboard/database", response_class=HTMLResponse)
async def database_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/signin", status_code=303)
    return templates.TemplateResponse("dashboard_database.html", {"request": request, "user": user})


@router.get("/dashboard/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/signin", status_code=303)
    return templates.TemplateResponse("dashboard_settings.html", {"request": request, "user": user})
