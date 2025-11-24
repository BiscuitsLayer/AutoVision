import os
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher

DB_PATH = os.path.join(os.getcwd(), "database", "autovision.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def clean_ocr_text(text):
    return ''.join(filter(str.isalnum, text)).upper()

def get_closest_plate(ocr_text):
    ocr_clean = clean_ocr_text(ocr_text)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT plate_number FROM cars")
    plates = [row[0] for row in cur.fetchall()]
    conn.close()

    best_match = None
    best_ratio = 0
    for plate in plates:
        ratio = SequenceMatcher(None, ocr_clean, plate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = plate

    return best_match if best_ratio > 0.65 else None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE if not exists users (
        chat_id INTEGER PRIMARY KEY,
        username TEXT,
        registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE if not exists cars (
        plate_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        plate_number TEXT NOT NULL,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
    );

    CREATE TABLE if not exists detections (
        detect_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT NOT NULL,
        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        processed INTEGER DEFAULT 0,
        location TEXT DEFAULT 'unknown',
        image_path TEXT
    );
    """)
    conn.commit()
    conn.close()

def add_detection(plate_number, location="unknown", image_path=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO detections (plate_number, location, image_path, processed) VALUES (?, ?, ?, 0)",
        (plate_number, location, image_path)
    )
    print(f"[DB] Added detection for plate: {plate_number} at {location}")
    conn.commit()
    conn.close()

# def get_user_chat_ids_for_plate(plate_number):
#     plate_number=
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()
#     cur.execute("""
#         SELECT u.chat_id 
#         FROM users u
#         JOIN cars c ON u.chat_id=c.chat_id
#         WHERE c.plate_number=?
#     """, (plate_number,))
#     chat_ids = [row[0] for row in cur.fetchall()]
#     conn.close()
#     return chat_ids
def get_user_chat_ids_for_plate(plate_number):
    print(f"[DB] Raw OCR Plate Received -> {plate_number}")

    # Fuzzy match step
    matched_plate = get_closest_plate(plate_number)
    print(f"[DB] Fuzzy Matched Plate -> {matched_plate}")

    if not matched_plate:
        print("[DB] ❌ No similar plate found in database.")
        return []

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    print(f"[DB] 🔍 Searching chat IDs linked to -> {matched_plate}")

    cur.execute("""
        SELECT u.chat_id 
        FROM users u
        JOIN cars c ON u.chat_id=c.chat_id
        WHERE c.plate_number=?
    """, (matched_plate,))
    chat_ids = [row[0] for row in cur.fetchall()]
    conn.close()

    if chat_ids:
        print(f"[DB] 📬 Found Chat IDs -> {chat_ids}")
    else:
        print(f"[DB] ⚠️ No chat IDs registered for plate -> {matched_plate}")

    return chat_ids
