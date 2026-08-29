import os
import sys
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageDraw, ImageFont

from app.detection.detector import YOLODetector
from app.tracking.tracker import ByteTracker
from app.zones.zone_engine import SafetyZoneEngine
from app.ppe.detector import PPEDetector
from app.ppe.config import PPE_CLASSES_MAP, PPE_MODEL_PATH
from app.safety.engine import SafetyRiskEngine
from app.safety.alert_engine import SafetyAlertEngine

# 4K Coordinate Scale Safe Zone configs
ZONES_CONFIG = [
    {
        "zone_id": "rest_zone",
        "name": "REST_ZONE",
        "zone_type": "SAFE",
        "severity": "LOW",
        "coordinates": [[100, 1500], [800, 1500], [800, 2100], [100, 2100]]
    },
    {
        "zone_id": "work_zone",
        "name": "WORK_ZONE",
        "zone_type": "CAUTION",
        "severity": "CAUTION",
        "coordinates": [[1000, 1200], [2200, 1200], [2200, 2100], [1000, 2100]]
    },
    {
        "zone_id": "vehicle_zone",
        "name": "VEHICLE_ZONE",
        "zone_type": "HIGH_RISK",
        "severity": "HIGH_RISK",
        "coordinates": [[2400, 1200], [3700, 1200], [3700, 2100], [2400, 2100]]
    },
    {
        "zone_id": "critical_zone",
        "name": "CRITICAL_ZONE",
        "zone_type": "CRITICAL",
        "severity": "CRITICAL",
        "coordinates": [[1400, 750], [2800, 750], [2800, 1150], [1400, 1150]]
    }
]

# Track global process state (for API queries)
PROCESS_STATUS = {
    "status": "idle",
    "progress": 0.0,
    "current_frame": 0,
    "total_frames": 0,
    "error": None
}

LATEST_FRAME = None

