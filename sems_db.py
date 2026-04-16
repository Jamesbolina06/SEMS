import sqlite3

class Database:
    def __init__(self, db_name="sems_reports.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. Dinagdag ang camera_type sa violations table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT,
                camera_type TEXT,
                violation_type TEXT,
                date_time TEXT,
                file_path TEXT
            )
        ''')
        
        # 2. Table for Saved Cameras
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT,
                camera_type TEXT,
                camera_url TEXT
            )
        ''')

        # 3. Table for Manual Recordings (Para sa Replay System)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_name TEXT,
                camera_type TEXT,
                date_time TEXT,
                file_path TEXT
            )
        ''')
        self.conn.commit()

    # ==========================================
    # --- VIOLATION METHODS (Para sa Reports) ---
    # ==========================================
    def insert_violation(self, room, cam_type, v_type, dt, path):
        # BAGO: Tinatanggap na niya ang cam_type
        self.cursor.execute("INSERT INTO violations (room_name, camera_type, violation_type, date_time, file_path) VALUES (?, ?, ?, ?, ?)", (room, cam_type, v_type, dt, path))
        self.conn.commit()
        return self.cursor.lastrowid

    def fetch_all_violations(self):
        self.cursor.execute("SELECT * FROM violations ORDER BY id DESC")
        return self.cursor.fetchall()

    def delete_violation(self, rec_id):
        self.cursor.execute("DELETE FROM violations WHERE id=?", (rec_id,))
        self.conn.commit()

    # ==========================================
    # --- RECORDING METHODS (Para sa Replays) ---
    # ==========================================
    def insert_record(self, room, cam_type, dt, path):
        self.cursor.execute("INSERT INTO recordings (room_name, camera_type, date_time, file_path) VALUES (?, ?, ?, ?)", (room, cam_type, dt, path))
        self.conn.commit()
        return self.cursor.lastrowid

    def fetch_all(self):
        self.cursor.execute("SELECT * FROM recordings ORDER BY id DESC")
        return self.cursor.fetchall()

    def delete_record(self, rec_id):
        self.cursor.execute("DELETE FROM recordings WHERE id=?", (rec_id,))
        self.conn.commit()

    # ==========================================
    # --- CAMERA SAVING METHODS ---
    # ==========================================
    def insert_camera(self, room, cam_type, url):
        self.cursor.execute("INSERT INTO saved_cameras (room_name, camera_type, camera_url) VALUES (?, ?, ?)", (room, cam_type, url))
        self.conn.commit()
        
    def fetch_all_cameras(self):
        self.cursor.execute("SELECT room_name, camera_type, camera_url FROM saved_cameras")
        return self.cursor.fetchall()
        
    def delete_camera_by_name(self, room_name):
        self.cursor.execute("DELETE FROM saved_cameras WHERE room_name=?", (room_name,))
        self.conn.commit()

    def close(self):
        self.conn.close()