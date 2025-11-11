# chat_expert.py
from flask import Blueprint, render_template, request, jsonify, session
from db import get_db
from datetime import datetime

chat = Blueprint("chat", __name__, url_prefix="/chat")

# ----- Route dashboard/chat -----
@chat.route("")
def chat_dashboard():
    """
    Student: show list of experts
    Expert: show list of students who have chatted
    """
    if "user_id" not in session:
        return "Bạn cần đăng nhập để vào chat.", 403

    role = session.get("role")
    user_id = session.get("user_id")
    conn = get_db()

    if role == "student":
        # Lấy danh sách tất cả chuyên gia
        experts = conn.execute("SELECT id, username FROM users WHERE role='expert'").fetchall()
        experts_list = [{"id": e["id"], "username": e["username"]} for e in experts]
        return render_template("dashboard.html", username=session["username"], role=role, user_id=user_id, experts=experts_list)
    else:
        # Expert: lấy danh sách học sinh đã chat
        rows = conn.execute(
            "SELECT DISTINCT sender_id AS student_id FROM messages WHERE receiver_id=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        students_list = [r["student_id"] for r in rows]
        return render_template("dashboard.html", username=session["username"], role=role, user_id=user_id, students=students_list)

# ----- Route mở chat messenger với peer -----
@chat.route("/<int:peer_id>")
def open_chat(peer_id):
    if "user_id" not in session:
        return "Bạn cần đăng nhập để vào chat.", 403

    role = session.get("role")
    user_id = session.get("user_id")
    conn = get_db()

    peer = conn.execute("SELECT username FROM users WHERE id=?", (peer_id,)).fetchone()
    peer_name = peer["username"] if peer else (f"Học sinh {peer_id}" if role=="expert" else f"Chuyên gia {peer_id}")

    return render_template("chat_messenger.html",
                           user_id=user_id,
                           role=role,
                           peer_id=peer_id,
                           peer_name=peer_name)

# ----- API: Lấy danh sách chuyên gia -----
@chat.route("/api/get_all_experts")
def get_all_experts():
    conn = get_db()
    rows = conn.execute("SELECT id, username FROM users WHERE role='expert'").fetchall()
    experts = [{"id": r["id"], "username": r["username"]} for r in rows]
    return jsonify({"experts": experts})

# ----- API: Lấy danh sách học sinh đã chat với expert -----
@chat.route("/api/get_chats_for_expert/<int:expert_id>")
def get_chats_for_expert(expert_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT DISTINCT sender_id AS student_id FROM messages WHERE receiver_id=? ORDER BY created_at DESC",
        (expert_id,)
    ).fetchall()
    students = [r["student_id"] for r in rows]
    return jsonify({"students": students})

# ----- API: Lấy số tin nhắn chưa đọc -----
@chat.route("/api/get_unread/<role>/<int:uid>")
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

# ----- API: Lấy tin nhắn giữa 2 người -----
@chat.route("/api/get_messages/<int:user_id>/<int:peer_id>")
def get_messages(user_id, peer_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM messages
        WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
        ORDER BY created_at ASC
    """, (user_id, peer_id, peer_id, user_id)).fetchall()

    messages = []
    for r in rows:
        messages.append({
            "sender_id": r["sender_id"],
            "receiver_id": r["receiver_id"],
            "message": r["message"],
            "timestamp": r["created_at"]
        })
    return jsonify({"messages": messages})

# ----- API: Gửi tin nhắn -----
@chat.route("/api/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    message = data.get("message", "").strip()

    if not sender_id or not receiver_id or not message:
        return jsonify({"status": "error", "message": "Missing data"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO messages (sender_id, receiver_id, message, created_at, is_read) VALUES (?, ?, ?, ?, 0)",
        (sender_id, receiver_id, message, datetime.now())
    )
    conn.commit()
    return jsonify({"status": "success"})