def draw_worker_safety_label_pil(img: np.ndarray, text: str, x: int, y: int, bg_color: tuple) -> np.ndarray:
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    font = None
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, 13)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()
        
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        w, h = draw.textsize(text, font=font)
        
    bg_color_rgb = (bg_color[2], bg_color[1], bg_color[0])
    draw.rectangle([x, y - h - 6, x + w + 8, y + 2], fill=bg_color_rgb)
    draw.text((x + 4, y - h - 3), text, font=font, fill=(255, 255, 255))
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def draw_hud_dashboard(frame: np.ndarray, active_workers: int, violations_count: int, max_risk: int, active_alerts: list) -> np.ndarray:
    hud_x1, hud_y1 = 30, 30
    hud_x2, hud_y2 = 620, 280
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    
    cv2.rectangle(frame, (hud_x1, hud_y1), (hud_x2, hud_y2), (255, 255, 255), 2)
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    cv2.putText(frame, "SITEGUARD AI - SAFETY INTELLIGENCE HUD", (hud_x1 + 20, hud_y1 + 35), font, 0.65, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.line(frame, (hud_x1 + 20, hud_y1 + 45), (hud_x2 - 20, hud_y1 + 45), (255, 255, 255), 1)
    cv2.putText(frame, f"Active Workers: {active_workers}", (hud_x1 + 20, hud_y1 + 80), font, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    
    v_color = (0, 0, 255) if violations_count > 0 else (0, 255, 0)
    cv2.putText(frame, f"Active PPE Violations: {violations_count}", (hud_x1 + 20, hud_y1 + 115), font, 0.55, v_color, 1, cv2.LINE_AA)
    
    if max_risk < 30:
        r_color = (0, 255, 0)
    elif max_risk < 70:
        r_color = (0, 165, 255)
    else:
        r_color = (0, 0, 255)
    cv2.putText(frame, f"Current Max Risk Score: {max_risk}%", (hud_x1 + 20, hud_y1 + 150), font, 0.55, r_color, 2, cv2.LINE_AA)
    
    cv2.putText(frame, "RECENT HIGH SEVERITY ALERTS:", (hud_x1 + 20, hud_y1 + 190), font, 0.50, (0, 255, 255), 1, cv2.LINE_AA)
    
    start_y = hud_y1 + 215
    for idx, alert in enumerate(active_alerts[-2:]):
        cv2.putText(frame, f"! {alert}", (hud_x1 + 20, start_y + (idx * 25)), font, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
        
    return frame


def process_video(
    input_video_path: str, 
    worker_conf: float = 0.25, 
    ppe_conf: float = 0.25,
    output_video_path: str = None,
    output_json_path: str = None
) -> Dict[str, Any]:
    """
    Core safety intelligence analysis processing pipeline.
    """
    global PROCESS_STATUS
    PROCESS_STATUS.update({
        "status": "processing",
        "progress": 0.0,
        "current_frame": 0,
        "total_frames": 0,
        "error": None
    })
    
    # Resolve default paths if none provided (3 levels up from app/safety)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    if not output_video_path:
        output_video_path = os.path.join(base_dir, "data/outputs/safety_output.mp4")
    if not output_json_path:
        output_json_path = os.path.join(base_dir, "data/outputs/safety_events.json")
        
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    
    try:
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open input video: {input_video_path}")
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        PROCESS_STATUS["total_frames"] = total_frames
        
        # Scale coordinates
        scale_x = width / 3840.0
        scale_y = height / 2160.0
        
        scaled_zones = []
        for zone_cfg in ZONES_CONFIG:
            scaled_coords = [[int(pt[0] * scale_x), int(pt[1] * scale_y)] for pt in zone_cfg["coordinates"]]
            scaled_cfg = zone_cfg.copy()
            scaled_cfg["coordinates"] = scaled_coords
            scaled_zones.append(scaled_cfg)
            
        zone_engine = SafetyZoneEngine(scaled_zones)
        tracker = ByteTracker()
        ppe_detector = PPEDetector(confidence_threshold=ppe_conf)
        risk_engine = SafetyRiskEngine()
        alert_engine = SafetyAlertEngine(fps=fps, cooldown_seconds=5.0)
        
        # Setup Video Writer using avc1 H.264
        fourcc = cv2.VideoWriter_fourcc(*"avc1")
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        if not out.isOpened():
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
            if not out.isOpened():
                raise ValueError("Could not open VideoWriter with avc1 or mp4v fallback")
                
        frame_idx = 0
        total_violations_recorded = 0
        max_observed_risk = 0
        active_alerts_history = []
        
        risk_severity_colors = {
            "SAFE": (0, 200, 0),
            "LOW": (0, 160, 255),
            "MEDIUM": (0, 100, 255),
            "HIGH": (0, 0, 200),
            "CRITICAL": (0, 0, 255)
        }
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_idx += 1
            PROCESS_STATUS["current_frame"] = frame_idx
            PROCESS_STATUS["progress"] = round((frame_idx / total_frames) * 100, 1) if total_frames > 0 else 0.0
            
            # 1. Draw Safety Zones
            frame = zone_engine.draw_zones(frame)
            
            # 2. Track workers
            tracks, annotated_frame = tracker.track(
                frame, 
                confidence_threshold=worker_conf, 
                persist=True,
                imgsz=1280,
                classes=[0]
            )
            
            frame_violations_count = 0
            frame_max_risk = 0
            zone_occupancy = {}
            
            # 3. Assess each worker
            for track in tracks:
                xmin, ymin, xmax, ymax = track["bbox"]
                track_id = track["track_id"]
                
                bottom_center = (int((xmin + xmax) / 2), ymax)
                matched_zone = zone_engine.get_zone_for_point(bottom_center)
                zone_name = matched_zone.name if matched_zone else "Outside Zones"
                zone_type = matched_zone.zone_type if matched_zone else "NONE"
                
                if matched_zone:
                    if zone_name not in zone_occupancy:
                        zone_occupancy[zone_name] = []
                    zone_occupancy[zone_name].append(track_id)
                    
                # Crop and PPE Detection
                pad = 20
                c_xmin = max(0, xmin - pad)
                c_ymin = max(0, ymin - pad)
                c_xmax = min(width, xmax + pad)
                c_ymax = min(height, ymax + pad)
                
                worker_crop = frame[c_ymin:c_ymax, c_xmin:c_xmax]
                local_detections = ppe_detector.detect_crop(worker_crop)
                
                has_helmet = False
                has_vest = False
                has_shoes = False
                
                for det in local_detections:
                    class_name = det["class_name"]
                    if class_name == "helmet":
                        has_helmet = True
                    elif class_name == "safety_vest":
                        has_vest = True
                    elif class_name == "safety_shoes":
                        has_shoes = True
                        
                ppe_status = {
                    "helmet": has_helmet,
                    "safety_vest": has_vest,
                    "safety_shoes": has_shoes
                }
                
                # Risk calculation
                risk_score, violations, severity = risk_engine.evaluate_safety(track_id, matched_zone, ppe_status)
                
                if violations:
                    frame_violations_count += len(violations)
                    total_violations_recorded += len(violations)
                    
                frame_max_risk = max(frame_max_risk, risk_score)
                max_observed_risk = max(max_observed_risk, risk_score)
                
                # Check alerts
                worker_new_alerts = alert_engine.check_worker_alerts(
                    frame_idx=frame_idx,
                    worker_id=track_id,
                    zone_name=zone_name,
                    zone_type=zone_type,
                    ppe_status=ppe_status,
                    risk_score=risk_score,
                    severity=severity
                )
                
                for alert in worker_new_alerts:
                    if alert["severity"] in ["HIGH", "CRITICAL"]:
                        hud_msg = f"Worker#{track_id:02d}: {alert['description'].split(' in ')[0]}"
                        active_alerts_history.append(hud_msg)
                        
                # Draw label
                helmet_status = "✓" if has_helmet else "✗"
                vest_status = "✓" if has_vest else "✗"
                shoes_status = "✓" if has_shoes else "✗"
                
                label = f"Worker#{track_id:02d} | Risk: {risk_score}% ({severity}) | H:{helmet_status} V:{vest_status} S:{shoes_status}"
                bg_color = risk_severity_colors.get(severity, (40, 40, 40))
                text_ymin = max(ymin, 15)
                annotated_frame = draw_worker_safety_label_pil(annotated_frame, label, xmin, text_ymin, bg_color)
                
            # Crowd Alerts
            crowd_new_alerts = alert_engine.check_zone_crowd_alerts(
                frame_idx=frame_idx,
                zone_occupancy=zone_occupancy,
                crowd_threshold=3
            )
            for alert in crowd_new_alerts:
                if alert["severity"] in ["HIGH", "CRITICAL"]:
                    active_alerts_history.append(alert["description"])
                    
            # HUD dashboard
            annotated_frame = draw_hud_dashboard(
                annotated_frame, 
                active_workers=len(tracks), 
                violations_count=frame_violations_count, 
                max_risk=frame_max_risk, 
                active_alerts=active_alerts_history
            )
            
            global LATEST_FRAME
            LATEST_FRAME = annotated_frame.copy()
            
            out.write(annotated_frame)
            
        cap.release()
        out.release()
        
        # Save JSON events
        alert_engine.save_report(output_json_path)
        
        unique_workers = tracker.get_unique_workers_count()
        
        # Compile final stats
        event_types = {}
        severity_types = {}
        for evt in alert_engine.events:
            event_types[evt["event_type"]] = event_types.get(evt["event_type"], 0) + 1
            severity_types[evt["severity"]] = severity_types.get(evt["severity"], 0) + 1
            
        summary = {
            "total_frames": frame_idx,
            "unique_workers": unique_workers,
            "peak_risk": max_observed_risk,
            "cumulative_violations": total_violations_recorded,
            "total_events": len(alert_engine.events),
            "event_types": event_types,
            "severity_breakdown": severity_types,
            "video_path": output_video_path,
            "json_path": output_json_path
        }
        
        PROCESS_STATUS.update({
            "status": "completed",
            "progress": 100.0
        })
        
        return summary
        
    except Exception as e:
        PROCESS_STATUS.update({
            "status": "failed",
            "error": str(e)
        })
        raise e
