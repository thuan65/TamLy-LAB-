# chat.py
from flask import Blueprint, render_template, request, redirect, session, flash, current_app, jsonify
from db import get_db
import uuid
import logging
from extensions import socketio
from flask_socketio import emit, join_room, leave_room

chat = Blueprint("chat", __name__)

#Dùng set để lưu ID của seeker đang chờ
WAITING_USERS = set()

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

    seeker_id = session.get('user_id')
    seeker_room = f'user_{seeker_id}'
    illness = data.get('illness')
    
    # Chuẩn bị các biến tag
    tag_to_match = f"cured_{illness}" 
    sql_tag_pattern = f'%,{tag_to_match},%'
    
    # Kiểm tra xem user đã đang chờ chưa
    if seeker_id in WAITING_USERS:
        logging.info(f"User {seeker_id} đã đang tìm kiếm.")
        # Báo cho client biết là vẫn đang chờ (phòng trường hợp client refresh)
        emit('match_waiting', {'message': 'Vẫn đang tìm kiếm...'}, to=seeker_room)
        return

    conn = get_db()

    # Hàm helper để tạo session (bạn có thể đã có hàm này)
    def create_session(helper_id, is_expert=0):
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

    try:
        # --- LOGIC MỚI THEO KỊCH BẢN CỦA BẠN ---

        # 1. TÌM P1: Student cùng tag (Ưu tiên cao nhất)
        p1_helper = conn.execute(
            """
            SELECT id FROM users
            WHERE (',' || status_tag || ',') LIKE ? 
            AND role != 'expert' AND (chat_opt_in=1 OR chat_opt_in='1') AND id != ?
            AND id NOT IN (SELECT helper_id FROM chat_sessions WHERE status='active')
            AND id NOT IN (SELECT seeker_id FROM chat_sessions WHERE status='active')
            ORDER BY RANDOM() LIMIT 1
            """,
            (sql_tag_pattern, seeker_id)
        ).fetchone()

        if p1_helper:
            logging.info(f"MATCH P1: Tìm thấy {p1_helper['id']} cho {seeker_id}")
            session_data = create_session(p1_helper['id'], is_expert=0)
            if session_data:
                room_url = f"/chat/room/{session_data['session_key']}"
                emit("match_found", {"room_url": room_url}, to=seeker_room)
                emit("force_join_room", {"room_url": room_url}, to=f'user_{p1_helper["id"]}')
            return # KẾT THÚC

        # 2. TÌM P2: Expert (Ưu tiên nhì)
        p2_helper = conn.execute(
            """
            SELECT id FROM users
            WHERE role='expert' AND (chat_opt_in=1 OR chat_opt_in='1') AND id != ?
            AND id NOT IN (SELECT helper_id FROM chat_sessions WHERE status='active')
            AND id NOT IN (SELECT seeker_id FROM chat_sessions WHERE status='active')
            ORDER BY RANDOM() LIMIT 1
            """,
            (seeker_id,)
        ).fetchone()
        
        if p2_helper:
            logging.info(f"MATCH P2: Tìm thấy Expert {p2_helper['id']} cho {seeker_id}")
            session_data = create_session(p2_helper['id'], is_expert=1)
            if session_data:
                room_url = f"/chat/room/{session_data['session_key']}"
                emit("match_found", {"room_url": room_url}, to=seeker_room)
                emit("force_join_room", {"room_url": room_url}, to=f'user_{p2_helper["id"]}')
            return # KẾT THÚC

        # 3. TÌM P3: Student khác tag (Kịch bản CHỜ)
        p3_helper = conn.execute(
            """
            SELECT id FROM users
            WHERE status_tag LIKE 'cured_%' AND (',' || status_tag || ',') NOT LIKE ?
            AND role != 'expert' AND (chat_opt_in=1 OR chat_opt_in='1') AND id != ?
            AND id NOT IN (SELECT helper_id FROM chat_sessions WHERE status='active')
            AND id NOT IN (SELECT seeker_id FROM chat_sessions WHERE status='active')
            ORDER BY RANDOM() LIMIT 1
            """,
            (sql_tag_pattern, seeker_id)
        ).fetchone()

        if p3_helper:
            # Đây là kịch bản bạn muốn: (A: Trầm cảm, B: Lo âu)
            logging.info(f"MATCH P3 (WAIT): Tìm thấy {p3_helper['id']} (khác tag). Đưa {seeker_id} vào hàng đợi.")
            WAITING_USERS.add(seeker_id)
            emit('match_waiting', {'message': 'Đang tìm kiếm người phù hợp...'}, to=seeker_room)
            return # KẾT THÚC (nhưng user vẫn ở trạng thái isSearching=true)

        # 4. KHÔNG TÌM THẤY AI CẢ
        logging.info(f"MATCH FAILED: Không tìm thấy P1, P2, hay P3 cho {seeker_id}")
        emit('match_failed', {"message":"Rất tiếc, hiện tại không có ai rảnh."}, to=seeker_room)

    except Exception as e:
        logging.error(f"Lỗi nghiêm trọng trong on_request_match: {e}")
        emit('match_failed', {"message": f"Lỗi server: {e}"}, to=seeker_room)

@socketio.on('cancel_match')
def on_cancel_match():
    seeker_id = session.get("user_id")
    if not seeker_id:
        return
    
    if seeker_id in WAITING_USERS:
        WAITING_USERS.remove(seeker_id)
        logging.info(f"User {seeker_id} đã hủy tìm kiếm.")
    else:
        logging.warning(f"User {seeker_id} HỦY nhưng không có trong hàng đợi.")