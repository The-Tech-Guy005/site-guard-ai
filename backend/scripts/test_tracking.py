import os
import sys
import argparse
import cv2

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.detection.detector import YOLODetector
from app.tracking.tracker import ByteTracker

def main():
    parser = argparse.ArgumentParser(description="Test ByteTrack multi-object tracking on construction video.")
    parser.add_argument(
        "--video",
        type=str,
        default="",
        help="Path to the input video file (defaults to the first .mp4 found in ../data/videos/)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for YOLO tracking (default: 0.25)"
    )
    
    args = parser.parse_args()
    
    # 1. Resolve input video path
    input_video_path = args.video
    if not input_video_path:
        # Scan data/videos for mp4 files
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
    output_video_path = os.path.abspath(os.path.join(backend_dir, "../data/outputs/tracked_output.mp4"))
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
    
    print("=" * 60)
    print("SiteGuard AI - ByteTrack Multi-Object Tracking Test")
    print("=" * 60)
    print("Startup Settings:")
    print(f"  - Model: yolo11n.pt")
    print(f"  - Tracker: ByteTrack (bytetrack.yaml)")
    print(f"  - Inference Resolution (imgsz): 1280")
    print(f"  - Confidence Threshold: {args.conf}")
    print(f"  - Target Class: ['person'] (COCO Class ID 0)")
    print(f"  - Input Video: {input_video_path}")
    print(f"  - Output Video: {output_video_path}")
    print("=" * 60)
    
    # Stage 1: Verify video file
    print(f"[*] Stage 1: Checking input video: {input_video_path}")
    if not os.path.exists(input_video_path):
        print(f"[!] Error: Video file not found at: {input_video_path}")
        print("Please place the construction video in data/videos/ and re-run.")
        print("=" * 60)
        sys.exit(1)
    print("[+] Video file verified.")
    
    # Stage 2: Initialize tracker
    print("[*] Stage 2: Initializing ByteTracker...")
    try:
        tracker = ByteTracker()
    except FileNotFoundError as e:
        print(str(e))
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error initializing tracker: {e}")
        sys.exit(1)
    print("[+] Tracker initialized.")
    
    # Stage 3: Open Video Capture
    print("[*] Stage 3: Opening video streams...")
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        print(f"[!] Error: Could not open video file: {input_video_path}")
        sys.exit(1)
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"[+] Input Video Specs: {width}x{height} @ {fps:.2f} FPS | Total Frames: {total_frames}")
    
    # Preserve original resolution and frame rate
    target_width, target_height = width, height
    print(f"[*] Preserving original resolution: {target_width}x{target_height} and FPS: {fps:.2f} for output.")
        
    # Setup Video Writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (target_width, target_height))
    if not out.isOpened():
        print(f"[!] Error: Could not open VideoWriter for saving output to: {output_video_path}")
        cap.release()
        sys.exit(1)
        
    # Stage 4: Process frames
    print("[*] Stage 4: Processing frames (tracking people)...")
    frame_idx = 0
    max_simultaneous_workers = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_idx += 1
            
            # Track ONLY the person class (ID 0) and use increased imgsz (1280) for high sensitivity
            tracks, annotated_frame = tracker.track(
                frame, 
                confidence_threshold=args.conf, 
                persist=True,
                imgsz=1280,
                classes=[0]
            )
            
            # Update metrics
            current_workers = len(tracks)
            max_simultaneous_workers = max(max_simultaneous_workers, current_workers)
            
            # Write to output file
            out.write(annotated_frame)
            
            # Print periodic progress
            if frame_idx % 30 == 0 or frame_idx == total_frames:
                pct = (frame_idx / total_frames) * 100 if total_frames > 0 else 0.0
                unique_workers = tracker.get_unique_workers_count()
                print(f"  Processed {frame_idx}/{total_frames} frames ({pct:.1f}%) | Active/Unique Workers: {current_workers}/{unique_workers}")
                
    except KeyboardInterrupt:
        print("\n[!] Processing interrupted by user.")
    finally:
        cap.release()
        out.release()
        
    # Stage 5: Wrap up
    print("\n[*] Stage 5: Finalizing...")
    unique_workers = tracker.get_unique_workers_count()
    print("=" * 60)
    print("Tracking Completed Summary:")
    print(f"  - Total frames processed: {frame_idx}")
    print(f"  - Maximum simultaneously tracked workers: {max_simultaneous_workers}")
    print(f"  - Total unique tracking IDs: {unique_workers}")
    print(f"  - Output saved to: {output_video_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
