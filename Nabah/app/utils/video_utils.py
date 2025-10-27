from ultralytics import YOLO
import os


MODEL_FILES = {
    "person": "/content/models/best_person.pt",
    "mask": "/content/models/mask.pt",
    "gloves": "/content/models/gloves.pt",
    "labcoat": "/content/models/labcoat.pt",
    "glasses": "/content/models/glasses.pt",
    "liquid": "/content/models/liquid.pt"
}

def load_model(model_name: str):
    if model_name not in MODEL_FILES:
        raise FileNotFoundError(f" Model '{model_name}' not found in MODEL_FILES.")

    model_path = MODEL_FILES[model_name]
    if not os.path.exists(model_path):
        raise FileNotFoundError(f" Model file missing: {model_path}")

    print(f" Loading model: {model_name} from {model_path}")
    return YOLO(model_path)

def load_models_by_type(analysis_type: str):
    """
    تحميل الموديلات بناءً على نوع التحليل (ppe / spill / both)
    """
    analysis_type = analysis_type.strip().lower()
    models = {}

    if analysis_type == "ppe":
        models["person"] = load_model("person")
        models["mask"] = load_model("mask")
        models["gloves"] = load_model("gloves")
        models["labcoat"] = load_model("labcoat")
        models["glasses"] = load_model("glasses")

    elif analysis_type == "spill":
        models["liquid"] = load_model("liquid")

    elif analysis_type == "both":
        models["person"] = load_model("person")
        models["mask"] = load_model("mask")
        models["gloves"] = load_model("gloves")
        models["labcoat"] = load_model("labcoat")
        models["glasses"] = load_model("glasses")
        models["liquid"] = load_model("liquid")

    else:
        print(f" Unknown analysis type '{analysis_type}', using PPE models by default.")
        models["person"] = load_model("person")
        models["mask"] = load_model("mask")
        models["gloves"] = load_model("gloves")
        models["labcoat"] = load_model("labcoat")
        models["glasses"] = load_model("glasses")

    print(f" Loaded models for analysis type: {analysis_type}")
    return models

from datetime import datetime, timezone
from Nabah.app.utils import save_to_db
import cv2

def process_frame(frame, models, video_id, frame_number):
    """
    تحليل إطار واحد باستخدام الموديلات المحمّلة
    - models: ناتج من load_models_by_type()
    - video_id: رقم الفيديو في قاعدة البيانات
    - frame_number: رقم الإطار الحالي
    """
    try:
        
        h, w = frame.shape[:2]
        red_x1, red_y1 = int(w * 0.7), int(h * 0.7)
        red_x2, red_y2 = w, h

        
        person = models.get("person")
        mask = models.get("mask")
        gloves = models.get("gloves")
        labcoat = models.get("labcoat")
        glasses = models.get("glasses")
        liquid = models.get("liquid")

        
        if person:
            det = person(frame, verbose=False)
            for box in det[0].boxes:
                if int(box.cls[0]) == 0 and float(box.conf[0]) > 0.5:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    crop = frame[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue

                    has_mask = len(mask(crop, verbose=False)[0].boxes) > 0 if mask else False
                    has_gloves = len(gloves(crop, verbose=False)[0].boxes) > 0 if gloves else False
                    has_labcoat = len(labcoat(crop, verbose=False)[0].boxes) > 0 if labcoat else False
                    has_glasses = len(glasses(crop, verbose=False)[0].boxes) > 0 if glasses else False

                    status = "safe" if all([has_mask, has_gloves, has_labcoat, has_glasses]) else "unsafe"
                    color = (0, 255, 0) if status == "safe" else (0, 0, 255)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, status.upper(), (x1, max(15, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    in_red = (red_x1 <= cx <= red_x2) and (red_y1 <= cy <= red_y2)

                    
                    save_to_db.save_person(
                        video_id=video_id,
                        track_id=None,
                        frame_number=frame_number,
                        has_mask=has_mask,
                        has_gloves=has_gloves,
                        has_labcoat=has_labcoat,
                        has_glasses=has_glasses,
                        in_red_zone=in_red,
                        status=status,
                        created_at=datetime.now(timezone.utc).isoformat()
                    )

      
        if liquid:
            liq = liquid(frame, verbose=False)
            for box in liq[0].boxes:
                if float(box.conf[0]) > 0.6:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, "Spill", (x1, max(15, y1 - 7)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    save_to_db.save_spill(
                        video_id=video_id,
                        frame_path="processed_frame",
                        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                        confidence=float(box.conf[0]),
                        detected_at=datetime.now(timezone.utc).isoformat()
                    )

        
        cv2.rectangle(frame, (red_x1, red_y1), (red_x2, red_y2), (0, 0, 255), 2)

        return frame

    except Exception as e:
        print(" process_frame error:", e)
        return frame
