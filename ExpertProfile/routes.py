from flask import Blueprint, session, jsonify, request, render_template, redirect, url_for
from database import TherapySession
from models import User, ExpertProfile
from .ExpertProfile import (
    get_expert_profile,
    update_expert_profile,
    check_profile_completed
)

expert_profile_bp = Blueprint(
    "expert_profile_bp", 
    __name__, 
    url_prefix="/expert/profile",
    template_folder="templates"
)


# Middleware check expert
@expert_profile_bp.before_request
def check_expert():
    """Check xem user có phải expert không"""
    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.url))
    
    if session.get("role") != "expert":
        return jsonify({"error": "Chỉ chuyên gia mới được truy cập"}), 403


# === TRANG WEB ===

@expert_profile_bp.route("/", methods=["GET"])
def profile_page():
    """Trang cập nhật profile chuyên gia"""
    db = TherapySession()
    try:
        profile_data = get_expert_profile(db, session["user_id"])
        return render_template("expert/update_profile.html", profile=profile_data)
    finally:
        db.close()


# === API ENDPOINTS ===

@expert_profile_bp.route("/api/get", methods=["GET"])
def api_get_profile():
    """API: Lấy thông tin profile hiện tại"""
    db = TherapySession()
    try:
        profile_data = get_expert_profile(db, session["user_id"])
        return jsonify({
            "success": True,
            "profile": profile_data
        })
    finally:
        db.close()


@expert_profile_bp.route("/api/update", methods=["POST"])
def api_update_profile():
    """API: Cập nhật profile chuyên gia"""
    data = request.get_json()
    
    # Validate dữ liệu
    required_fields = ["qualification", "years_of_experience", "bio"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                "success": False,
                "message": f"Thiếu thông tin: {field}"
            }), 400
    
    # Validate học vị
    valid_qualifications = ["Tiến sĩ", "Thạc sĩ", "Bác sĩ"]
    if data["qualification"] not in valid_qualifications:
        return jsonify({
            "success": False,
            "message": "Học vị không hợp lệ"
        }), 400
    
    # Validate học hàm (chỉ tiến sĩ mới được chọn)
    title = data.get("title", "")
    if title and title != "Không có":
        if data["qualification"] != "Tiến sĩ":
            return jsonify({
                "success": False,
                "message": "Chỉ Tiến sĩ mới được chọn học hàm"
            }), 400
        
        if title not in ["GS", "PGS"]:
            return jsonify({
                "success": False,
                "message": "Học hàm không hợp lệ"
            }), 400
    
    # Validate số năm kinh nghiệm
    try:
        years = int(data["years_of_experience"])
        if years < 0 or years > 100:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Số năm hành nghề không hợp lệ"
        }), 400
    
    db = TherapySession()
    try:
        result = update_expert_profile(
            db,
            session["user_id"],
            title=title if title != "Không có" else None,
            qualification=data["qualification"],
            years_of_experience=years,
            bio=data["bio"],
            specialization=data.get("specialization", ""),
            organization=data.get("organization", "")
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    finally:
        db.close()


@expert_profile_bp.route("/api/check-completed", methods=["GET"])
def api_check_completed():
    """API: Check xem profile đã hoàn thành chưa"""
    db = TherapySession()
    try:
        is_completed = check_profile_completed(db, session["user_id"])
        return jsonify({
            "success": True,
            "completed": is_completed
        })
    finally:
        db.close()