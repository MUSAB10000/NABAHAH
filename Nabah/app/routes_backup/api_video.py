from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime, timezone
import cv2, os, tempfile
from Nabah.app.utils import save_to_db, video_utils
from Nabah.app.utils.supabase_client import supabase

router = APIRouter()

@router.post("/api/analyze-video")
async def analyze_video(file: UploadFile = File(...), title: str = Form("Analyzed Video"), analysis_type: str = Form("ppe")):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(await file.read())
            src = tmp.name

        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            return JSONResponse({"error": "Cannot open video"}, status_code=400)

        fps = max(1, int(cap.get(cv2.CAP_PROP_FPS)))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        os.makedirs("/content/outputs", exist_ok=True)
        out_path = f"/content/outputs/annotated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        out = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

        models = video_utils.load_models_by_type(analysis_type)

        video_id = None
        try:
            res = supabase.table("videos").insert({
                "title": title,
                "video_name": os.path.basename(src),
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            video_id = res.data[0]["id"] if res.data else None
        except Exception as e:
            print("Cannot insert video:", e)

        frame_i = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_i += 1
            frame = video_utils.process_frame(frame, models, video_id, frame_i)
            out.write(frame)

        cap.release()
        out.release()

        return JSONResponse({
            "status": "success",
            "video_id": video_id,
            "analysis_type": analysis_type,
            "download_url": f"/download/{os.path.basename(out_path)}"
        })
    except Exception as e:
        print("analyze_video error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/download/{filename}")
async def download_file(filename: str):
    path = f"/content/outputs/{filename}"
    if os.path.exists(path):
        return FileResponse(
            path,
            media_type="application/octet-stream",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    return JSONResponse({"error": "File not found"}, status_code=404)
