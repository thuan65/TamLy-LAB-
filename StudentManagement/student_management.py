from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import sqlite3

student_mgmt_bp = Blueprint('student_mgmt', __name__, template_folder='templates')

def get_db_connection():
    conn = sqlite3.connect('therapy.db')
    conn.row_factory = sqlite3.Row
    return conn

@student_mgmt_bp.route('/expert/manage-students')
def manage_students():
    if session.get('role') != 'expert':
        return redirect(url_for('home'))

    expert_id = session.get('user_id')
    search_query = request.args.get('search', '')
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    # 1. Lấy danh sách sinh viên mà Expert đã từng nhắn tin (Giống logic api/get_peers)
    # Chúng ta tìm tất cả sender_id hoặc receiver_id có tương tác với expert_id
    peers_query = '''
        SELECT DISTINCT u.id, u.username, u.status_tag
        FROM users u
        JOIN messages m ON (u.id = m.sender_id OR u.id = m.receiver_id)
        WHERE (m.sender_id = ? OR m.receiver_id = ?)
        AND u.id != ?
        AND u.role = 'STUDENT'
    '''
    peers_rows = conn.execute(peers_query, (expert_id, expert_id, expert_id)).fetchall()
    
    # Chuyển đổi thành list dict để dễ thêm trường status_tag nếu cần
    # Chuyển đổi sang list các dict và thêm status_tag mặc định để HTML không bị lỗi
    accepted_students = []
    for row in peers_rows:
        s = dict(row)
        # s['status_tag'] = 'Đang theo dõi' # Giá trị mặc định cho giao diện
        req = conn.execute("SELECT status FROM quiz_access_requests WHERE student_id = ? AND expert_id = ?", 
                           (s['id'], expert_id)).fetchone()
        s['request_status'] = req['status'] if req else None
        accepted_students.append(s)

    # 2. Logic tìm kiếm (Sửa lỗi Incorrect number of bindings)
    searched_students = []
    if search_query:
        # Dùng dấu ? để truyền tham số, không dùng f-string trực tiếp trong câu lệnh
        query = "SELECT * FROM users WHERE role = 'STUDENT' AND username LIKE ?"
        search_rows = conn.execute(query, (f'%{search_query}%',)).fetchall()
        #searched_students = [dict(r) for r in search_rows]
        # Chuyển kết quả tìm kiếm thành list dict
        # for r in search_rows:
        #     # Chỉ hiện ở mục tìm kiếm nếu sinh viên này chưa có trong danh sách theo dõi
        #     if not any(p['id'] == r['id'] for p in accepted_students):
        #         searched_students.append(dict(r))
        for r in search_rows:
            sd = dict(r)
            req = conn.execute('SELECT status FROM quiz_access_requests WHERE expert_id=? AND student_id=?', 
                             (expert_id, sd['id'])).fetchone()
            sd['request_status'] = req['status'] if req else None
            searched_students.append(sd)

    conn.close()
    return render_template('student_management.html', 
                           accepted_students=accepted_students, 
                           searched_students=searched_students)

@student_mgmt_bp.route('/expert/request-quiz/<int:student_id>', methods=['POST'])
def request_quiz(student_id):
    expert_id = session.get('user_id')
    conn = get_db_connection()
    # Kiểm tra xem đã gửi chưa
    existing = conn.execute('SELECT id, status FROM quiz_access_requests WHERE expert_id=? AND student_id=?', 
                           (expert_id, student_id)).fetchone()
    # if not existing:
    #     conn.execute('INSERT INTO quiz_access_requests (expert_id, student_id) VALUES (?, ?)', 
    #                  (expert_id, student_id))
    #     conn.commit()
    if not existing:
        # Nếu chưa từng có request, insert mới
        conn.execute(
            'INSERT INTO quiz_access_requests (expert_id, student_id, status) VALUES (?, ?, "pending")', 
            (expert_id, student_id)
        )
    elif existing['status'] == 'rejected':
        # Nếu đã bị từ chối, cập nhật lại thành pending để gửi lại
        conn.execute(
            'UPDATE quiz_access_requests SET status = "pending", is_read_expert = 0, created_at = ? WHERE id = ?',
            (datetime.now(), existing['id'])
        )
    else:
        # Nếu đang pending hoặc đã accepted thì không làm gì cả
        conn.close()
        return jsonify({'status': 'already_exists'})

    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

