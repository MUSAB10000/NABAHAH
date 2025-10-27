from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime
from collections import defaultdict
from Nabah.app.utils.supabase_client import supabase
from pydantic import BaseModel
from Nabah.app.utils.llm_chat import ask_llm

router = APIRouter()

@router.get("/api/dashboard-stats")
async def get_dashboard_stats():
    if not supabase:
        print("Supabase client not initialized in get_dashboard_stats.")
        return JSONResponse({"error": "Database connection not available."}, status_code=500)
    try:
        persons = supabase.table("persons").select("has_mask, has_gloves, has_labcoat, has_glasses, created_at, status, in_red_zone").execute().data or []
        alerts = supabase.table("alerts").select("alert_type").execute().data or []
        spills = supabase.table("spills").select("*").execute().data or []
        videos = supabase.table("videos").select("*").execute().data or []

        persons_count = len(persons)
        alerts_count = len(alerts)
        spills_count = len(spills)
        videos_count = len(videos)

        safe_count = sum(
            1 for p in persons if all([
                p.get("has_mask") is True,
                p.get("has_gloves") is True,
                p.get("has_labcoat") is True,
                p.get("has_glasses") is True,
            ])
        )
        compliance_rate = round((safe_count / persons_count) * 100, 2) if persons_count > 0 else 0

        hours = set()
        for p in persons:
            ts = p.get("created_at")
            if ts:
                try:
                    dt_obj = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    hours.add(dt_obj.strftime('%Y-%m-%d %H'))
                except ValueError:
                    continue
        active_hours = len(hours)

        return JSONResponse({
            "persons_count": persons_count,
            "alerts_count": alerts_count,
            "spills_count": spills_count,
            "videos_count": videos_count,
            "compliance_rate": compliance_rate,
            "active_hours": active_hours
        })
    except Exception as e:
        print("Error fetching dashboard stats:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/dashboard-charts")
