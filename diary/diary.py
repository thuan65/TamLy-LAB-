# diary/diary.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session as flask_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import TherapySession
from models import DiaryEntry, User
from datetime import datetime
from models import DiaryEntry  
import os


diary_bp = Blueprint(
    "diary",
    __name__,
    template_folder="htmltemplates",
    static_folder="../static"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "therapy.db")
)

from flask import redirect, url_for
from flask import session 

#@diary_bp.route("/diary")
#def diary_home():
#    user_id = session.get("user_id")
#    if user_id:
#        # user_id == student_id (theo thiết kế hiện tại)
#        return redirect(url_for("diary.list_diary", student_id=user_id))
#    else:
#        return redirect(url_for("auth.login"))

@diary_bp.route("/diary")
def diary_home():

    user_id = session.get("user_id")
    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.full_path))

    with TherapySession() as db_session:
        student = db_session.query(User).filter_by(id=user_id).first()

    if not student:
        return "❌ User này chưa có hồ sơ Student (chưa link).", 404

    return redirect(url_for("diary.list_diary", student_id=student.id))

# --- Danh sách nhật ký của sinh viên ---
@diary_bp.route("/diary/<int:student_id>", methods=["GET"])
def list_diary(student_id):
    """Hiển thị tất cả nhật ký của sinh viên"""
    with TherapySession() as session:
        student = session.query(User).filter_by(id=student_id).first()
    
        if not student:
            return "❌ Không tìm thấy sinh viên", 404
    
        # Lấy tất cả nhật ký, sắp xếp mới nhất trước
        entries = session.query(DiaryEntry).filter_by(student_id=student_id)\
            .order_by(DiaryEntry.created_at.desc()).all()
        
    return render_template("diary_list.html", student=student, entries=entries)

# --- Xem chi tiết 1 nhật ký ---
@diary_bp.route("/diary/view/<int:entry_id>", methods=["GET"])
def view_diary(entry_id):
    """Xem chi tiết một bài nhật ký"""
    with TherapySession() as  session:
        entry = session.query(DiaryEntry).filter_by(id=entry_id).first()
        
        if not entry:
            return "❌ Không tìm thấy nhật ký", 404
        
        student = session.query(User).filter_by(id=entry.student_id).first()
    return render_template("diary_view.html", entry=entry, student=student)

# --- Tạo nhật ký mới ---
@diary_bp.route("/diary/create/<int:student_id>", methods=["GET", "POST"])
def create_diary(student_id):
    """Tạo nhật ký mới"""
    with TherapySession() as  s:
        student = s.query(User).filter_by(id=student_id).first()
        
        if not student:
            return "❌ Không tìm thấy sinh viên", 404
        
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            content = request.form.get("content", "").strip()
            mood = request.form.get("mood", "Bình thường")
            mood_score = int(request.form.get("mood_score", 3))
            tags = request.form.get("tags", "").strip()
            is_private = int(request.form.get("is_private", 1))
            
            if not title or not content:
                return "⚠️ Vui lòng điền đầy đủ tiêu đề và nội dung", 400
            
            # Tạo entry mới
            entry = DiaryEntry(
                student_id=student_id,
                title=title,
                content=content,
                mood=mood,
                mood_score=mood_score,
                tags=tags,
                is_private=is_private
            )
            
            s.add(entry)
            s.commit()
            from streak.utils import mark_diary
            mark_diary(s, user_id=session["user_id"])

            entry_id = entry.id
            
            return redirect(url_for("diary.view_diary", entry_id=entry_id))
        
    return render_template("diary_create.html", student=student)

# --- Chỉnh sửa nhật ký ---
@diary_bp.route("/diary/edit/<int:entry_id>", methods=["GET", "POST"])
def edit_diary(entry_id):
    """Chỉnh sửa nhật ký"""
    with TherapySession() as s:
        entry = s.query(DiaryEntry).filter_by(id=entry_id).first()
        
        if not entry:
            return "❌ Không tìm thấy nhật ký", 404
        
        student = s.query(User).filter_by(id=entry.student_id).first()
        
        if request.method == "POST":
            entry.title = request.form.get("title", "").strip()
            entry.content = request.form.get("content", "").strip()
            entry.mood = request.form.get("mood", "Bình thường")
            entry.mood_score = int(request.form.get("mood_score", 3))
            entry.tags = request.form.get("tags", "").strip()
            entry.is_private = int(request.form.get("is_private", 1))
            entry.updated_at = datetime.now().isoformat(timespec="seconds")
            
            s.commit()
            
            return redirect(url_for("diary.view_diary", entry_id=entry_id))
        
    return render_template("diary_edit.html", entry=entry, student=student)

# --- Xóa nhật ký ---
@diary_bp.route("/diary/delete/<int:entry_id>", methods=["POST"])
def delete_diary(entry_id):
    """Xóa nhật ký"""
    with TherapySession() as s:

        entry = s.query(DiaryEntry).filter_by(id=entry_id).first()
        
        if not entry:
            return jsonify({"success": False, "message": "Không tìm thấy nhật ký"}), 404
        
        student_id = entry.student_id
        s.delete(entry)
        s.commit()
    
    return redirect(url_for("diary.list_diary", student_id=student_id))


# --- API: Lấy thống kê tâm trạng ---
@diary_bp.route("/api/diary/mood-stats/<int:student_id>", methods=["GET"])
def mood_stats(student_id):
    """Thống kê tâm trạng của sinh viên qua các ngày"""
    with TherapySession() as s:
        entries = (
            s.query(DiaryEntry)
            .filter_by(student_id=student_id)
            .order_by(DiaryEntry.created_at.asc())
            .all()
        )

        stats = []
        for entry in entries:
            dt = entry.created_at
            if isinstance(dt, str):
                # nếu string ISO "YYYY-MM-DDTHH:MM:SS"
                dt_str = dt[:10]
            else:
                dt_str = dt.strftime("%Y-%m-%d")

            stats.append({
                "date": dt_str,
                "mood": entry.mood,
                "mood_score": entry.mood_score,
                "title": entry.title
            })

    return jsonify({"success": True, "stats": stats})


@diary_bp.route("/mood-chart", methods=["GET"])
def mood_chart_page():
    user_id = flask_session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    return render_template("mood_chart.html")


@diary_bp.route("/api/mood-series", methods=["GET"])
def mood_series_api():
    user_id = flask_session.get("user_id")
    if not user_id:
        return jsonify({"error": "unauthorized"}), 401

    with TherapySession() as db:
        entries = (
            db.query(DiaryEntry)
            .filter(DiaryEntry.student_id == user_id)     # ✅ sửa chỗ này
            .order_by(DiaryEntry.created_at.asc())
            .all()
        )

    labels, data = [], []
    for e in entries:
        if e.mood_score is None:
            continue

        dt = e.created_at
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except Exception:
                # fallback nếu format lạ
                dt = datetime.strptime(dt[:10], "%Y-%m-%d")

        labels.append(dt.strftime("%d/%m"))
        data.append(float(e.mood_score))

    return jsonify({"labels": labels, "data": data})
