# app.py
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, session, redirect

# --- Import của cả hai bạn ---
from extensions import socketio
from history_conversation import history_bp
from chat import chat
from auth import auth
from forum import forum
from chat_expert import chat_expert_bp


# from chat_expert import chat # <--- Bị trùng, file chat đã import ở trên
from db import close_db, init_db, get_db 
import os


# --- Khởi tạo Flask ---
app = Flask(__name__)
app.secret_key = "my-dev-secret-key"

# --- Teardown DB (Giữ của bạn) ---
app.teardown_appcontext(close_db)

# --- Đăng ký blueprint (Gộp cả hai) ---
app.register_blueprint(auth)
app.register_blueprint(forum)
app.register_blueprint(chat)
app.register_blueprint(chat_expert_bp)
app.register_blueprint(history_bp) # <--- Giữ của bạn

# --- Tạo thư mục instance (Giữ của bạn) ---
instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance")
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

# --- Tạo file SQLite history (Giữ của bạn) ---
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

# ---- DASHBOARD (Giữ của bạn bạn) ----
@app.route("/dashboard")
def dashboard():
    """
    Chuyển hướng theo role
    """
    if "user_id" not in session:
        return redirect("/login")
    role = session.get("role")
    if role == "student":
        return redirect("/dashboard_student")
    else:
        return redirect("/dashboard_expert")


@app.route("/dashboard_student")
def dashboard_student():
    if "user_id" not in session:
        return redirect("/login")
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        user_id=session["user_id"],
    )


@app.route("/dashboard_expert")
def dashboard_expert():
    if "user_id" not in session:
        return redirect("/login")
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        user_id=session["user_id"]
    )

# --- Khởi tạo SocketIO (Giữ của bạn) ---
socketio.init_app(app)

if __name__ == "__main__":
    # --- Gộp logic của cả hai ---
    
    # Tạo DB forum.db nếu chưa có (Từ bạn của bạn)
    if not os.path.exists("forum.db"):
        init_db()
        
    # Chạy server với SocketIO (Từ bạn)
    print("Khởi chạy server với SocketIO...")
    socketio.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)