async def get_dashboard_charts():
    if not supabase:
        print("Supabase client not initialized in get_dashboard_charts.")
        return JSONResponse({"error": "Database connection not available."}, status_code=500)
    try:
        persons = supabase.table("persons").select("has_mask, has_gloves, has_labcoat, has_glasses, created_at, status, in_red_zone").execute().data or []
        alerts = supabase.table("alerts").select("alert_type").execute().data or []
        spills = supabase.table("spills").select("*").execute().data or []

        compliance_daily = defaultdict(lambda: [0, 0])
        for p in persons:
            created_at = p.get("created_at")
            if not created_at:
                continue
            try:
                day = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except ValueError:
                continue
            compliance_daily[day][0] += 1
            if all([p.get("has_mask") is True, p.get("has_gloves") is True, p.get("has_labcoat") is True, p.get("has_glasses") is True]):
                compliance_daily[day][1] += 1

        compliance_over_time = [
            {"day": d, "rate": round((c / t) * 100, 2) if t else 0}
            for d, (t, c) in sorted(compliance_daily.items())
        ]

        total_persons_for_ppe = len(persons) or 1
        ppe_compliance = {
            "Mask": round(sum(1 for p in persons if p.get("has_mask") is True) / total_persons_for_ppe * 100, 2),
            "Gloves": round(sum(1 for p in persons if p.get("has_gloves") is True) / total_persons_for_ppe * 100, 2),
            "Labcoat": round(sum(1 for p in persons if p.get("has_labcoat") is True) / total_persons_for_ppe * 100, 2),
            "Glasses": round(sum(1 for p in persons if p.get("has_glasses") is True) / total_persons_for_ppe * 100, 2)
        }

        zone_events = {"Red Zone": 0, "Other": 0}
        for p in persons:
            if str(p.get("status", "")).lower() == "unsafe":
                if p.get("in_red_zone") is True:
                    zone_events["Red Zone"] += 1
                else:
                    zone_events["Other"] += 1

        incident_types = defaultdict(int)
        for a in alerts:
            incident_types[a.get("alert_type", "Unknown")] += 1

        shift_buckets = {"Morning": [0, 0], "Evening": [0, 0], "Night": [0, 0]}
        for p in persons:
            created_at = p.get("created_at")
            if not created_at:
                continue
            try:
                hour = datetime.fromisoformat(created_at.replace('Z', '+00:00')).hour
            except ValueError:
                continue

            if 8 <= hour < 16:
                shift = "Morning"
            elif 16 <= hour < 24:
                shift = "Evening"
            else:
                shift = "Night"
            shift_buckets[shift][0] += 1
            if all([p.get("has_mask") is True, p.get("has_gloves") is True, p.get("has_labcoat") is True, p.get("has_glasses") is True]):
                shift_buckets[shift][1] += 1

        shift_compliance = {
            s: round((c / t) * 100, 2) if t else 0
            for s, (t, c) in shift_buckets.items()
        }

        unsafe_ratio_daily = defaultdict(lambda: [0, 0])
        for p in persons:
            created_at = p.get("created_at")
            if not created_at:
                continue
            try:
                day = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except ValueError:
                continue
            unsafe_ratio_daily[day][0] += 1
            if str(p.get("status", "")).lower() == "unsafe":
                unsafe_ratio_daily[day][1] += 1

        unsafe_ratio = {
            d: round((unsafe / total) * 100, 2) if total else 0
            for d, (total, unsafe) in sorted(unsafe_ratio_daily.items())
        }

        violation_counts = {"Mask": 0, "Gloves": 0, "Labcoat": 0, "Glasses": 0}
        for p in persons:
            if str(p.get("status", "")).lower() == "unsafe":
                if not p.get("has_mask"): violation_counts["Mask"] += 1
                if not p.get("has_gloves"): violation_counts["Gloves"] += 1
                if not p.get("has_labcoat"): violation_counts["Labcoat"] += 1
                if not p.get("has_glasses"): violation_counts["Glasses"] += 1

        alert_type_counts = defaultdict(int)
        for a in alerts:
            alert_type_counts[a.get("alert_type", "Unknown")] += 1

        spills_per_day = defaultdict(int)
        for s in spills:
            ts = s.get("detected_at") or s.get("created_at")
            if not ts:
                continue
            try:
                day = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                spills_per_day[day] += 1
            except ValueError:
                continue

        ppe_histogram = {
            "Fully Safe": sum(1 for p in persons if p["status"] == "safe"),
            "Unsafe": sum(1 for p in persons if p["status"] == "unsafe"),
        }

        avg_ppe_items = round(sum([
            int(p.get("has_mask", 0)) +
            int(p.get("has_gloves", 0)) +
            int(p.get("has_labcoat", 0)) +
            int(p.get("has_glasses", 0))
            for p in persons
        ]) / max(len(persons), 1), 2)

        unsafe_trend = defaultdict(lambda: [0, 0])
        for p in persons:
            ts = p.get("created_at")
            if not ts:
                continue
            try:
                day = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            except ValueError:
                continue
            unsafe_trend[day][0] += 1
            if str(p.get("status", "")).lower() == "unsafe":
                unsafe_trend[day][1] += 1

        unsafe_over_time = [
            {"day": d, "unsafe_rate": round((u / t) * 100, 2) if t else 0}
            for d, (t, u) in sorted(unsafe_trend.items())
        ]

        total_persons = len(persons) or 1
        ppe_missing_ratio = {
            "Mask": round(sum(1 for p in persons if not p.get("has_mask")) / total_persons * 100, 2),
            "Gloves": round(sum(1 for p in persons if not p.get("has_gloves")) / total_persons * 100, 2),
            "Labcoat": round(sum(1 for p in persons if not p.get("has_labcoat")) / total_persons * 100, 2),
            "Glasses": round(sum(1 for p in persons if not p.get("has_glasses")) / total_persons * 100, 2),
        }

        alerts_daily = defaultdict(int)
        for a in alerts:
            ts = a.get("created_at")
            if not ts:
                continue
            try:
                day = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                alerts_daily[day] += 1
            except ValueError:
                continue

        detections = supabase.table("detections").select("class_name, confidence").execute().data or []
        conf_by_class = defaultdict(list)
        for d in detections:
            if d.get("class_name") and d.get("confidence") is not None:
                conf_by_class[d["class_name"]].append(float(d["confidence"]))
        avg_confidence = {k: round(sum(v) / len(v), 2) for k, v in conf_by_class.items() if v}

        return JSONResponse({
            "compliance_over_time": compliance_over_time,
            "ppe_compliance": ppe_compliance,
            "zone_events": zone_events,
            "incident_types": incident_types,
            "shift_compliance": shift_compliance,
            "unsafe_ratio": unsafe_ratio,
            "violation_counts": violation_counts,
            "alert_type_counts": alert_type_counts,
            "spills_per_day": spills_per_day,
            "ppe_histogram": ppe_histogram,
            "avg_ppe_items": avg_ppe_items,
            "unsafe_over_time": unsafe_over_time,
            "ppe_missing_ratio": ppe_missing_ratio,
            "alerts_daily": alerts_daily,
            "avg_confidence": avg_confidence
        })

    except Exception as e:
        print("Error in charts:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/api/database")
async def get_database():
    try:
        tables = ["persons", "alerts", "spills", "videos", "detections", "clips"]
        result = {}
        for t in tables:
            try:
                rows = supabase.table(t).select("*").limit(100).execute().data or []
                result[t] = rows
            except Exception as sub_e:
                print(f"Error loading {t}: {sub_e}")
                result[t] = []
        return JSONResponse(result)
    except Exception as e:
        print("DB error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


class ChatRequest(BaseModel):
    question: str

@router.post("/api/db-chat")
async def db_chat(request: ChatRequest):
    try:
        answer = ask_llm(request.question)
        return JSONResponse({"answer": answer})
    except Exception as e:
        print("LLM chat error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)
