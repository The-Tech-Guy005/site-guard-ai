import os
import sys
import argparse
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.detection.detector import YOLODetector
from app.tracking.tracker import ByteTracker
from app.zones.zone_engine import SafetyZoneEngine
from app.ppe.detector import PPEDetector
from app.ppe.config import PPE_CLASSES_MAP, PPE_MODEL_PATH
from app.safety.engine import SafetyRiskEngine

# Configurable polygon zone configuration (defined for 4K space 3840x2160)
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

def draw_worker_safety_label_pil(img: np.ndarray, text: str, x: int, y: int, bg_color: tuple) -> np.ndarray:
    """
    Draws the worker ID and PPE/Risk status banner (including unicode checkmarks/crossmarks) using Pillow.
    """
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
        
    # Draw solid background banner
    bg_color_rgb = (bg_color[2], bg_color[1], bg_color[0])
    draw.rectangle([x, y - h - 6, x + w + 8, y + 2], fill=bg_color_rgb)
    # Draw text (white text on filled banner)
    draw.text((x + 4, y - h - 3), text, font=font, fill=(255, 255, 255))
    
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def draw_hud_dashboard(frame: np.ndarray, active_workers: int, violations_count: int, max_risk: int, active_alerts: list) -> np.ndarray:
    """
    Draws a translucent real-time Safety Analytics HUD Dashboard in the top-left corner.
    """
    # 1. Overlay translucent black box
    hud_x1, hud_y1 = 30, 30
    hud_x2, hud_y2 = 620, 280
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (hud_x1, hud_y1), (hud_x2, hud_y2), (0, 0, 0), -1)
    # Blend with original frame (55% opacity for HUD background)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    
    # Draw border outline around HUD
    cv2.rectangle(frame, (hud_x1, hud_y1), (hud_x2, hud_y2), (255, 255, 255), 2)
    
    # 2. Render Text Stats
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # Title
    cv2.putText(frame, "SITEGUARD AI - SAFETY INTELLIGENCE HUD", (hud_x1 + 20, hud_y1 + 35), font, 0.65, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.line(frame, (hud_x1 + 20, hud_y1 + 45), (hud_x2 - 20, hud_y1 + 45), (255, 255, 255), 1)
    
    # Metrics
    cv2.putText(frame, f"Active Workers: {active_workers}", (hud_x1 + 20, hud_y1 + 80), font, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Violations (red if > 0)
    v_color = (0, 0, 255) if violations_count > 0 else (0, 255, 0)
    cv2.putText(frame, f"Active PPE Violations: {violations_count}", (hud_x1 + 20, hud_y1 + 115), font, 0.55, v_color, 1, cv2.LINE_AA)
    
    # Peak Risk (Red/Orange/Green)
    if max_risk < 30:
        r_color = (0, 255, 0)
    elif max_risk < 70:
        r_color = (0, 165, 255)
    else:
        r_color = (0, 0, 255)
    cv2.putText(frame, f"Current Max Risk Score: {max_risk}%", (hud_x1 + 20, hud_y1 + 150), font, 0.55, r_color, 2, cv2.LINE_AA)
    
    # Active Alerts Section
    cv2.putText(frame, "RECENT HIGH SEVERITY ALERTS:", (hud_x1 + 20, hud_y1 + 190), font, 0.50, (0, 255, 255), 1, cv2.LINE_AA)
    
    start_y = hud_y1 + 215
    for idx, alert in enumerate(active_alerts[-2:]): # Show last 2 alerts
        cv2.putText(frame, f"! {alert}", (hud_x1 + 20, start_y + (idx * 25)), font, 0.45, (0, 0, 255), 1, cv2.LINE_AA)
        
    return frame


def main():
    parser = argparse.ArgumentParser(description="Test SiteGuard AI Step 6 Risk & Alert Engine.")
    parser.add_argument(
        "--video",
        type=str,
        default="",
        help="Path to the input video file"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for worker tracking (default: 0.25)"
    )
    parser.add_argument(
        "--ppe_conf",
        type=float,
        default=0.25,
        help="Confidence threshold for PPE detection (default: 0.25)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    input_video_path = args.video
    if not input_video_path:
        video_dir = os.path.abspath(os.path.join(backend_dir, "../data/videos"))
        if os.path.exists(video_dir):
            mp4_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4") and not f.startswith(".")]
            if mp4_files:
                input_video_path = os.path.join(video_dir, mp4_files[0])
            else:
                input_video_path = os.path.join(video_dir, "14495427_3840_2160_30fps.mp4")
        else:
            input_video_path = "../data/videos/14495427_3840_2160_30fps.mp4"
            
    input_video_path = os.path.abspath(input_video_path)
    output_video_path = os.path.abspath(os.path.join(backend_dir, "../data/outputs/safety_output.mp4"))
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    
    # Stage 1: Verify video file
    if not os.path.exists(input_video_path):
        print(f"[!] Error: Video file not found at: {input_video_path}")
        sys.exit(1)
        
    # Open Video Capture
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"[!] Error: Could not open video file: {input_video_path}")
        sys.exit(1)
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Scale safety zones coordinates dynamically
    scale_x = width / 3840.0
    scale_y = height / 2160.0
    
    scaled_zones_config = []
    for zone_cfg in ZONES_CONFIG:
        scaled_coords = []
        for pt in zone_cfg["coordinates"]:
            scaled_coords.append([int(pt[0] * scale_x), int(pt[1] * scale_y)])
        
        scaled_cfg = zone_cfg.copy()
        scaled_cfg["coordinates"] = scaled_coords
        scaled_zones_config.append(scaled_cfg)
        
    zone_engine = SafetyZoneEngine(scaled_zones_config)
    
    # Print startup specifications
    print("=" * 60)
    print("SiteGuard AI - Step 6 Safety & Risk Engine Startup")
    print("=" * 60)
    print(f"[*] Input Video Path: {input_video_path}")
    print(f"[*] Video Resolution: {width}x{height} @ {fps:.2f} FPS")
    print(f"[*] Worker Bounding Box Model: yolo11n.pt")
    print(f"[*] PPE Detection Model: {PPE_MODEL_PATH}")
    print(f"[*] Safety Zone Count: {len(zone_engine.zones)}")
    print(f"[*] Worker Conf Threshold: {args.conf}")
    print(f"[*] PPE Conf Threshold: {args.ppe_conf}")
    print("=" * 60)
    
    # Initialize components
    print("[*] Initializing tracker...")
    tracker = ByteTracker()
    
    print("[*] Initializing PPE detector...")
    ppe_detector = PPEDetector(confidence_threshold=args.ppe_conf)
    
    print("[*] Initializing Risk engine...")
    risk_engine = SafetyRiskEngine()
    
    # Setup Video Writer using avc1 H.264 codec
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    if not out.isOpened():
        print("[!] Warning: avc1 codec could not be opened. Falling back to mp4v...")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        if not out.isOpened():
            print(f"[!] Error: Could not open VideoWriter with fallback mp4v for saving output to: {output_video_path}")
            cap.release()
            sys.exit(1)
            
    # Metrics tracking variables
    frame_idx = 0
    total_violations_recorded = 0
    max_observed_risk = 0
    active_alerts_history = []
    
    # BGR Risk Colors mapping for worker labels
    risk_severity_colors = {
        "SAFE": (0, 200, 0),         # Darker Green
        "LOW": (0, 160, 255),        # Orange-Yellow
        "MEDIUM": (0, 100, 255),     # Darker Orange
        "HIGH": (0, 0, 200),         # Crimson
        "CRITICAL": (0, 0, 255)      # Pure Red
    }
    
    print("[*] Processing frames (Zones + Tracking + PPE + Risk Scoring)...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_idx += 1
            
            # 1. Draw Safety Zones on base frame (15% transparency)
            frame = zone_engine.draw_zones(frame)
            
            # 2. Track workers (YOLO + ByteTrack)
            tracks, annotated_frame = tracker.track(
                frame, 
                confidence_threshold=args.conf, 
                persist=True,
                imgsz=1280,
                classes=[0] # Person class only
            )
            
            frame_violations_count = 0
            frame_max_risk = 0
            
            # 3. For each worker, detect local PPE and assess safety risk
            for track in tracks:
                xmin, ymin, xmax, ymax = track["bbox"]
                track_id = track["track_id"]
                
                # Bounding box bottom-center point
                bottom_center = (int((xmin + xmax) / 2), ymax)
                # Query safety zone
                matched_zone = zone_engine.get_zone_for_point(bottom_center)
                zone_name = matched_zone.name if matched_zone else "Outside Zones"
                
                # Bounding box crop with padding
                pad = 20
                c_xmin = max(0, xmin - pad)
                c_ymin = max(0, ymin - pad)
                c_xmax = min(width, xmax + pad)
                c_ymax = min(height, ymax + pad)
                
                worker_crop = frame[c_ymin:c_ymax, c_xmin:c_xmax]
                
                # Detect PPE locally
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
                
                # 4. Safety Risk Engine Calculation
                risk_score, violations, severity = risk_engine.evaluate_safety(track_id, matched_zone, ppe_status)
                
                # Accumulate stats
                if violations:
                    frame_violations_count += len(violations)
                    total_violations_recorded += len(violations)
                
                frame_max_risk = max(frame_max_risk, risk_score)
                max_observed_risk = max(max_observed_risk, risk_score)
                
                # Record high/critical severity alerts
                if severity in ["HIGH", "CRITICAL"] and violations:
                    alert_msg = f"Worker#{track_id:02d} ({severity}): {violations[0]}"
                    if not active_alerts_history or active_alerts_history[-1] != alert_msg:
                        active_alerts_history.append(alert_msg)
                
                # 5. Draw Worker Bounding Box label above box
                # Format: Worker#XX | Risk: YY% (SEVERITY) | H:✓ V:✓ S:✗
                helmet_status = "✓" if has_helmet else "✗"
                vest_status = "✓" if has_vest else "✗"
                shoes_status = "✓" if has_shoes else "✗"
                
                label = f"Worker#{track_id:02d} | Risk: {risk_score}% ({severity}) | H:{helmet_status} V:{vest_status} S:{shoes_status}"
                
                # Map BGR color based on safety severity
                bg_color = risk_severity_colors.get(severity, (40, 40, 40))
                
                # Render Unicode label tag utilizing Pillow
                text_ymin = max(ymin, 15)
                annotated_frame = draw_worker_safety_label_pil(annotated_frame, label, xmin, text_ymin, bg_color)
                
            # 6. Overlay HUD safety dashboard in the top-left corner
            annotated_frame = draw_hud_dashboard(
                annotated_frame, 
                active_workers=len(tracks), 
                violations_count=frame_violations_count, 
                max_risk=frame_max_risk, 
                active_alerts=active_alerts_history
            )
            
            # Write annotated frame to video file
            out.write(annotated_frame)
            
            # Log periodic progress
            if frame_idx % 30 == 0 or frame_idx == total_frames:
                pct = (frame_idx / total_frames) * 100 if total_frames > 0 else 0.0
                print(f"  Processed {frame_idx}/{total_frames} frames ({pct:.1f}%) | Active Workers: {len(tracks)} | Max Frame Risk: {frame_max_risk}%")
                
    except KeyboardInterrupt:
        print("\n[!] Processing interrupted by user.")
    finally:
        cap.release()
        out.release()
        
    # Stage 7: Wrap up and Summary
    print("\n[*] Stage 7: Finalizing...")
    print("=" * 60)
    print("SiteGuard AI - Step 6 Safety Engine Final Summary:")
    print("=" * 60)
    
    # Verify file output
    file_exists = os.path.exists(output_video_path)
    file_size = os.path.getsize(output_video_path) if file_exists else 0
    unique_workers = tracker.get_unique_workers_count()
    
    print(f"  - Output Video Path: {output_video_path}")
    print(f"  - Verification Status: {'SUCCESS (File written & verified)' if file_exists and file_size > 0 else 'FAILED (File missing or empty)'}")
    print(f"  - Output File Size: {file_size / (1024 * 1024):.2f} MB")
    print(f"  - Codec: avc1 (H.264)")
    print(f"  - Total Frames Processed: {frame_idx}")
    print(f"  - Total Unique Workers Tracked: {unique_workers}")
    print(f"  - Cumulative Safety Violations Recorded: {total_violations_recorded}")
    print(f"  - Peak Site Risk Level Observed: {max_observed_risk}%")
    print("=" * 60)

if __name__ == "__main__":
    main()
