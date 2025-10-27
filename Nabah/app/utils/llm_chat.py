# llm_chat.py
import os
import re
import requests
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta, timezone

env_path = "/content/Nabah/.env"
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print(f".env not found at {env_path}")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL")

print("llm_chat config:")
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY exists:", bool(SUPABASE_KEY))

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        f"Missing Supabase credentials in llm_chat.\nSUPABASE_URL={SUPABASE_URL}\nSUPABASE_KEY exists={bool(SUPABASE_KEY)}"
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

from Nabah.app.utils.rag_search import search_context

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Lab-RAG",
}

LAB_KEYWORDS = [
    "lab", "safety", "ppe", "violation", "violations", "alert", "alerts",
    "redzone", "red zone", "spill", "spills", "detection", "detections",
    "person", "persons", "people", "video", "videos",
    "مختبر", "سلامة", "معدات الوقاية", "قفازات", "خوذة", "نظارات",
    "تنبيه", "تنبيهات", "منطقة خطرة", "تسرب", "أشخاص", "فيديو"
]

def _is_arabic(q: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", q))

def _gate_lab(q: str) -> bool:
    ql = q.lower()
    return any(k in ql for k in LAB_KEYWORDS)

COUNT_PATTERNS_EN = [
    r"\bhow many\b", r"\bcount\b", r"\bnumber of\b", r"\btotal\b",
]
COUNT_PATTERNS_AR = [
    r"\bكم\b", r"\bعدد\b", r"\bالمجموع\b", r"\bإجمالي\b",
]

def _is_count_query(q: str, arabic: bool) -> bool:
    ql = q.lower()
    pats = COUNT_PATTERNS_AR if arabic else COUNT_PATTERNS_EN
    return any(re.search(p, ql) for p in pats)

def _get_time_filter(q: str):
    ql = q.lower()
    today = datetime.now(timezone.utc).date()
    if any(k in ql for k in ["today", "اليوم"]):
        return today, today
    if any(k in ql for k in ["yesterday", "البارحة", "أمس"]):
        y = today - timedelta(days=1)
        return y, y
    if any(k in ql for k in ["this week", "الأسبوع", "اسبوع"]):
        start = today - timedelta(days=today.weekday())
        end = today
        return start, end
    return None, None

from datetime import datetime, date, timedelta, timezone

def _count_table(table: str, date_range=None) -> int:
    query = supabase.table(table).select("id", count="exact")
    if date_range and all(isinstance(d, date) for d in date_range if d):
        start, end = date_range
        start_iso = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).isoformat()
        end_iso = datetime.combine(end, datetime.max.time(), tzinfo=timezone.utc).isoformat()
        query = query.gte("created_at", start_iso).lte("created_at", end_iso)
    res = query.limit(1).execute()
    return res.count or 0

def _count_ppe_alerts_only() -> int:
    res = supabase.table("alerts").select("id", count="exact").eq("alert_type", "ppe_violation").limit(1).execute()
    return res.count or 0

def _maybe_numeric_answer(q: str, arabic: bool):
    if not _is_count_query(q, arabic):
        return None
    t = q.lower()
    n = None
    if "ppe" in t or "معدات" in t or "وقاية" in t:
        n = _count_ppe_alerts_only()
        return (f"There are {n} PPE violation alerts in the database."
                if not arabic else f"يوجد {n} مخالفة لمعدات الوقاية في قاعدة البيانات.")
    if "spill" in t or "تسرب" in t:
        n = _count_table("spills")
        return (f"There are {n} liquid spills recorded."
                if not arabic else f"يوجد {n} حالة تسرب مسجلة.")
    if any(k in t for k in ["person", "persons", "people", "أشخاص", "شخص"]):
        date_range = _get_time_filter(q)
        n = _count_table("persons", date_range if any(date_range) else None)
        if date_range and date_range[0]:
            if "today" in q or "اليوم" in q:
                return (f"There were {n} persons detected today."
                        if not arabic else f"تم تسجيل {n} شخصًا اليوم.")
            if "yesterday" in q or "أمس" in q or "البارحة" in q:
                return (f"There were {n} persons detected yesterday."
                        if not arabic else f"تم تسجيل {n} شخصًا بالأمس.")
            if "week" in q or "أسبوع" in q:
                return (f"There were {n} persons detected this week."
                        if not arabic else f"تم تسجيل {n} شخصًا خلال هذا الأسبوع.")
        return (f"There are {n} persons currently recorded."
                if not arabic else f"يوجد {n} شخصًا مسجلاً.")
    if "detection" in t or "اكتشاف" in t:
        n = _count_table("detections")
        return (f"There are {n} total detections logged."
                if not arabic else f"يوجد {n} عملية كشف مسجلة.")
    if "alert" in t or "تنبيه" in t or "تنبيهات" in t:
        n = _count_table("alerts")
        return (f"There are {n} alerts recorded."
                if not arabic else f"يوجد {n} تنبيهًا مسجلًا.")
    if "video" in t or "فيديو" in t:
        n = _count_table("videos")
        return (f"There are {n} videos recorded."
                if not arabic else f"يوجد {n} فيديو مسجل.")
    return ("I don't have enough data in the database."
            if not arabic else "لا توجد بيانات كافية في قاعدة البيانات.")

