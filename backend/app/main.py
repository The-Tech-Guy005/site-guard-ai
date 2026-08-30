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
ZONES_JSON_PATH = os.path.join(PROJECT_ROOT, "data/outputs/zones_config.json")

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ZONES_JSON_PATH), exist_ok=True)

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
    # Try to load from persistent storage first
    if os.path.exists(ZONES_JSON_PATH):
        try:
            with open(ZONES_JSON_PATH, "r") as f:
                zones_data = json.load(f)
                return {"zones": zones_data.get("zones", [])}
        except Exception as e:
            print(f"Error loading zones from file: {e}")
    
    # Fallback to default zones from processor
    return {"zones": ZONES_CONFIG}

@app.post("/api/v1/zones")
def create_zone(zone_data: dict):
    """
    Creates a new safety zone.
    """
    # Load existing zones
    existing_zones = ZONES_CONFIG
    if os.path.exists(ZONES_JSON_PATH):
        try:
            with open(ZONES_JSON_PATH, "r") as f:
                data = json.load(f)
                existing_zones = data.get("zones", ZONES_CONFIG)
        except Exception as e:
            print(f"Error loading zones: {e}")
    
    # Validate required fields
    required_fields = ["zone_id", "name", "zone_type", "coordinates"]
    for field in required_fields:
        if field not in zone_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Check for duplicate zone_id
    if any(z["zone_id"] == zone_data["zone_id"] for z in existing_zones):
        raise HTTPException(status_code=400, detail=f"Zone with ID '{zone_data['zone_id']}' already exists")
    
    # Add new zone
    new_zone = {
        "zone_id": zone_data["zone_id"],
        "name": zone_data["name"],
        "zone_type": zone_data["zone_type"],
        "coordinates": zone_data["coordinates"],
        "severity": zone_data.get("severity", "LOW"),
        "enabled": zone_data.get("enabled", True)
    }
    existing_zones.append(new_zone)
    
    # Save to persistent storage
    try:
        with open(ZONES_JSON_PATH, "w") as f:
            json.dump({"zones": existing_zones}, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save zone configuration: {str(e)}")
    
    return {"zone": new_zone, "message": "Zone created successfully"}

@app.put("/api/v1/zones/{zone_id}")
def update_zone(zone_id: str, zone_data: dict):
    """
    Updates an existing safety zone.
    """
    # Load existing zones
    existing_zones = ZONES_CONFIG
    if os.path.exists(ZONES_JSON_PATH):
        try:
            with open(ZONES_JSON_PATH, "r") as f:
                data = json.load(f)
                existing_zones = data.get("zones", ZONES_CONFIG)
        except Exception as e:
            print(f"Error loading zones: {e}")
    
    # Find and update zone
    zone_found = False
    for zone in existing_zones:
        if zone["zone_id"] == zone_id:
            zone.update({
                "name": zone_data.get("name", zone["name"]),
                "zone_type": zone_data.get("zone_type", zone["zone_type"]),
                "coordinates": zone_data.get("coordinates", zone["coordinates"]),
                "severity": zone_data.get("severity", zone.get("severity", "LOW")),
                "enabled": zone_data.get("enabled", zone.get("enabled", True))
            })
            zone_found = True
            break
    
    if not zone_found:
        raise HTTPException(status_code=404, detail=f"Zone with ID '{zone_id}' not found")
    
    # Save to persistent storage
    try:
        with open(ZONES_JSON_PATH, "w") as f:
            json.dump({"zones": existing_zones}, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save zone configuration: {str(e)}")
    
    return {"zone": zone, "message": "Zone updated successfully"}

@app.delete("/api/v1/zones/{zone_id}")
def delete_zone(zone_id: str):
    """
    Deletes a safety zone.
    """
    # Load existing zones
    existing_zones = ZONES_CONFIG
    if os.path.exists(ZONES_JSON_PATH):
        try:
            with open(ZONES_JSON_PATH, "r") as f:
                data = json.load(f)
                existing_zones = data.get("zones", ZONES_CONFIG)
        except Exception as e:
            print(f"Error loading zones: {e}")
    
    # Find and remove zone
    zone_found = False
    updated_zones = []
    for zone in existing_zones:
        if zone["zone_id"] == zone_id:
            zone_found = True
        else:
            updated_zones.append(zone)
    
    if not zone_found:
        raise HTTPException(status_code=404, detail=f"Zone with ID '{zone_id}' not found")
    
    # Save to persistent storage
    try:
        with open(ZONES_JSON_PATH, "w") as f:
            json.dump({"zones": updated_zones}, f, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save zone configuration: {str(e)}")
    
    return {"message": f"Zone '{zone_id}' deleted successfully"}

@app.get("/api/v1/zone-membership")
def get_zone_membership():
    """
    Returns current detections with their zone membership information.
    """
    from app.safety.processor import PROCESS_STATUS, CURRENT_DETECTIONS, LATEST_FRAME
    from app.zones.zone_engine import SafetyZoneEngine
    
    # Load current zones
    zones_config = ZONES_CONFIG
    if os.path.exists(ZONES_JSON_PATH):
        try:
            with open(ZONES_JSON_PATH, "r") as f:
                data = json.load(f)
                zones_config = data.get("zones", ZONES_CONFIG)
        except Exception as e:
            print(f"Error loading zones: {e}")
    
    # Create zone engine (will be scaled if processing is active)
    zone_engine = SafetyZoneEngine(zones_config)
    
    # If processing is active, use scaled zones
    if PROCESS_STATUS.get("status") == "processing" and LATEST_FRAME is not None:
        width = LATEST_FRAME.shape[1]
        height = LATEST_FRAME.shape[0]
        scale_x = width / 3840.0
        scale_y = height / 2160.0
        
        scaled_zones = []
        for zone_cfg in zones_config:
            scaled_coords = [[int(pt[0] * scale_x), int(pt[1] * scale_y)] for pt in zone_cfg["coordinates"]]
            scaled_cfg = zone_cfg.copy()
            scaled_cfg["coordinates"] = scaled_coords
            scaled_zones.append(scaled_cfg)
        zone_engine = SafetyZoneEngine(scaled_zones)
    
    # Calculate zone membership for current detections
    membership_data = []
    for track in CURRENT_DETECTIONS:
        # Calculate center point of bounding box
        bbox = track["bbox"]
        center_x = (bbox[0] + bbox[2]) / 2
        center_y = (bbox[1] + bbox[3]) / 2
        
        # Find zone for this point
        zone = zone_engine.get_zone_for_point((center_x, center_y))
        
        object_data = {
            "id": f"Worker#{track['track_id']:02d}" if track['class_name'] == 'person' else f"{track['class_name'].capitalize()}#{track['track_id']:02d}",
            "class": track['class_name'],
            "track_id": track['track_id'],
            "bbox": track['bbox'],
            "center": {"x": center_x, "y": center_y},
            "zone": zone.name if zone else None,
            "zone_type": zone.zone_type if zone else None,
            "zone_severity": zone.severity if zone else None
        }
        membership_data.append(object_data)
    
    return {
        "frame_number": PROCESS_STATUS.get("current_frame", 0),
        "status": PROCESS_STATUS.get("status", "idle"),
        "objects": membership_data
    }

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

@app.get("/api/v1/dashboard")
def get_dashboard():
    """
    Retrieves dashboard-specific metrics for the frontend.
    """
    if not os.path.exists(EVENTS_JSON_PATH):
        return {
            "site_status": "OFFLINE",
            "overall_risk_score": 0,
            "active_alerts": 0,
            "active_hazards": 0,
            "recent_events": []
        }
        
    try:
        with open(EVENTS_JSON_PATH, "r") as f:
            events = json.load(f)
            
        # Calculate metrics
        active_alerts = sum(1 for e in events if e["severity"] in ["CRITICAL", "HIGH"])
        active_hazards = sum(1 for e in events if e["event_type"] in ["HAZARD_DETECTION", "ZONE_BREACH"])
        
        # Calculate risk score based on severity distribution
        severity_weights = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25}
        total_risk = sum(severity_weights.get(e["severity"], 0) for e in events)
        overall_risk_score = min(100, int(total_risk / max(len(events), 1))) if events else 0
        
        # Get recent events (last 5)
        recent_events = []
        for e in events[-5:][::-1]:  # Last 5 events in reverse order
            recent_events.append({
                "id": e["event_id"],
                "type": e["event_type"].replace("_", " ").title(),
                "severity": e["severity"].title(),
                "time": f"{e['timestamp_seconds']}s",
                "location": e["zone"]
            })
        
        return {
            "site_status": "LIVE" if events else "OFFLINE",
            "overall_risk_score": overall_risk_score,
            "active_alerts": active_alerts,
            "active_hazards": active_hazards,
            "recent_events": recent_events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process dashboard data: {str(e)}")

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

@app.get("/api/v1/current-detections")
def get_current_detections():
    """
    Returns the current frame's detection data for frontend overlay rendering.
    """
    from app.safety import processor
    
    if processor.LATEST_FRAME is None:
        return {
            "frame_number": processor.PROCESS_STATUS.get("current_frame", 0),
            "total_frames": processor.PROCESS_STATUS.get("total_frames", 0),
            "progress": processor.PROCESS_STATUS.get("progress", 0.0),
            "status": processor.PROCESS_STATUS.get("status", "idle"),
            "error": processor.PROCESS_STATUS.get("error"),
            "detections": [],
            "has_frame": False
        }
    
    # Format detections for frontend consumption
    formatted_detections = []
    for track in processor.CURRENT_DETECTIONS:
        formatted_detections.append({
            "id": f"Worker#{track['track_id']:02d}" if track['class_name'] == 'person' else f"{track['class_name'].capitalize()}#{track['track_id']:02d}",
            "class": track['class_name'],
            "confidence": round(track['confidence'], 2),
            "bbox": track['bbox'],
            "track_id": track['track_id']
        })
    
    return {
        "frame_number": processor.PROCESS_STATUS.get("current_frame", 0),
        "total_frames": processor.PROCESS_STATUS.get("total_frames", 0),
        "progress": processor.PROCESS_STATUS.get("progress", 0.0),
        "status": processor.PROCESS_STATUS.get("status", "idle"),
        "error": processor.PROCESS_STATUS.get("error"),
        "detections": formatted_detections,
        "has_frame": True
    }


