from datetime import datetime, timezone
from Nabah.app.utils.supabase_client import supabase

def save_video(video_name, title, uploaded_by=None, uploaded_at=None):
    try:
        data = {
            "video_name": video_name,
            "uploaded_at": uploaded_at or datetime.now(timezone.utc).isoformat(),
            "title": title,
            "uploaded_by": uploaded_by
        }
        response = supabase.table("videos").insert(data).execute()
        print(f"Video saved: {video_name}")
        return response
    except Exception as e:
        print(f"Error saving video: {e}")
        return None

def save_person(video_id, track_id, frame_number, has_mask, has_gloves, has_labcoat, has_glasses, in_red_zone, status, created_at):
    try:
        data = {
            "video_id": video_id,
            "track_id": track_id,
            "frame_number": frame_number,
            "has_mask": has_mask,
            "has_gloves": has_gloves,
            "has_labcoat": has_labcoat,
            "has_glasses": has_glasses,
            "in_red_zone": in_red_zone,
            "status": status,
            "created_at": created_at
        }
        response = supabase.table("persons").insert(data).execute()
        print(f"Person saved: frame={frame_number}, status={status}")
        return response
    except Exception as e:
        print(f"Error saving person: {e}")
        return None

def save_detection(class_name, confidence, bbox, frame_path, detected_at=None):
    try:
        data = {
            "class_name": class_name,
            "confidence": confidence,
            "bbox": bbox,
            "frame_path": frame_path,
            "detected_at": detected_at or datetime.now(timezone.utc).isoformat()
        }
        response = supabase.table("detections").insert(data).execute()
        print(f"Detection saved: {class_name} ({confidence:.2f})")
        return response
    except Exception as e:
        print(f"Error saving detection: {e}")
        return None

def save_alert(person_id, alert_type, reason, created_at=None):
    try:
        data = {
            "person_id": person_id,
            "alert_type": alert_type,
            "reason": reason,
            "created_at": created_at or datetime.now(timezone.utc).isoformat()
        }
        response = supabase.table("alerts").insert(data).execute()
        print(f"Alert saved: {alert_type}")
        return response
    except Exception as e:
        print(f"Error saving alert: {e}")
        return None

def save_spill(video_id, frame_path, bbox, confidence, detected_at=None):
    try:
        data = {
            "video_id": video_id,
            "frame_path": frame_path,
            "bbox": bbox,
            "confidence": confidence,
            "detected_at": detected_at or datetime.now(timezone.utc).isoformat()
        }
        response = supabase.table("spills").insert(data).execute()
        print(f"Spill saved for video_id={video_id}")
        return response
    except Exception as e:
        print(f"Error saving spill: {e}")
        return None

def save_clip(person_id, alert_id, clip_path, start_frame, end_frame, created_at=None):