from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = "https://uycfvnrkyvvlvcwbtwzi.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV5Y2Z2bnJreXZ2bHZjd2J0d3ppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjExMjI2ODksImV4cCI6MjA3NjY5ODY4OX0.IKGEgUYJx8w1D3V4YSBCi3ZhCUrTYSGyRDHVQWlzDcc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()
templates = Jinja2Templates(directory="/content/Nabah/app/templates")


@router.get("/", response_class=HTMLResponse)
@router.get("/signin", response_class=HTMLResponse)
async def signin_page(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})


@router.post("/signin", response_class=HTMLResponse)
async def signin_user(request: Request, username: str = Form(...), password: str = Form(...)):
    response = (
        supabase.table("users")
        .select("*")
        .or_(f"username.eq.{username},email.eq.{username}")
        .eq("password", password)
        .execute()
    )
    if response.data:
        user = response.data[0]
        request.session["user"] = {
            "id": user["id"],
            "username": user["username"],
            "role": user.get("role", "user"),
        }
        print(f"{user['username']} logged in successfully.")
        return RedirectResponse(url="/dashboard/overview", status_code=303)
    else:
        return templates.TemplateResponse(
            "signin.html",
            {"request": request, "error": "Invalid username or password."},
        )


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup", response_class=HTMLResponse)
async def signup_user(request: Request, name: str = Form(...), employee_id: str = Form(...),
                      email: str = Form(...), password: str = Form(...)):
    try:
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return templates.TemplateResponse(
                "signup.html", {"request": request, "error": "Email already exists"},
            )

        new_user = {
            "username": name,
            "email": email,
            "password": password,
            "role": "user",
            "created_at": datetime.utcnow().isoformat(),
        }
        supabase.table("users").insert(new_user).execute()
        print(f"New user registered: {name}")
        return RedirectResponse(url="/signin", status_code=303)
    except Exception as e:
        print("Signup error:", e)
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Signup failed. Please try again."},
        )


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/signin", status_code=303)
