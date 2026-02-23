import cv2
import time
import os
import sqlite3

# --- 1. DATABASE SETUP ---
# This creates a file named 'sems_database.db' in your folder automatically
def init_db():
    conn = sqlite3.connect('sems_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            violation_type TEXT,
            snapshot_path TEXT
        )
    ''')
    conn.commit()
    return conn

# --- 2. INITIALIZE DETECTORS ---
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')

# Connect to DB and open camera
db_conn = init_db()
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# --- 3. TUNABLE PARAMETERS ---
RIGHT_SENSITIVITY_RATIO = 0.20  
LEFT_SENSITIVITY_RATIO = 0.40   
SIDE_LOOK_MIN_NEIGHBORS = 15    
TURN_DURATION = 3            
ALERT_DISPLAY_SECONDS = 5    

initial_x = None
turn_start_time = None
alert_active = False
last_alert_time = 0

print("✅ SEMS Master System Active (Camera + SQL) — Press 'Q' to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue

        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Face & Profile Detection
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        profiles = profile_cascade.detectMultiScale(gray, 1.1, SIDE_LOOK_MIN_NEIGHBORS)
        
        # Detect Left Profile
        flipped_gray = cv2.flip(gray, 1)
        profiles_left = profile_cascade.detectMultiScale(flipped_gray, 1.1, SIDE_LOOK_MIN_NEIGHBORS)

        is_looking_away = False
        current_direction = "FORWARD"

        # Logic: Spatial Movement
        if len(faces) > 0:
            (x, y, cw, ch) = faces[0]
            center_x = x + cw // 2
            if initial_x is None:
                initial_x = center_x
            
            move_x = center_x - initial_x
            
            # Dynamic limits based on face width (cw)
            if move_x > (cw * RIGHT_SENSITIVITY_RATIO):
                current_direction = "RIGHT"
                is_looking_away = True
            elif move_x < (cw * LEFT_SENSITIVITY_RATIO * -1):
                current_direction = "LEFT"
                is_looking_away = True

            cv2.rectangle(frame, (x, y), (x + cw, y + ch), (0, 255, 0), 2)
        
        # Logic: Profile Visuals
        if len(profiles) > 0 or len(profiles_left) > 0:
            is_looking_away = True
            current_direction = "SIDE LOOK"

        # --- ALERT & SQL LOGGING ---
        if is_looking_away:
            if turn_start_time is None:
                turn_start_time = time.time()
            
            elapsed = time.time() - turn_start_time
            cv2.putText(frame, f"Suspicious: {elapsed:.1f}s", (20, 110), 0, 0.7, (0, 165, 255), 2)

            if elapsed > TURN_DURATION and not alert_active:
                alert_active = True
                last_alert_time = time.time()
                
                # 1. Save Snapshot
                os.makedirs("snapshots", exist_ok=True)
                ts_filename = time.strftime("%Y%m%d_%H%M%S")
                snapshot_path = f"snapshots/alert_{ts_filename}.jpg"
                cv2.imwrite(snapshot_path, frame)
                
                # 2. Save to SQLite Database
                ts_db = time.strftime("%Y-%m-%d %H:%M:%S")
                cursor = db_conn.cursor()
                cursor.execute("INSERT INTO incidents (timestamp, violation_type, snapshot_path) VALUES (?, ?, ?)",
                               (ts_db, current_direction, snapshot_path))
                db_conn.commit()
                print(f"📁 Logged to DB & Saved: {snapshot_path}")
        else:
            turn_start_time = None

        # UI Overlay
        status_color = (0, 0, 255) if is_looking_away else (0, 255, 0)
        cv2.putText(frame, f"Status: {current_direction}", (20, 40), 0, 0.8, status_color, 2)

        if alert_active and (time.time() - last_alert_time) < ALERT_DISPLAY_SECONDS:
            cv2.rectangle(frame, (0, 0), (w, 60), (0, 0, 255), -1)
            cv2.putText(frame, "⚠️ CHEATING DETECTED", (w//4, 40), 0, 1.0, (255, 255, 255), 2)
        elif alert_active:
            alert_active = False

        cv2.imshow("SEMS Capstone - AI Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    db_conn.close()
    cap.release()
    cv2.destroyAllWindows()
    print("✅ System Shutdown. Database and Snapshots saved.")