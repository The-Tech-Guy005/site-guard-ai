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
from app.ppe.detector import PPEDetector
from app.ppe.config import PPE_CLASSES_MAP, PPE_MODEL_PATH, PPE_CONF_THRESHOLD

def draw_worker_label_pil(img: np.ndarray, text: str, x: int, y: int, bg_color: tuple) -> np.ndarray:
    """
    Draws a worker label banner including Unicode check/cross marks on the image using Pillow.
    """
    # Convert BGR to RGB for PIL
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(img_pil)
    
    # Choose standard system font supporting Unicode
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
        
    # Measure text dimensions
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        w, h = draw.textsize(text, font=font)
        
    # Draw background banner (subtle rectangular background)
    bg_color_rgb = (bg_color[2], bg_color[1], bg_color[0])
    draw.rectangle([x, y - h - 6, x + w + 8, y + 2], fill=bg_color_rgb)
    
    # Draw text (white text on dark background)
    draw.text((x + 4, y - h - 3), text, font=font, fill=(255, 255, 255))
    
    # Convert back to BGR
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


def main():
    parser = argparse.ArgumentParser(description="Test PPE Detection Layer with Worker Bounding Box Crop Association.")
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
    
    # 1. Resolve paths
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
    output_video_path = os.path.abspath(os.path.join(backend_dir, "../data/outputs/ppe_output.mp4"))
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    
    # Stage 1: Verify video file exists
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
    
    # Print startup specifications
    print("=" * 60)
    print("SiteGuard AI - PPE Detection Engine Startup Settings")
    print("=" * 60)
    print(f"[*] Input Video Path: {input_video_path}")
    print(f"[*] Video Resolution: {width}x{height} @ {fps:.2f} FPS")
    print(f"[*] Worker Tracking Model: yolo11n.pt")
    print(f"[*] PPE Detection Model: {PPE_MODEL_PATH}")
    print(f"[*] Target PPE Classes: {list(PPE_CLASSES_MAP.values())}")
    print(f"[*] Worker Conf Threshold: {args.conf}")
    print(f"[*] PPE Conf Threshold: {args.ppe_conf}")
    print("=" * 60)
    
    # Stage 2: Initialize Worker Tracker
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
        
    # Stage 3: Initialize PPE Detector (Separate Layer)
    print("[*] Initializing PPEDetector...")
    try:
        ppe_detector = PPEDetector(confidence_threshold=args.ppe_conf)
    except FileNotFoundError as e:
        print(str(e))
        cap.release()
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error: {e}")
        cap.release()
        sys.exit(1)
        
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
            
    # Metrics
    frame_idx = 0
    total_ppe_count = 0
    ppe_counters = {class_name: 0 for class_name in PPE_CLASSES_MAP.values()}
    
    print("[*] Processing frames (tracking workers & detecting PPE locally on crops)...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_idx += 1
            
            # 1. Detect and track workers (YOLO + ByteTrack)
            tracks, annotated_frame = tracker.track(
                frame, 
                confidence_threshold=args.conf, 
                persist=True,
                imgsz=1280,
                classes=[0] # Track only person class
            )
            
            # 2. Run local PPE detection on crops for each tracked worker
            for track in tracks:
                xmin, ymin, xmax, ymax = track["bbox"]
                track_id = track["track_id"]
                
                # Define crop coordinates with padding around worker bounding box
                pad = 20
                c_xmin = max(0, xmin - pad)
                c_ymin = max(0, ymin - pad)
                c_xmax = min(width, xmax + pad)
                c_ymax = min(height, ymax + pad)
                
                # Extract crop
                worker_crop = frame[c_ymin:c_ymax, c_xmin:c_xmax]
                
                # Run PPE detection strictly inside the cropped region
                local_detections = ppe_detector.detect_crop(worker_crop)
                
                has_helmet = False
                has_vest = False
                has_shoes = False
                
                # Process each local detection (accumulate stats only, do NOT draw individual boxes on the frame)
                for det in local_detections:
                    class_name = det["class_name"]
                    total_ppe_count += 1
                    ppe_counters[class_name] += 1
                    
                    # Check safety gear status
                    if class_name == "helmet":
                        has_helmet = True
                    elif class_name == "safety_vest":
                        has_vest = True
                    elif class_name == "safety_shoes":
                        has_shoes = True
                
                # 3. Construct Unicode label representing current worker's compliance in compact format
                helmet_status = "✓" if has_helmet else "✗"
                vest_status = "✓" if has_vest else "✗"
                shoes_status = "✓" if has_shoes else "✗"
                
                label = f"Worker#{track_id:02d} | H:{helmet_status} V:{vest_status} S:{shoes_status}"
                
                # Subtle dark gray/black background for the worker text tag
                bg_color = (40, 40, 40)
                
                # Render label text utilizing Pillow
                text_ymin = max(ymin, 15)
                annotated_frame = draw_worker_label_pil(annotated_frame, label, xmin, text_ymin, bg_color)
                
            # Write processed frame to output file
            out.write(annotated_frame)
            
            # Log progress
            if frame_idx % 30 == 0 or frame_idx == total_frames:
                pct = (frame_idx / total_frames) * 100 if total_frames > 0 else 0.0
                active_workers = len(tracks)
                print(f"  Processed {frame_idx}/{total_frames} frames ({pct:.1f}%) | Active Workers: {active_workers} | Total PPE Detections: {total_ppe_count}")
                
    except KeyboardInterrupt:
        print("\n[!] Processing interrupted by user.")
    finally:
        cap.release()
        out.release()
        
    # Stage 4: Wrap up and Summary
    print("\n[*] Stage 4: Finalizing...")
    print("=" * 60)
    print("SiteGuard AI - PPE Processing Summary:")
    print("=" * 60)
    
    # Verify file output
    file_exists = os.path.exists(output_video_path)
    file_size = os.path.getsize(output_video_path) if file_exists else 0
    unique_workers_count = tracker.get_unique_workers_count()
    
    print(f"  - Output Video Path: {output_video_path}")
    print(f"  - Verification Status: {'SUCCESS (File written & verified)' if file_exists and file_size > 0 else 'FAILED (File missing or empty)'}")
    print(f"  - Output File Size: {file_size / (1024 * 1024):.2f} MB")
    print(f"  - Codec: avc1 (H.264)")
    print(f"  - Total Frames Processed: {frame_idx}")
    print(f"  - Total Tracked Workers (Unique): {unique_workers_count}")
    print(f"  - Total PPE Detections: {total_ppe_count}")
    print("\n--- Cumulative PPE Detections by Class ---")
    for cls_name, count in ppe_counters.items():
        print(f"    * {cls_name}: {count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
