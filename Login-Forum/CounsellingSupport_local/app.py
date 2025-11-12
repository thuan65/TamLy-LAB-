# app.py
import eventlet
eventlet.monkey_patch()

from flask import Flask
from extensions import socketio
from history_conversation import history_bp
from chat import chat
from auth import auth
from forum import forum
from db import close_db
import os

# --- Khởi tạo Flask ---
app = Flask(__name__)
app.secret_key = "my-dev-secret-key"

# --- Teardown DB ---
app.teardown_appcontext(close_db)

# --- Đăng ký blueprint ---
app.register_blueprint(auth)
app.register_blueprint(forum)
app.register_blueprint(chat)
app.register_blueprint(history_bp)

# --- Tạo thư mục instance nếu chưa có ---
instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# --- Tạo file SQLite history nếu chưa có ---
history_db_path = os.path.join(instance_dir, "history.db")
if not os.path.exists(history_db_path):
    import sqlite3
    conn = sqlite3.connect(history_db_path)
    cursor = conn.cursor()
    # Tạo bảng conversation_history nếu chưa có
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_type TEXT,
            session_key TEXT,
            user_message TEXT,
            system_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Tạo bảng chat_sessions nếu chưa có
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_key TEXT,
            seeker_id INTEGER,
            helper_id INTEGER,
            is_expert_fallback INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# --- Khởi tạo SocketIO ---
socketio.init_app(app)

if __name__ == "__main__":
    print("Khởi chạy server với SocketIO...")
    socketio.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
