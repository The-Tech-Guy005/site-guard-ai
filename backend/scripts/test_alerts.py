import os
import sys
import argparse

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.safety.processor import process_video

def main():
    parser = argparse.ArgumentParser(description="Test SiteGuard AI Step 7 Safety Event & Alert Engine.")
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
    output_json_path = os.path.abspath(os.path.join(backend_dir, "../data/outputs/safety_events.json"))
    
    print("=" * 60)
    print("SiteGuard AI - Step 7 Safety Event & Alert Engine Startup")
    print("=" * 60)
    print(f"[*] Input Video Path: {input_video_path}")
    print(f"[*] Worker Conf Threshold: {args.conf}")
    print(f"[*] PPE Conf Threshold: {args.ppe_conf}")
    print("=" * 60)
    
    print("[*] Processing video with Safety & Alert Engine...")
    summary = process_video(
        input_video_path=input_video_path,
        worker_conf=args.conf,
        ppe_conf=args.ppe_conf,
        output_video_path=output_video_path,
        output_json_path=output_json_path
    )
    
    # Stage 7: Finalizing and Summary
    print("\n[*] Stage 7: Finalizing...")
    print("=" * 60)
    print("SiteGuard AI - Step 7 Safety Event Engine Final Summary:")
    print("=" * 60)
    
    video_exists = os.path.exists(output_video_path)
    video_size = os.path.getsize(output_video_path) if video_exists else 0
    json_exists = os.path.exists(output_json_path)
    json_size = os.path.getsize(output_json_path) if json_exists else 0
    
    print(f"  - Output Video Path: {output_video_path}")
    print(f"  - Video Verification: {'SUCCESS' if video_exists and video_size > 0 else 'FAILED'}")
    print(f"  - Video File Size: {video_size / (1024 * 1024):.2f} MB")
    print(f"  - Output JSON Path: {output_json_path}")
    print(f"  - JSON Verification: {'SUCCESS' if json_exists and json_size > 0 else 'FAILED'}")
    print(f"  - JSON File Size: {json_size:.2f} Bytes")
    print(f"  - Codec: avc1 (H.264)")
    print(f"  - Total Frames Processed: {summary['total_frames']}")
    print(f"  - Total Unique Workers Tracked: {summary['unique_workers']}")
    print(f"  - Peak Site Risk Level Observed: {summary['peak_risk']}%")
    print(f"  - Cumulative Safety Violations Count: {summary['cumulative_violations']}")
    print(f"  - Total Safety Events Triggered: {summary['total_events']}")
    
    print("\n--- Event Types Summary ---")
    for evt_type, count in summary["event_types"].items():
        print(f"    * {evt_type}: {count}")
        
    print("\n--- Severity Breakdown ---")
    for sev, count in summary["severity_breakdown"].items():
        print(f"    * {sev}: {count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
