import os
import sys
import argparse
import cv2

# Add the backend directory to sys.path to allow imports from app
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.detection.detector import YOLODetector

def main():
    parser = argparse.ArgumentParser(description="Test YOLO object detection on a sample image.")
    parser.add_argument(
        "--image", 
        type=str, 
        default="../data/videos/construction site image.jpg",
        help="Path to the input sample image (default: ../data/videos/construction site image.jpg)"
    )
    parser.add_argument(
        "--conf", 
        type=float, 
        default=0.25,
        help="Confidence threshold for detection (default: 0.25)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to current working directory
    input_path = os.path.abspath(args.image)
    output_path = os.path.abspath("../data/outputs/annotated.jpg")
    output_dir = os.path.dirname(output_path)
    
    print("=" * 60)
    print("SiteGuard AI - YOLO Object Detection Test")
    print("=" * 60)
    
    # Stage 1: Verify sample image exists
    print(f"[*] Stage 1: Verifying input image at: {input_path}")
    if not os.path.exists(input_path):
        print(f"[!] Error: Input image not found at: {input_path}")
        print("\nTo run the detection test, please place the input image at:")
        print(f"  {input_path}")
        print("\nOr specify a custom path using:")
        print("  python scripts/test_detection.py --image /path/to/your/image.jpg")
        print("=" * 60)
        sys.exit(1)
    print(f"[+] Input image verified.")

    # Stage 2: Load Input Image
    print(f"[*] Stage 2: Loading input image...")
    frame = cv2.imread(input_path)
    if frame is None:
        print(f"[!] Error: Could not read image at {input_path}. Make sure it is a valid image file.")
        sys.exit(1)
    print(f"[+] Image loaded successfully (dimensions: {frame.shape[1]}x{frame.shape[0]}).")
        
    # Stage 3: Initializing YOLO Detector
    print("[*] Stage 3: Initializing YOLO Detector...")
    try:
        detector = YOLODetector()
    except FileNotFoundError as e:
        print(str(e))
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Error loading YOLO model: {e}")
        sys.exit(1)
    
    # Stage 4: Running object detection
    print("[*] Stage 4: Running object detection...")
    detections, annotated_frame = detector.detect(frame, confidence_threshold=args.conf)
    
    print("\n--- Detection Results ---")
    if not detections:
        print("No target objects (person, car, truck, motorcycle, bus) detected.")
    else:
        for idx, det in enumerate(detections, 1):
            bbox = det['bbox']
            print(f"{idx}. Class: {det['class_name']} | Conf: {det['confidence']:.2f} | Bbox: {bbox}")
            
    # Stage 5: Save Output Image
    print(f"\n[*] Stage 5: Saving annotated result...")
    # Ensure outputs directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    success = cv2.imwrite(output_path, annotated_frame)
    if success:
        print(f"[+] Output successfully saved to: {output_path}")
    else:
        print(f"[!] Error: Failed to write output image to: {output_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()

