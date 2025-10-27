# NABAHAH (نباهة) – AI-Powered Laboratory Safety System

## 1-Overview
**NABAHAH** (Arabic: *نباهة*, meaning *alertness*) is an **AI-driven laboratory safety monitoring system** that combines **Computer Vision**, **Database Management**, and **Real-Time Analytics** to enhance safety and compliance.

It automatically detects:
- PPE compliance (lab coat, gloves, mask, goggles)
- Unauthorized entry into restricted *red zones*
- Chemical and liquid spills

All detections are logged in a **Supabase PostgreSQL database** and displayed through a **FastAPI-based web dashboard** for safety officers.

---

## 2-Key Features
✅ Real-time detection of PPE violations, spills, and red-zone breaches  
✅ Live monitoring dashboard using FastAPI + Ngrok  
✅ Voice alerts with Edge-TTS (Arabic/English)  
✅ Centralized Supabase database for detections, alerts, and clips  
✅ RAG (Retrieval-Augmented Generation) chatbot that answers safety queries  
✅ Continuous retraining and model updates using new data  
✅ Secure admin login with bcrypt-hashed passwords  

---

## 3-System Architecture

The system follows a **three-layer architecture**:

1. **Data Acquisition Layer** – Captures live video streams via OpenCV  
2. **AI Detection Layer** – Uses YOLOv8 models to analyze PPE, spills, and red-zone activity  
3. **Monitoring & Alert Layer** – Displays detections, triggers voice alerts, and logs data


---

## 4-Core Technologies

| Category | Tools / Frameworks |
|-----------|--------------------|
| Programming | Python, FastAPI, Jupyter Notebook |
| AI Models | YOLOv8, PyTorch, OpenCV, Norfair |
| Backend | Supabase (PostgreSQL), PostgREST |
| Audio | Edge-TTS, Pydub, MoviePy |
| RAG Chatbot | Databricks + Vector Database |
| Deployment | Ngrok, Google Colab |
| Visualization | Dashboard with analytics (EDA, compliance rate, violations) |

---

## 5-Database Schema

| Table | Description |
|--------|-------------|
| `users` | Admin login and authentication |
| `videos` | Uploaded video metadata |
| `persons` | Tracked individuals and PPE status |
| `detections` | Frame-level detection logs |
| `alerts` | PPE or red-zone alerts |
| `clips` | Saved annotated video clips |
| `spills` | Chemical/liquid spill records |

---

## 6-Model Performance

| Metric | Result | Description |
|---------|--------|-------------|
| **mAP** | 94 % | Mean Average Precision for detection |
| **Precision** | 93 % | Correct detections among alerts |
| **Recall** | 90 % | True positive rate |
| **Inference Speed** | 0.8 s / frame | Real-time detection capability |

---

## 7-Installation

### Clone the Repository
```bash
git clone https://github.com/MUSAB10000/NABAHAH.git
cd NABAHAH
```
## All Models  
You can find all trained models here:  
[Models](https://drive.google.com/drive/folders/1fz9O_1Ix7JBGsIG9jq2FoJDP-HpOpkzy)


