import os
import json
import cv2
import time
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import io
import csv
from app.safety.processor import process_video, PROCESS_STATUS, ZONES_CONFIG

app = FastAPI(
    title="SiteGuard AI", 
    description="REST API Backend Foundation for SiteGuard AI Predictive Safety Engine"
)

# Base project root paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
VIDEOS_DIR = os.path.join(PROJECT_ROOT, "data/videos")
EVENTS_JSON_PATH = os.path.join(PROJECT_ROOT, "data/outputs/safety_events.json")

os.makedirs(VIDEOS_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"status": "SiteGuard AI backend running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/api/v1/recordings/upload")
async def upload_recording(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a construction video recording and run the safety analytics pipeline in the background.
    """
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only standard video files are supported.")
        
    file_path = os.path.join(VIDEOS_DIR, file.filename)
    try:
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save video to storage: {str(e)}")
        
    # Launch video safety analysis in the background
    background_tasks.add_task(process_video, input_video_path=file_path)
    
    return {
        "status": "processing",
        "file_name": file.filename,
        "message": "Video uploaded successfully. Safety analysis started in background.",
        "progress_url": "/api/v1/progress"
    }

@app.get("/api/v1/progress")
def get_progress():
    """
    Retrieves the current background safety analysis progress.
    """
    return PROCESS_STATUS

@app.get("/api/v1/zones")
def get_zones():
    """
    Retrieves the current spatial safety zones configuration.
    """
    return {"zones": ZONES_CONFIG}

@app.get("/api/v1/events")
def get_events():
    """
    Retrieves the compiled safety alert events log from the latest run.
    """
    if not os.path.exists(EVENTS_JSON_PATH):
        return []
        
    try:
        with open(EVENTS_JSON_PATH, "r") as f:
            events = json.load(f)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read safety events: {str(e)}")

@app.get("/api/v1/stats")
def get_stats():
    """
    Compiles key compliance and safety analytics statistics from the latest run.
    """
    if not os.path.exists(EVENTS_JSON_PATH):
        return {
            "message": "No safety analytics run has been performed yet.",
            "total_events": 0,
            "violations_count": 0,
            "unique_workers_count": 0,
            "event_type_breakdown": {},
            "severity_breakdown": {}
        }
        
    try:
        with open(EVENTS_JSON_PATH, "r") as f:
            events = json.load(f)
            
        total_events = len(events)
        violations_count = sum(1 for e in events if e["event_type"] == "PPE_VIOLATION")
        
        event_types = {}
        severities = {}
        unique_workers = set()
        
        for e in events:
            # Group event types
            t = e["event_type"]
            event_types[t] = event_types.get(t, 0) + 1
            # Group severity
            s = e["severity"]
            severities[s] = severities.get(s, 0) + 1
            # Track unique workers
            if e["worker_id"]:
                unique_workers.add(e["worker_id"])
                
        return {
            "total_events": total_events,
            "violations_count": violations_count,
            "unique_workers_count": len(unique_workers),
            "event_type_breakdown": event_types,
            "severity_breakdown": severities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process safety stats: {str(e)}")

@app.get("/api/v1/reports/export")
def export_report(severity: str = None):
    """
    Exports the safety events as a formal, formatted CSV compliance audit report.
    """
    if not os.path.exists(EVENTS_JSON_PATH):
        raise HTTPException(status_code=404, detail="No safety events found to export. Please run analysis first.")
        
    try:
        with open(EVENTS_JSON_PATH, "r") as f:
            events = json.load(f)
            
        # Optional severity filter
        if severity:
            events = [e for e in events if e["severity"].upper() == severity.upper()]
            
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write CSV Headers
        writer.writerow([
            "Event ID", "Frame", "Timestamp (s)", "Worker ID", 
            "Event Type", "Severity", "Safety Zone", "Description"
        ])
        
        # Write event rows
        for e in events:
            writer.writerow([
                e["event_id"],
                e["frame_number"],
                e["timestamp_seconds"],
                e["worker_id"] if e["worker_id"] else "N/A",
                e["event_type"],
                e["severity"],
                e["zone"],
                e["description"]
            ])
            
        output.seek(0)
        
        response = StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv"
        )
        response.headers["Content-Disposition"] = "attachment; filename=osha_compliance_report.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export safety compliance report: {str(e)}")

def frame_generator():
    """
    Yields compressed JPEG frames from the active video processor.
    """
    from app.safety import processor
    is_testing = os.getenv("TESTING") == "true"
    frame_count = 0
    while True:
        frame = processor.LATEST_FRAME
        if frame is not None:
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                frame_count += 1
        if is_testing and frame_count >= 3:
            break
        time.sleep(0.033)

@app.get("/api/v1/stream")
def stream_live_video():
    """
    Streams the live processed video analysis as a multipart MJPEG stream.
    """
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


