# chat.py
from flask import Blueprint, render_template, request, redirect, session, flash, current_app, jsonify
# from .db import get_db
import sqlite3
import os
import uuid
import logging
from .extensions import socketio
from flask_socketio import emit, join_room, leave_room

chat = Blueprint("chat", __name__)

#Dùng set để lưu ID của seeker đang chờ
WAITING_USERS = set()


# ============ TEMPORARY ONLY ============
_basedir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(_basedir)
DATABASE = os.path.join(parent_dir, "therapy.db")

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10  # chờ nếu database đang bị lock
        )
        g.db.row_factory = sqlite3.Row
    return g.db

# Đóng kết nối sau mỗi request
def close_db(e=None):
    db_conn = g.pop("db", None)
    if db_conn is not None:
        db_conn.close()

# ============ TEMPORARY ONLY ============

# -----------------------------------------------
# --- LOGIC MATCHING
# -----------------------------------------------
def find_match_for_user(seeker_id, illness, prefer_anonymous=False):
    conn = get_db()
    helper_id = None
    is_expert = 0
    # Chuỗi tag cần tìm: ví dụ: "cured_anxiety"
    tag_to_match = f"cured_{illness}" 
    # Chuỗi tìm kiếm trong SQLite: ví dụ: "%,cured_anxiety,%"
    sql_tag_pattern = f'%,{tag_to_match},%'


    if not prefer_anonymous:
        # -----------------------------------------------------------------
        # Step 1A (Ưu tiên): Tìm Cured Student có TAG MATCH CHÍNH XÁC
        # -----------------------------------------------------------------
        cured_helper_specific = conn.execute(
            """
            SELECT id FROM users
            WHERE (',' || status_tag || ',') LIKE ? 
            AND role != 'expert'
            AND (chat_opt_in=1 OR chat_opt_in='1') AND id != ?
            AND id NOT IN (SELECT helper_id FROM chat_sessions WHERE status='active')
            AND id NOT IN (SELECT seeker_id FROM chat_sessions WHERE status='active')
            ORDER BY RANDOM() LIMIT 1
            """,
            (sql_tag_pattern, seeker_id)
        ).fetchone()

        if cured_helper_specific:
            helper_id = cured_helper_specific["id"]
        
        # -----------------------------------------------------------------
        # Step 1B (Fallback): Tìm Cured Student BẤT KỂ status_tag nào
        # (Chỉ chạy nếu Step 1A không tìm thấy)
        # -----------------------------------------------------------------
        if not helper_id:
            cured_helper_broad = conn.execute(
                """
                SELECT id FROM users
                WHERE status_tag LIKE 'cured_%' AND role != 'expert' AND (chat_opt_in=1 OR chat_opt_in='1') AND id != ?
                AND id NOT IN (SELECT helper_id FROM chat_sessions WHERE status='active')
                AND id NOT IN (SELECT seeker_id FROM chat_sessions WHERE status='active')
                ORDER BY RANDOM() LIMIT 1
                """,
                (seeker_id,)
            ).fetchone()
            
            if cured_helper_broad:
                helper_id = cured_helper_broad["id"]

    # -----------------------------------------------------------------
    # Step 2: Fallback sang Expert
    # -----------------------------------------------------------------
    if not helper_id:
        expert_helper = conn.execute(
            """
            SELECT id FROM users
            WHERE role='expert' AND (chat_opt_in=1 OR chat_opt_in='1')
            AND id != ?
            AND id NOT IN (SELECT helper_id FROM chat_sessions WHERE status='active')
            AND id NOT IN (SELECT seeker_id FROM chat_sessions WHERE status='active')
            ORDER BY RANDOM() LIMIT 1
            """,
            (seeker_id,)
        ).fetchone()
        
        if expert_helper:
            helper_id = expert_helper["id"]
            is_expert = 1
            
    if not helper_id:
        return None

    # Tạo session chat
    new_session_key = str(uuid.uuid4())
    try:
        conn.execute(
            "INSERT INTO chat_sessions (session_key, seeker_id, helper_id, is_expert_fallback) VALUES (?, ?, ?, ?)",
            (new_session_key, seeker_id, helper_id, is_expert)
        )
        conn.commit()
        return {"session_key": new_session_key, "helper_id": helper_id}
    except Exception as e:
        logging.error(f"Lỗi tạo session chat: {e}")
        conn.rollback()
        return None

    # Tạo session chat
    new_session_key = str(uuid.uuid4())
    try:
        conn.execute(
            "INSERT INTO chat_sessions (session_key, seeker_id, helper_id, is_expert_fallback) VALUES (?, ?, ?, ?)",
            (new_session_key, seeker_id, helper_id, is_expert)
        )
        conn.commit()
        return {"session_key": new_session_key, "helper_id": helper_id}
    except Exception as e:
        logging.error(f"Lỗi tạo session chat: {e}")
        conn.rollback()
        return None

# -----------------------------------------------
# --- ROUTES
# -----------------------------------------------
@chat.route("/chat/waiting")
def chat_waiting():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("chat_waiting.html")

@chat.route("/chat/room/<string:session_key>")
def chat_room(session_key):
    if "user_id" not in session:
        return redirect("/login")
    
    conn = get_db()
    session_data = conn.execute(
        "SELECT * FROM chat_sessions WHERE session_key=? AND (seeker_id=? OR helper_id=?)",
        (session_key, session["user_id"], session["user_id"])
    ).fetchone()

    if not session_data or session_data['status']=='ended':
        flash("Phòng chat không tồn tại hoặc đã kết thúc.")
        return redirect("/forum")

    session['current_room_key'] = session_key

    # --- Lấy lịch sử chat từ DB ---
    chat_history = conn.execute(
        "SELECT * FROM conversation_history WHERE session_key=? ORDER BY timestamp ASC",
        (session_key,)
    ).fetchall()

    return render_template("chat_room.html", session_key=session_key, chat_history=chat_history)

