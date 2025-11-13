from flask import Blueprint, jsonify, request
from datetime import date, datetime
from .db import connect

gamify = Blueprint("gamify", __name__, url_prefix="/api/gamify")

# --- cập nhật streak nhật ký ---
@gamify.route("/diary/<int:student_id>", methods=["POST"])
def update_diary(student_id):
    from datetime import date

    today = date.today().isoformat()
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT streak, last_date FROM diary_streak WHERE student_id=?", (student_id,))
    row = cur.fetchone()

    # --- Nếu chưa có streak cho user này ---
    if not row:
        cur.execute("""
            INSERT INTO diary_streak (student_id, streak, last_date)
            VALUES (?, ?, ?)
        """, (student_id, 1, today))

        conn.commit()
        conn.close()
        return jsonify({"ok": True, "streak": 1})

    # --- Nếu đã có streak ---
    last_date = row["last_date"]
    streak = row["streak"]

    # 🚫 1) Nếu hôm nay đã viết rồi → KHÔNG tăng streak
    if last_date == today:
        conn.close()
        return jsonify({"ok": True, "streak": streak})   # giữ nguyên streak

    # 🔥 2) Nếu hôm nay là ngày KẾ TIẾP so với ngày cuối cùng
    from datetime import datetime, timedelta
    yesterday = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=1)).date().isoformat()

    if last_date == yesterday:
        streak += 1   # tăng streak
    else:
        streak = 1    # reset streak vì bỏ ngày rồi

    # update streak trong DB
    cur.execute("""
        UPDATE diary_streak
        SET streak=?, last_date=?
        WHERE student_id=?
    """, (streak, today, student_id))

    conn.commit()
    conn.close()
    return jsonify({"ok": True, "streak": streak})


# --- log chơi game (Silk / Zoomquilt) ---
@gamify.route("/game/<int:student_id>", methods=["POST"])
def log_game(student_id):
    data = request.json
    game_name = data.get("game", "unknown")
    now = datetime.now().isoformat()

    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO game_log(student_id, game, played_at) VALUES (?, ?, ?)",
                (student_id, game_name, now))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


# --- trả thống kê ---
@gamify.route("/stats/<int:student_id>")
def stats(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT streak, last_date FROM diary_streak WHERE student_id=?", (student_id,))
    streak_row = cur.fetchone()

    cur.execute("SELECT COUNT(*) AS c FROM game_log WHERE student_id=?", (student_id,))
    game_count = cur.fetchone()["c"]

    conn.close()

    return jsonify({
        "diary_streak": streak_row["streak"] if streak_row else 0,
        "diary_last": streak_row["last_date"] if streak_row else None,
        "games_played": game_count
    })
