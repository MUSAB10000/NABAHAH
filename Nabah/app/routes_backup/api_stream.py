from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime, timezone
import cv2, os, asyncio, time
import edge_tts
from playsound import playsound
from ultralytics import YOLO
from Nabah.app.utils import save_to_db
from Nabah.app.utils.supabase_client import supabase

router = APIRouter()

MODELS_DIR = "/content/models"
VOICES_DIR = "voices"
os.makedirs(VOICES_DIR, exist_ok=True)

person_model = YOLO(os.path.join(MODELS_DIR, "yolov8n.pt"))
mask_model = YOLO(os.path.join(MODELS_DIR, "mask.pt"))
gloves_model = YOLO(os.path.join(MODELS_DIR, "gloves.pt"))
labcoat_model = YOLO(os.path.join(MODELS_DIR, "labcoat.pt"))
glasses_model = YOLO(os.path.join(MODELS_DIR, "glasses.pt"))

camera = None
is_streaming = False
current_status = "safe"


async def generate_voice_file(text):
    voice = "ar-SA-ZariyahNeural"
    timestamp = int(time.time() * 1000)
    mp3_path = os.path.join(VOICES_DIR, f"alert_{timestamp}.mp3")
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(mp3_path)
    return mp3_path

def speak(text):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    mp3_path = loop.run_until_complete(generate_voice_file(text))
    playsound(mp3_path)


def analyze_frame(frame, video_id):
    global current_status
    results = person_model(frame, verbose=False)
    unsafe_detected = False
    alert_text = ""

    for box in results[0].boxes:
        if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.6:
            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu())
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            has_mask = len(mask_model(crop, verbose=False)[0].boxes) > 0
            has_gloves = len(gloves_model(crop, verbose=False)[0].boxes) > 0
            has_labcoat = len(labcoat_model(crop, verbose=False)[0].boxes) > 0
            has_glasses = len(glasses_model(crop, verbose=False)[0].boxes) > 0

            all_ok = has_mask and has_gloves and has_labcoat and has_glasses
            status = "safe" if all_ok else "unsafe"
            color = (0, 255, 0) if all_ok else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, status.upper(), (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            save_to_db.save_person(
                video_id=video_id,
                track_id=None,
                frame_number=int(time.time() * 1000) % 100000,
                has_mask=has_mask,
                has_gloves=has_gloves,
                has_labcoat=has_labcoat,
                has_glasses=has_glasses,
                in_red_zone=False,
                status=status,
                created_at=datetime.now(timezone.utc).isoformat()
            )

            if not all_ok:
                unsafe_detected = True
                missing_ar = []
                if not has_mask: missing_ar.append("الكمامة")
                if not has_gloves: missing_ar.append("القفازات")
                if not has_labcoat: missing_ar.append("المعطف")
                if not has_glasses: missing_ar.append("النظارات")
                alert_text = f"لم يتم ارتداء {' و '.join(missing_ar)}"

    if unsafe_detected and current_status == "safe":
        print(f"Alert: {alert_text}")
        speak(alert_text)
        save_to_db.save_alert(None, "PPE Violation", alert_text)
        current_status = "unsafe"
    elif not unsafe_detected and current_status == "unsafe":
        print("Status is safe now")
        current_status = "safe"

    return frame


def generate_frames(video_id):
    global camera, is_streaming
    while is_streaming and camera.isOpened():
        ret, frame = camera.read()
        if not ret:
            break
        frame = analyze_frame(frame, video_id)
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')


@router.get("/video_feed")
async def video_feed():
    global camera, is_streaming
    try:
        if not is_streaming:
            camera = cv2.VideoCapture(1)
            if not camera.isOpened():
                return JSONResponse({"error": "Cannot access external camera"}, status_code=400)

            is_streaming = True
            print("External camera started")

            video = save_to_db.save_video(
                video_name="External Camera",
                title="Real-Time Monitoring"
            )
            video_id = video.data[0]["id"] if video and video.data else None
        else:
            video_id = None

        return StreamingResponse(
            generate_frames(video_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        print("Stream error:", e)
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/stop_feed")
async def stop_feed():
    global camera, is_streaming
    try:
        if camera and camera.isOpened():
            camera.release()
        is_streaming = False
        print("Camera stopped.")
        return JSONResponse({"message": "Camera stopped."})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