# API trả về lịch sử chat (dùng khi reload page)
@chat.route("/api/get_history/<string:session_key>")
def get_history(session_key):
    conn = get_db()
    history = conn.execute(
        "SELECT * FROM conversation_history WHERE session_key=? ORDER BY timestamp ASC",
        (session_key,)
    ).fetchall()
    # Convert thành list dict
    result = []
    for msg in history:
        result.append({
            "user_id": msg["user_id"],
            "user_message": msg["user_message"],
            "system_response": msg["system_response"],
            "timestamp": msg["timestamp"]
        })
    return jsonify({"history": result})

# -----------------------------------------------
# --- SOCKETIO EVENTS
# -----------------------------------------------
@socketio.on('join')
def on_join(data):
    room_key = data['room']
    user_id = session.get("user_id")
    if not user_id: return

    conn = get_db()
    session_data = conn.execute(
        "SELECT * FROM chat_sessions WHERE session_key=? AND (seeker_id=? OR helper_id=?)",
        (room_key, user_id, user_id)
    ).fetchone()

    if session_data:
        join_room(room_key)
        emit("chat_log", {"message": f"Đã kết nối vào phòng chat. (Session: {room_key})"})
    else:
        emit("chat_log", {"message": "Lỗi xác thực phòng."})

@socketio.on('send_message')
def on_send_message(data):
    user_id = session.get("user_id")
    message_content = data.get("message", "").strip()
    room_key = data.get("room")
    if not user_id or not message_content or not room_key:
        return

    # Emit tin nhắn real-time
    emit("receive_message", {"message": message_content, "sender": "Người lạ"}, to=room_key, skip_sid=request.sid)

    # --- Chỉ lưu tin nhắn mới vào DB (tránh duplicate khi reload) ---
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO conversation_history (user_id, session_type, session_key, user_message, system_response) VALUES (?, ?, ?, ?, ?)",
            (user_id, "chat", room_key, message_content, None)
        )
        if data.get("system_response"):
            conn.execute(
                "INSERT INTO conversation_history (user_id, session_type, session_key, user_message, system_response) VALUES (?, ?, ?, ?, ?)",
                (user_id, "chatbot", room_key, None, data["system_response"])
            )
        conn.commit()
    except Exception as e:
        logging.error(f"Lỗi lưu tin nhắn: {e}")
        conn.rollback()

@socketio.on('leave_chat')
def on_leave(data):
    room_key = data['room']
    user_id = session.get("user_id")
    if not user_id: return

    conn = get_db()
    session_data = conn.execute(
        "SELECT id FROM chat_sessions WHERE session_key=? AND (seeker_id=? OR helper_id=?)",
        (room_key, user_id, user_id)
    ).fetchone()

    if session_data:
        session.pop('current_room_key', None)
        conn.execute("UPDATE chat_sessions SET status='ended' WHERE session_key=?", (room_key,))
        conn.commit()
        emit("chat_ended", {"message": "Một người dùng đã kết thúc cuộc trò chuyện."}, to=room_key)


@chat.route("/chat/toggle-opt-in", methods=["POST"])
def toggle_opt_in():
    if "user_id" not in session:
        return redirect("/login")
    conn = get_db()
    current_status = conn.execute("SELECT chat_opt_in FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if not current_status:
        return "Lỗi: Không tìm thấy user", 404
    new_status = 1 - current_status["chat_opt_in"]
    conn.execute("UPDATE users SET chat_opt_in=? WHERE id=?", (new_status, session["user_id"]))
    conn.commit()
    session["chat_opt_in"] = new_status
    return redirect("/forum")

@socketio.on('connect')
def on_connect():
    if session.get("user_id"):
        join_room(f'user_{session["user_id"]}')
        if session.get("role")=="expert":
            join_room("experts_room")

@socketio.on('disconnect')
def on_disconnect():
    if session.get("user_id"):
        user_id_room = f'user_{session["user_id"]}'
        leave_room(user_id_room)
        if session.get("role")=="expert":
            leave_room("experts_room")
        room_key = session.pop('current_room_key', None)
        if room_key:
            try:
                conn = get_db()
                conn.execute("UPDATE chat_sessions SET status='ended' WHERE session_key=?", (room_key,))
                conn.commit()
                socketio.emit("chat_ended", {"message":"Người dùng kia đã ngắt kết nối."}, to=room_key)
            except Exception as e:
                logging.error(f"Lỗi khi dọn dẹp session {room_key}: {e}")

@socketio.on('request_match')
def on_request_match(data):
    if "user_id" not in session:
        return
    illness = data.get('illness')
    seeker_id = session.get('user_id')
    seeker_room = f'user_{seeker_id}'
    prefer_anonymous = data.get('anonymous', False)  # frontend gửi lên nếu muốn chat ẩn danh
    match_result = find_match_for_user(seeker_id, illness, prefer_anonymous=prefer_anonymous)
    if match_result:
        helper_id = match_result["helper_id"]
        session_key = match_result["session_key"]
        room_url = f"/chat/room/{session_key}"
        helper_room = f'user_{helper_id}'
        # Ép helper join room
        socketio.emit("force_join_room", {"room_url": room_url}, to=helper_room)
        # Gửi về student
        socketio.emit("match_found", {"room_url": room_url}, to=seeker_room)
    else:
        socketio.emit("match_failed", {"message":"Không tìm thấy ai rảnh."}, to=seeker_room)

