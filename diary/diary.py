# diary/diary.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import DiaryEntry, Student
from datetime import datetime

diary_bp = Blueprint(
    "diary",
    __name__,
    template_folder="templates",
    static_folder="../static"
)

# --- Kết nối DB ---
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)

# --- Danh sách nhật ký của sinh viên ---
@diary_bp.route("/diary/<int:student_id>", methods=["GET"])
def list_diary(student_id):
    """Hiển thị tất cả nhật ký của sinh viên"""
    s = Session()
    student = s.query(Student).filter_by(id=student_id).first()
    
    if not student:
        return "❌ Không tìm thấy sinh viên", 404
    
    # Lấy tất cả nhật ký, sắp xếp mới nhất trước
    entries = s.query(DiaryEntry).filter_by(student_id=student_id)\
        .order_by(DiaryEntry.created_at.desc()).all()
    
    s.close()
    return render_template("diary_list.html", student=student, entries=entries)

# --- Xem chi tiết 1 nhật ký ---
@diary_bp.route("/diary/view/<int:entry_id>", methods=["GET"])
def view_diary(entry_id):
    """Xem chi tiết một bài nhật ký"""
    s = Session()
    entry = s.query(DiaryEntry).filter_by(id=entry_id).first()
    
    if not entry:
        return "❌ Không tìm thấy nhật ký", 404
    
    student = s.query(Student).filter_by(id=entry.student_id).first()
    s.close()
    return render_template("diary_view.html", entry=entry, student=student)

# --- Tạo nhật ký mới ---
@diary_bp.route("/diary/create/<int:student_id>", methods=["GET", "POST"])
def create_diary(student_id):
    """Tạo nhật ký mới"""
    s = Session()
    student = s.query(Student).filter_by(id=student_id).first()
    
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
        entry_id = entry.id
        s.close()
        
        return redirect(url_for("diary.view_diary", entry_id=entry_id))
    
    s.close()
    return render_template("diary_create.html", student=student)

# --- Chỉnh sửa nhật ký ---
@diary_bp.route("/diary/edit/<int:entry_id>", methods=["GET", "POST"])
def edit_diary(entry_id):
    """Chỉnh sửa nhật ký"""
    s = Session()
    entry = s.query(DiaryEntry).filter_by(id=entry_id).first()
    
    if not entry:
        return "❌ Không tìm thấy nhật ký", 404
    
    student = s.query(Student).filter_by(id=entry.student_id).first()
    
    if request.method == "POST":
        entry.title = request.form.get("title", "").strip()
        entry.content = request.form.get("content", "").strip()
        entry.mood = request.form.get("mood", "Bình thường")
        entry.mood_score = int(request.form.get("mood_score", 3))
        entry.tags = request.form.get("tags", "").strip()
        entry.is_private = int(request.form.get("is_private", 1))
        entry.updated_at = datetime.now().isoformat(timespec="seconds")
        
        s.commit()
        s.close()
        
        return redirect(url_for("diary.view_diary", entry_id=entry_id))
    
    s.close()
    return render_template("diary_edit.html", entry=entry, student=student)

# --- Xóa nhật ký ---
@diary_bp.route("/diary/delete/<int:entry_id>", methods=["POST"])
def delete_diary(entry_id):
    """Xóa nhật ký"""
    s = Session()
    entry = s.query(DiaryEntry).filter_by(id=entry_id).first()
    
    if not entry:
        return jsonify({"success": False, "message": "Không tìm thấy nhật ký"}), 404
    
    student_id = entry.student_id
    s.delete(entry)
    s.commit()
    s.close()
    
    return redirect(url_for("diary.list_diary", student_id=student_id))

# --- API: Lấy thống kê tâm trạng ---
@diary_bp.route("/api/diary/mood-stats/<int:student_id>", methods=["GET"])
def mood_stats(student_id):
    """Thống kê tâm trạng của sinh viên qua các ngày"""
    s = Session()
    entries = s.query(DiaryEntry).filter_by(student_id=student_id)\
        .order_by(DiaryEntry.created_at.asc()).all()
    
    stats = []
    for entry in entries:
        stats.append({
            "date": entry.created_at[:10],  # Lấy ngày (YYYY-MM-DD)
            "mood": entry.mood,
            "mood_score": entry.mood_score,
            "title": entry.title
        })
    
    s.close()
    return jsonify({"success": True, "stats": stats})