def _compare_trends(q: str, arabic: bool) -> str | None:
    ql = q.lower()
    if not any(k in ql for k in ["today", "yesterday", "week", "اليوم", "أمس", "البارحة", "أسبوع"]):
        return None
    if "person" in ql or "people" in ql or "أشخاص" in ql or "شخص" in ql:
        table = "persons"
        metric = "persons detected"
    elif "alert" in ql or "تنبيه" in ql:
        table = "alerts"
        metric = "alerts recorded"
    elif "spill" in ql or "تسرب" in ql:
        table = "spills"
        metric = "liquid spills"
    elif "ppe" in ql or "معدات" in ql or "وقاية" in ql:
        table = "alerts"
        metric = "PPE violations"
    else:
        return None
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=7)
    def _count_between(table, start_date, end_date):
        res = (
            supabase.table(table)
            .select("id", count="exact")
            .gte("created_at", f"{start_date}T00:00:00Z")
            .lte("created_at", f"{end_date}T23:59:59Z")
            .limit(1)
            .execute()
        )
        return res.count or 0
    today_count = _count_between(table, today, today)
    yest_count = _count_between(table, yesterday, yesterday)
    week_count = _count_between(table, week_start, today)
    if "week" in ql or "أسبوع" in ql:
        trend = f"{week_count} {metric} this week"
        return (f"There were {trend}." if not arabic else f"تم تسجيل {week_count} {metric} خلال هذا الأسبوع.")
    if "yesterday" in ql or "أمس" in ql or "البارحة" in ql:
        diff = today_count - yest_count
        if diff > 0:
            return f"There were {diff} more {metric} today than yesterday ({today_count} vs {yest_count})." if not arabic else f"زاد عدد {metric} اليوم بمقدار {diff} مقارنة بالأمس ({today_count} مقابل {yest_count})."
        elif diff < 0:
            return f"There were {abs(diff)} fewer {metric} today than yesterday ({today_count} vs {yest_count})." if not arabic else f"انخفض عدد {metric} اليوم بمقدار {abs(diff)} مقارنة بالأمس ({today_count} مقابل {yest_count})."
        else:
            return f"The number of {metric} today and yesterday are the same ({today_count})." if not arabic else f"عدد {metric} اليوم والأمس متساوي ({today_count})."
    if "today" in ql or "اليوم" in ql:
        return f"There were {today_count} {metric} recorded today." if not arabic else f"تم تسجيل {today_count} {metric} اليوم."
    return None

def _retrieve_context(question: str, top_k: int = 8) -> str:
    q = question.lower()
    tables = []
    if any(k in q for k in ["ppe", "equipment", "وقاية", "معدات"]):
        tables = ["alerts", "persons"]
    elif any(k in q for k in ["alert", "تنبيه"]):
        tables = ["alerts"]
    elif any(k in q for k in ["spill", "تسرب"]):
        tables = ["spills"]
    elif any(k in q for k in ["video", "فيديو"]):
        tables = ["videos"]
    elif any(k in q for k in ["person", "people", "شخص", "أشخاص"]):
        tables = ["persons"]
    elif any(k in q for k in ["detection", "كشف", "detections"]):
        tables = ["detections"]
    else:
        tables = ["alerts", "spills", "persons", "detections", "videos"]
    context_parts = []
    for table in tables:
        try:
            res = (
                supabase.table(table)
                .select("*")
                .order("created_at", desc=True)
                .limit(top_k)
                .execute()
            )
            if res.data:
                context_parts.append(f"### {table.upper()} SAMPLE ###\n{json.dumps(res.data[:top_k], indent=2)}")
        except Exception as e:
            print(f"Error reading {table}: {e}")
    context = "\n\n".join(context_parts)
    return context if context else "No relevant database context found."

def _llm(messages: list[dict]) -> str:
    payload = {"model": LLM_MODEL, "messages": messages, "temperature": 0.2}
    r = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def ask_llm(question: str, top_k: int = 8) -> str:
    arabic = _is_arabic(question)
    if not _gate_lab(question):
        return ("I’m restricted to lab-safety database topics (PPE, alerts, spills, detections, persons, videos)."
                if not arabic else "أنا مقيد بالإجابة عن مواضيع قاعدة بيانات السلامة بالمختبر فقط (معدات الوقاية، التنبيهات، التسربات، الاكتشافات، الأشخاص، الفيديوهات).")
    numeric = _maybe_numeric_answer(question, arabic)
    if numeric:
        return numeric.strip()
    trend = _compare_trends(question, arabic)
    if trend:
        return trend.strip()
    ctx = search_context(question, top_k=top_k, threshold=0.0)
    if not ctx:
        return ("I don't have enough data in the database."
                if not arabic else "لا توجد بيانات كافية في قاعدة البيانات.")
    context_text = "\n".join(f"- [{r.get('table_name')}] {r.get('text')}" for r in ctx if r.get("text"))
    SYSTEM_PROMPT = f"""
    You are the official Database Assistant for the Intelligent Laboratory Safety Monitoring System (ILSMS).
    Your role:
    - Answer ONLY based on lab-safety database information (PPE, alerts, spills, detections, persons, videos).
    - If asked anything unrelated, refuse politely.
    - Be concise, clear, and factual.
    - If data is missing, say: "I don't have enough data in the database."
    - If comparing time (today/yesterday/week), use numeric data when possible.
    - For safety comparisons: fewer alerts or spills = safer day.
    - Respond in {'Arabic' if arabic else 'English'} only.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (f"Question: {question}\n\nRelevant database context:\n{context_text}\n\nAnswer concisely in {'Arabic' if arabic else 'English'} only.")},
    ]
    try:
        response = _llm(messages)
        if not response or not response.strip():
            return ("The AI model could not generate a valid response."
                    if not arabic else "لم يتمكن نموذج الذكاء الاصطناعي من تقديم إجابة صحيحة.")
        response = response.replace("<s>", "").replace("</s>", "").strip()
        return response
    except Exception as e:
        return (f"LLM error: {e}" if not arabic else f"حدث خطأ أثناء الاتصال بالنموذج: {e}")