@student_mgmt_bp.route('/expert/toggle-status/<int:student_id>', methods=['POST'])
def toggle_status(student_id):
    conn = get_db_connection()
    user = conn.execute('SELECT status_tag FROM users WHERE id=?', (student_id,)).fetchone()
    new_status = 'CURED' if user['status_tag'] != 'CURED' else 'ILL'
    conn.execute('UPDATE users SET status_tag = ? WHERE id = ?', (new_status, student_id))
    conn.commit()
    conn.close()
    return jsonify({'new_status': new_status})

@student_mgmt_bp.route('/expert/view-report/<int:student_id>')
@student_mgmt_bp.route('/expert/view-report/<int:student_id>')
def view_report(student_id):
    expert_id = session.get('user_id')
    conn = get_db_connection()

    # Kiểm tra quyền truy cập (phải là accepted)
    check = conn.execute(
        'SELECT status FROM quiz_access_requests WHERE expert_id=? AND student_id=? AND status="accepted"',
        (expert_id, student_id)
    ).fetchone()

    if not check:
        conn.close()
        return "Bạn không có quyền xem báo cáo này hoặc yêu cầu chưa được chấp nhận.", 403

    # Lấy lịch sử Quiz
    quizzes_rows = conn.execute(
        'SELECT * FROM stress_logs WHERE student_id=? ORDER BY created_at DESC',
        (student_id,)
    ).fetchall()

    # Lấy lịch sử Mood từ Nhật ký
    moods_rows = conn.execute(
        'SELECT created_at, mood, mood_score FROM diary_entries WHERE student_id=? ORDER BY created_at DESC',
        (student_id,)
    ).fetchall()

    student_row = conn.execute(
        'SELECT username FROM users WHERE id=?',
        (student_id,)
    ).fetchone()

    conn.close()

    # ✅ Convert Row -> dict (để tojson dùng được)
    quizzes = [dict(r) for r in quizzes_rows]
    moods = [dict(r) for r in moods_rows]
    student = dict(student_row) if student_row else {"username": "Unknown"}

    # ✅ Convert created_at -> string cho chắc (tránh datetime/object lạ)
    for q in quizzes:
        if q.get("created_at") is not None:
            q["created_at"] = str(q["created_at"])
    for m in moods:
        if m.get("created_at") is not None:
            m["created_at"] = str(m["created_at"])

    return render_template('view_report.html', quizzes=quizzes, moods=moods, student=student)


@student_mgmt_bp.route('/api/notifications')
def get_notifications():
    if "user_id" not in session:
        return jsonify([])

    uid = session.get('user_id')
    role = session.get('role').upper()
    conn = get_db_connection()
    notis = []
    
    if role == 'STUDENT':
        # SV nhận yêu cầu từ Expert
        rows = conn.execute('''
            SELECT r.id, u.username as expert_name, r.status 
            FROM quiz_access_requests r 
            JOIN users u ON r.expert_id = u.id 
            WHERE r.student_id = ? AND r.status = "pending"
        ''', (uid,)).fetchall()
        for r in rows:
            notis.append({'id': r['id'], 'msg': f"Chuyên gia {r['expert_name']} muốn xem lịch sử của bạn", 'type': 'request'})
    else:
        # Expert nhận phản hồi từ SV
        rows = conn.execute('''
            SELECT r.id, u.username as student_name, r.status 
            FROM quiz_access_requests r 
            JOIN users u ON r.student_id = u.id 
            WHERE r.expert_id = ? AND r.status IN ("accepted", "rejected") AND (r.is_read_expert = 0 OR r.is_read_expert IS NULL)
            ORDER BY r.created_at DESC
        ''', (uid,)).fetchall()
        for r in rows:
            notis.append({'id': r['id'], 'msg': f"Sinh viên {r['student_name']} đã {r['status']} yêu cầu", 'type': 'response'})
            
    conn.close()
    return jsonify(notis)

@student_mgmt_bp.route('/student/respond-request/<int:request_id>/<string:action>')
def respond_request(request_id, action):
    if "user_id" not in session: return redirect(url_for('auth.login'))

    status = 'accepted' if action == 'agree' else 'rejected'
    conn = get_db_connection()
    conn.execute('UPDATE quiz_access_requests SET status = ?, is_read_student = 1 WHERE id = ?', 
                 (status, request_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@student_mgmt_bp.route('/expert/mark-read-notifications', methods=['POST'])
def mark_read_notifications():
    expert_id = session.get('user_id')
    conn = get_db_connection()
    conn.execute(
        'UPDATE quiz_access_requests SET is_read_expert = 1 WHERE expert_id = ? AND status IN ("accepted", "rejected")',
        (expert_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})