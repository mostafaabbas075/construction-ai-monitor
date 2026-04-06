import cv2
import json
import math
import time
import datetime
from ultralytics import YOLO
from kafka import KafkaProducer

# ==========================================
# 1. Configuration & Paths
# ==========================================
MODEL_PATH = "best.pt"  
VIDEO_PATH = "test_video.mp4" 
OUTPUT_PATH = "demo_output.avi"
JSON_OUTPUT = "output_data.json" 

# Optimization: Process 1 frame, skip the next 2 frames
SKIP_FRAMES = 3  

EQUIPMENT_ID = "EX-001"
EQUIPMENT_CLASS = "excavator"

# ==========================================
# 2. Kafka Producer Setup
# ==========================================
try:
    producer = KafkaProducer(
        bootstrap_servers=['kafka:29092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("[INFO] 🟢 Connected to Kafka Successfully!")
except Exception as e:
    print(f"[WARNING] 🔴 Kafka not reachable. Running Offline Mode.")
    producer = None

# ==========================================
# 3. Model Loading
# ==========================================
print("[INFO] 🚀 Loading YOLO Model...")
model = YOLO(MODEL_PATH)

def format_timestamp(seconds):
    """Converts seconds to HH:MM:SS.mmm format"""
    td = datetime.timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    milliseconds = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"

def process_video():
    cap = cv2.VideoCapture(VIDEO_PATH)
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(OUTPUT_PATH, fourcc, fps, (width, height))
    
    frame_count = 0
    active_frames_total = 0
    idle_frames_total = 0
    
    last_annotated_frame = None
    all_payloads = []
    prev_bucket_center = None

    print(f"[INFO] 🎬 Processing Video on CPU (Analyzing 1 every {SKIP_FRAMES} frames)...")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: 
            break
        
        frame_count += 1
        
        # --- CPU Optimization Logic ---
        if frame_count % SKIP_FRAMES == 1:
            results = model.track(frame, persist=True, imgsz=640, conf=0.25, verbose=False)
            res = results[0]
            
            bucket_box = None
            truck_box = None
            boom_box = None
            
            # Extract Bounding Boxes
            if res.boxes:
                for box in res.boxes:
                    cls_id = int(box.cls[0])
                    label = model.names[cls_id]
                    coords = box.xyxy[0].tolist() 
                    
                    if label == 'bucket': bucket_box = coords
                    elif label == 'dumptruck': truck_box = coords
                    elif label == 'boom': boom_box = coords

            # --- Business Logic: Activity Recognition ---
            current_activity = "WAITING"
            current_state = "INACTIVE"
            motion_source = "none"
            color = (0, 255, 255) # Yellow
            
            if bucket_box and truck_box:
                # 1. Dumping Logic: Intersection (IoU)
                if max(bucket_box[0], truck_box[0]) < min(bucket_box[2], truck_box[2]) and max(bucket_box[1], truck_box[1]) < min(bucket_box[3], truck_box[3]):
                    current_activity = "DUMPING"
                    current_state = "ACTIVE"
                    motion_source = "arm_and_bucket"
                    color = (0, 0, 255) # Red
                    
            elif bucket_box and boom_box:
                # 2. Digging Logic: Vertical distance
                dist_y = bucket_box[3] - boom_box[3] 
                if dist_y > 50:
                    current_activity = "DIGGING"
                    current_state = "ACTIVE"
                    motion_source = "arm_only" 
                    color = (0, 255, 0) # Green
                else:
                    # 3. Swinging Logic: Horizontal movement check
                    current_bucket_center = ((bucket_box[0]+bucket_box[2])/2, (bucket_box[1]+bucket_box[3])/2)
                    if prev_bucket_center:
                        movement = math.hypot(current_bucket_center[0] - prev_bucket_center[0], current_bucket_center[1] - prev_bucket_center[1])
                        if movement > 10:
                            current_activity = "SWINGING"
                            current_state = "ACTIVE"
                            motion_source = "body_swing"
                            color = (255, 165, 0) # Orange
                    prev_bucket_center = current_bucket_center

            # --- Time Analytics Calculation ---
            if current_state == "ACTIVE":
                active_frames_total += SKIP_FRAMES
            else:
                idle_frames_total += SKIP_FRAMES
                
            total_tracked_seconds = round(frame_count / fps, 2)
            total_active_seconds = round(active_frames_total / fps, 2)
            total_idle_seconds = round(idle_frames_total / fps, 2)
            
            utilization_percent = round((total_active_seconds / total_tracked_seconds) * 100, 1) if total_tracked_seconds > 0 else 0.0

            # --- Final JSON Payload Format ---
            payload = {
                "frame_id": frame_count,
                "equipment_id": EQUIPMENT_ID,
                "equipment_class": EQUIPMENT_CLASS,
                "timestamp": format_timestamp(total_tracked_seconds),
                "utilization": {
                    "current_state": current_state,
                    "current_activity": current_activity,
                    "motion_source": motion_source
                },
                "time_analytics": {
                    "total_tracked_seconds": total_tracked_seconds,
                    "total_active_seconds": total_active_seconds,
                    "total_idle_seconds": total_idle_seconds,
                    "utilization_percent": utilization_percent
                }
            }
            all_payloads.append(payload)
            
            # Send payload to Kafka
            if producer:
                producer.send('excavator_activity', value=payload)
            
            # Generate the frame with YOLO bounding boxes
            last_annotated_frame = res.plot(line_width=2, font_size=1)
            
        else:
            if last_annotated_frame is None:
                last_annotated_frame = frame
        
        # --- Display, Save, and Live Feed Injection ---
        display_frame = last_annotated_frame.copy()
        
        # Display State, Activity, and Utilization % on the frame
        cv2.putText(display_frame, f"{current_state} | {current_activity} | Util: {utilization_percent}%", 
                    (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)
        
        # Write to video file
        out.write(display_frame)
        
        # Write to an image file for the Streamlit Live Feed
        cv2.imwrite("latest_frame.jpg", display_frame)
        
        if frame_count % 30 == 0:
            print(f"[LIVE] Frame: {frame_count} | {current_state} - {current_activity} | Utilization: {utilization_percent}%")

    cap.release()
    out.release()
    
    # Save the exact JSON format required
    with open(JSON_OUTPUT, "w") as f:
        json.dump(all_payloads, f, indent=4)
        
    print(f"\n[SUCCESS] 🎉 Video saved to {OUTPUT_PATH}")
    print(f"[SUCCESS] 💾 Payload JSON saved to {JSON_OUTPUT}")

if __name__ == "__main__":
    process_video()