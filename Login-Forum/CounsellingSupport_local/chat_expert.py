# chat_expert.py
from flask import Blueprint, render_template, request, jsonify, session
from db import get_db
from extensions import socketio
from flask_socketio import emit, join_room
from datetime import datetime

chat_expert_bp = Blueprint("chat_expert", __name__, url_prefix="/chat_expert")

# ============================================================
# 1) Route: /expert  → Dashboard chỉ có “Vào Chat”
# ============================================================
@chat_expert_bp.route("")
def chat_dashboard():
    if "user_id" not in session:
        return "Bạn cần đăng nhập.", 403

    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        user_id=session["user_id"]
    )

# ============================================================
# 2) Route: /expert/chat  → Giao diện Messenger
# ============================================================
@chat_expert_bp.route("/chat")
def chat_page():
    if "user_id" not in session:
        return "Bạn cần đăng nhập", 403

    return render_template(
        "chat_messenger.html",
        user_id=session["user_id"],
        role=session["role"]
    )

# ============================================================
# 3) API: Lấy danh sách người từng chat + số unread + tên (dành cho expert)
# ============================================================
@chat_expert_bp.route("/api/get_peers/<int:user_id>")
def get_peers(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT DISTINCT 
            CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END AS peer
        FROM messages
        WHERE sender_id=? OR receiver_id=?
    """, (user_id, user_id, user_id)).fetchall()

    peers = []
    for r in rows:
        peer_id = r["peer"]
        u = conn.execute("SELECT username, role FROM users WHERE id=?", (peer_id,)).fetchone()
        if not u: continue
        unread = conn.execute("""
            SELECT COUNT(*) AS cnt
            FROM messages
            WHERE receiver_id=? AND sender_id=? AND is_read=0
        """, (user_id, peer_id)).fetchone()
        peers.append({
            "id": peer_id,
            "name": u["username"],
            "role": u["role"],
            "unread": unread["cnt"]
        })
    return jsonify({"peers": peers})

# ============================================================
# 4) API lấy danh sách experts + số tin chưa đọc (dành cho student)
# ============================================================
@chat_expert_bp.route("/api/get_experts_for_student/<int:uid>")
def get_experts_for_student(uid):
    conn = get_db()
    experts = conn.execute("SELECT id, username FROM users WHERE role='expert'").fetchall()
    result = []

    for e in experts:
        # Lấy số tin chưa đọc từ expert gửi student
        unread = conn.execute("""
            SELECT COUNT(*) AS cnt FROM messages
            WHERE sender_id=? AND receiver_id=? AND is_read=0
        """, (e["id"], uid)).fetchone()

        result.append({
            "id": e["id"],
            "name": e["username"],
            "unread": unread["cnt"] if unread else 0
        })

    return jsonify({"peers": result})

# ============================================================
# 5) API: Lấy tin nhắn
# ============================================================
@chat_expert_bp.route("/api/get_messages/<int:user_id>/<int:peer_id>")
def get_messages(user_id, peer_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM messages
        WHERE (sender_id=? AND receiver_id=?)
        OR (sender_id=? AND receiver_id=?)
        ORDER BY created_at ASC
    """, (user_id, peer_id, peer_id, user_id)).fetchall()

    messages = [{
        "sender_id": r["sender_id"],
        "receiver_id": r["receiver_id"],
        "message": r["message"],
        "timestamp": r["created_at"]
    } for r in rows]

    # Đánh dấu đã đọc
    conn.execute("""
        UPDATE messages
        SET is_read=1
        WHERE receiver_id=? AND sender_id=? AND is_read=0
    """, (user_id, peer_id))
    conn.commit()

    return jsonify({"messages": messages})


# ============================================================
# 📌 5) API: gửi tin nhắn (không realtime)
# ============================================================
# @chat_expert_bp.route("/api/send_message", methods=["POST"])
# def send_message():
#     data = request.get_json()
#     sender = data.get("sender_id")
#     receiver = data.get("receiver_id")
#     message = data.get("message", "").strip()

#     if not sender or not receiver or not message:
#         return jsonify({"status": "error"}), 400

#     conn = get_db()
#     conn.execute("""
#         INSERT INTO messages(sender_id, receiver_id, message, created_at)
#         VALUES (?, ?, ?, ?)
#     """, (sender, receiver, message, datetime.now()))
#     conn.commit()

#     return jsonify({"status": "ok"})

# ----- API: Lấy danh sách chuyên gia -----
@chat_expert_bp.route("/api/get_all_experts")
def get_all_experts():
    conn = get_db()
    rows = conn.execute("SELECT id, username FROM users WHERE role='expert'").fetchall()
    experts = [{"id": r["id"], "username": r["username"]} for r in rows]
    return jsonify({"experts": experts})

# ----- API: Lấy số tin nhắn chưa đọc -----
@chat_expert_bp.route("/api/get_unread/<role>/<int:uid>")
def get_unread(role, uid):
    conn = get_db()
    if role == "student":
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM messages WHERE receiver_id=? AND is_read=0",
            (uid,)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM messages WHERE receiver_id=? AND is_read=0",
            (uid,)
        ).fetchone()
    return jsonify({"unread": row["cnt"] if row else 0})


# ============================================================
# 📌 6) SOCKET.IO — join room cố định
# ============================================================
def get_room_for(a, b):
    return f"room_{min(a,b)}_{max(a,b)}"


@socketio.on("join_room")
def handle_join(data):
    user_id = session.get("user_id")
    peer_id = data.get("peer_id")

    if not user_id:
        return

    room = get_room_for(user_id, peer_id)
    join_room(room)


# ============================================================
# 📌 7) SOCKET.IO — gửi tin nhắn realtime
# ============================================================
@socketio.on("send_message")
def handle_send(data):
    sender = session.get("user_id")
    peer = data.get("peer_id")
    msg = data.get("message", "").strip()

    if not sender or not peer or not msg:
        return

    room = get_room_for(sender, peer)

    # Emit realtime
    emit("receive_message", {
        "sender_id": sender,
        "receiver_id": peer,
        "message": msg,
        "timestamp": str(datetime.now())
    }, to=room)

    # Lưu DB
    conn = get_db()
    conn.execute("""
        INSERT INTO messages(sender_id, receiver_id, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (sender, peer, msg, datetime.now()))
    conn.commit()


# ============================================================
# 📌 8) SOCKET.IO — đánh dấu đã đọc realtime
# ============================================================
@socketio.on("mark_read")
def handle_mark_read(data):
    user_id = session.get("user_id")
    peer_id = data.get("peer_id")

    conn = get_db()
    conn.execute("""
        UPDATE messages SET is_read=1
        WHERE receiver_id=? AND sender_id=? AND is_read=0
    """, (user_id, peer_id))
    conn.commit()
