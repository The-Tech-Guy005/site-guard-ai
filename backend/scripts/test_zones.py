import os
import sys
import argparse
import cv2
import numpy as np

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.detection.detector import YOLODetector
from app.tracking.tracker import ByteTracker
from app.zones.zone_engine import SafetyZoneEngine

# 1. Configurable polygon zone configuration (defined for 4K space 3840x2160)
# These represent sensible, non-overlapping regions corresponding to ground work areas
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

def main():
    parser = argparse.ArgumentParser(description="Test Safety Zone Engine with Multi-Object Tracking.")
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
        help="Confidence threshold for YOLO tracking"
    )
    
    args = parser.parse_args()
    
    # 2. Resolve paths
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
    output_video_path = os.path.abspath(os.path.join(backend_dir, "../data/outputs/zones_output.mp4"))
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
    
    # Print startup specifications and zone coordinates to verify fit
    print("=" * 60)
    print("SiteGuard AI - Safety Zone Engine Startup Settings")
    print("=" * 60)
    print(f"[*] Input Video Path: {input_video_path}")
    print(f"[*] Actual Video Resolution: {width}x{height}")
    print(f"[*] Original Video FPS: {fps:.2f}")
    print("[*] Configured Zones Coordinates:")
    for zone in ZONES_CONFIG:
        print(f"  - {zone['name']} ({zone['zone_type']}, Severity: {zone['severity']}): {zone['coordinates']}")
    print("=" * 60)

    # Scale zone coordinates if video resolution differs from design-time (3840x2160)
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
    
    # Initialize YOLO Tracker
    print("[*] Initializing ByteTracker...")
    try:
        tracker = ByteTracker()
    except FileNotFoundError as e:
        print(str(e))
        cap.release()
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}")
        cap.release()
        sys.exit(1)
        
    # Setup Video Writer using original resolution and a QuickTime-compatible H.264 codec (avc1)
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    if not out.isOpened():
        print("[!] Warning: avc1 codec could not be opened. Falling back to mp4v...")
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        if not out.isOpened():
            print(f"[!] Error: Could not open VideoWriter with fallback mp4v codec for saving output to: {output_video_path}")
            cap.release()
            sys.exit(1)
        
    # Initialize metric stats
    frame_idx = 0
    max_simultaneous_workers = 0
    zone_stats = {
        zone.zone_id: {
            "name": zone.name,
            "type": zone.zone_type,
            "visited_workers": set(),
            "peak": 0,
            "sum": 0
        } for zone in zone_engine.zones
    }
    zone_stats["outside"] = {
        "name": "Outside Configured Zones",
        "type": "NONE",
        "visited_workers": set(),
        "peak": 0,
        "sum": 0
    }
    
    print("[*] Processing frames (detecting zones and tracking)...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_idx += 1
            
            # 1. Draw safety zone polygons on the background frame first (with 15% opacity)
            frame = zone_engine.draw_zones(frame)
            
            # 2. Track workers in frame (using yolo11n.pt + ByteTrack)
            tracks, annotated_frame = tracker.track(
                frame, 
                confidence_threshold=args.conf, 
                persist=True,
                imgsz=1280,
                classes=[0] # Track only person class
            )
            
            current_occupants = {zone_id: 0 for zone_id in zone_stats.keys()}
            
            # 3. Assess zone membership for each worker and draw compact annotation
            for track in tracks:
                xmin, ymin, xmax, ymax = track["bbox"]
                track_id = track["track_id"]
                
                # Bottom center coordinate (representing where the worker is standing)
                bottom_center = (int((xmin + xmax) / 2), ymax)
                
                # Query zone engine
                matched_zone = zone_engine.get_zone_for_point(bottom_center)
                
                if matched_zone:
                    zone_id = matched_zone.zone_id
                    zone_name = matched_zone.name
                    zone_color = matched_zone.color
                else:
                    zone_id = "outside"
                    zone_name = "Outside Zones"
                    zone_color = (255, 255, 255) # White
                    
                # Update metrics
                zone_stats[zone_id]["visited_workers"].add(track_id)
                current_occupants[zone_id] += 1
                
                # Format worker annotation text in compact style: Worker#XX | ZONE_NAME
                label = f"Worker#{track_id:02d} | {zone_name}"
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.45  # Small compact text
                thickness = 1
                
                (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Overwrite standard tracker label banner at ymin
                text_ymin = max(ymin, h + 5)
                
                # Draw solid colored backing banner
                cv2.rectangle(annotated_frame, (xmin, text_ymin - h - 5), (xmin + w + 8, text_ymin + 3), zone_color, -1)
                # Draw compact label text (black text on colored background)
                cv2.putText(
                    annotated_frame,
                    label,
                    (xmin + 4, text_ymin - 3),
                    font,
                    font_scale,
                    (0, 0, 0),
                    thickness,
                    cv2.LINE_AA
                )
                
            # Log metrics
            total_active_workers = len(tracks)
            max_simultaneous_workers = max(max_simultaneous_workers, total_active_workers)
            for zone_id, count in current_occupants.items():
                zone_stats[zone_id]["sum"] += count
                if count > zone_stats[zone_id]["peak"]:
                    zone_stats[zone_id]["peak"] = count
            
            # Write annotated frame to output file
            out.write(annotated_frame)
            
            # Log periodic progress
            if frame_idx % 30 == 0 or frame_idx == total_frames:
                pct = (frame_idx / total_frames) * 100 if total_frames > 0 else 0.0
                print(f"  Processed {frame_idx}/{total_frames} frames ({pct:.1f}%) | Active Workers: {total_active_workers}")
                
    except KeyboardInterrupt:
        print("\n[!] Processing interrupted by user.")
    finally:
        cap.release()
        out.release()
        
    # Stage 6: Finalizing and Summary
    print("\n[*] Stage 6: Finalizing...")
    print("=" * 60)
    print("SiteGuard AI - Safety Zone Processing Summary:")
    print("=" * 60)
    
    # Verify output file exists and has non-zero size
    file_exists = os.path.exists(output_video_path)
    file_size = os.path.getsize(output_video_path) if file_exists else 0
    
    print(f"  - Output Video Path: {output_video_path}")
    print(f"  - Verification Status: {'SUCCESS (File written & verified)' if file_exists and file_size > 0 else 'FAILED (File missing or empty)'}")
    print(f"  - Output File Size: {file_size / (1024 * 1024):.2f} MB")
    print(f"  - Codec: avc1 (H.264)")
    print(f"  - Frame Resolution: {width}x{height}")
    print(f"  - Original Video FPS: {fps:.2f}")
    print(f"  - Total Frames Processed: {frame_idx}")
    print(f"  - Number of Configured Zones: {len(zone_engine.zones)}")
    print(f"  - Maximum Simultaneously Tracked Workers: {max_simultaneous_workers}")
    print("\n--- Zone Occupancy Summary ---")
    for zone_id, stats in zone_stats.items():
        avg_occupancy = stats["sum"] / frame_idx if frame_idx > 0 else 0.0
        unique_visitors = len(stats["visited_workers"])
        print(f"  * {stats['name']} [{stats['type']}]:")
        print(f"    - Unique Workers Visited: {unique_visitors}")
        print(f"    - Peak Worker Occupancy:  {stats['peak']}")
        print(f"    - Average Occupancy/Frame: {avg_occupancy:.2f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
