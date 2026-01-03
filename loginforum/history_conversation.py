# history_conversation.py
from flask import Blueprint, request, jsonify, render_template, current_app
from db import get_db  # Hàm trả về conn SQLite (dict row)
import logging

# --- Tạo Blueprint ---
history_bp = Blueprint('history', __name__, url_prefix="/chat", template_folder='htmltemplates')


# --- API lưu lịch sử ---
@history_bp.route('/api/save_history', methods=['POST'])
def save_history():
    try:
        data = request.json
        user_id = data['user_id']
        session_type = data['session_type']
        session_key = data.get('session_key', '')
        user_message = data.get('user_message')
        system_response = data.get('system_response')

        conn = get_db()
        cursor = conn.execute(
            "INSERT INTO conversation_history "
            "(user_id, session_type, session_key, user_message, system_response) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, session_type, session_key, user_message, system_response)
        )
        conn.commit()
        record_id = cursor.lastrowid

        return jsonify({"status": "success", "record_id": record_id}), 200

    except Exception as e:
        logging.error(f"Error saving history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- API lấy lịch sử ---
@history_bp.route('/api/get_history/<string:session_key>', methods=['GET'])
def get_history(session_key):
    try:
        conn = get_db()
        records = conn.execute(
            "SELECT * FROM conversation_history WHERE session_key=? ORDER BY timestamp ASC",
            (session_key,)
        ).fetchall()

        history_list = []
        for r in records:
            history_list.append({
                "id": r["id"],
                "user_id": r["user_id"],
                "session_type": r["session_type"],
                "session_key": r["session_key"],
                "user_message": r["user_message"],
                "system_response": r["system_response"],
                "timestamp": r["timestamp"]
            })

        return jsonify({"status": "success", "history": history_list}), 200

    except Exception as e:
        logging.error(f"Error fetching history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Route test (hiển thị giao diện chat) ---
@history_bp.route('/')
def chat_interface():
    # Demo: user_id=1, session_type='chatbot'
    return render_template('chat.html', user_id=1, session_type='chatbot')
