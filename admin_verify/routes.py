from flask import Blueprint, session, jsonify, request, render_template
from database import TherapySession
from models import User, ExpertProfile
from .utils import (
    is_admin,
    get_pending_experts_list,
    get_all_experts_list,
    verify_expert_profile,
    reject_expert_profile,
    get_admin_stats
)

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


# Check admin cho tất cả routes
@admin_bp.before_request
def check_admin():
    """Check xem user có phải admin không trước mỗi request"""
    # Bỏ qua check cho trang login
    if request.endpoint == "admin_bp.admin_login":
        return None
    
    if "user_id" not in session:
        return jsonify({"error": "Chưa đăng nhập"}), 401
    
    db = TherapySession()
    if not is_admin(db, session["user_id"]):
        db.close()
        return jsonify({"error": "Không có quyền truy cập. Chỉ admin mới được vào."}), 403
    db.close()



@admin_bp.route("/dashboard")
def dashboard():
    """Trang dashboard của admin để verify chuyên gia"""
    return render_template("admin/dashboard.html")


# === API ENDPOINTS ===

@admin_bp.route("/api/experts/pending", methods=["GET"])
def api_get_pending_experts():
    """API: Lấy danh sách chuyên gia chờ duyệt"""
    db = TherapySession()
    try:
        pending_list = get_pending_experts_list(db)
        return jsonify({
            "success": True,
            "pending_experts": pending_list,
            "count": len(pending_list)
        })
    finally:
        db.close()


@admin_bp.route("/api/experts/all", methods=["GET"])
def api_get_all_experts():
    """API: Lấy tất cả chuyên gia"""
    db = TherapySession()
    try:
        all_list = get_all_experts_list(db)
        return jsonify({
            "success": True,
            "experts": all_list,
            "count": len(all_list)
        })
    finally:
        db.close()


@admin_bp.route("/api/experts/<int:user_id>/verify", methods=["POST"])
def api_verify_expert(user_id):
    """API: Duyệt chuyên gia (PENDING -> VERIFIED)"""
    db = TherapySession()
    try:
        result = verify_expert_profile(
            db, 
            user_id, 
            admin_id=session["user_id"]
        )
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    finally:
        db.close()


@admin_bp.route("/api/experts/<int:user_id>/reject", methods=["POST"])
def api_reject_expert(user_id):
    """API: Từ chối chuyên gia"""
    data = request.get_json() or {}
    reason = data.get("reason", "Không đáp ứng yêu cầu")
    
    db = TherapySession()
    try:
        result = reject_expert_profile(db, user_id, reason)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    finally:
        db.close()


@admin_bp.route("/api/stats", methods=["GET"])
def api_get_stats():
    """API: Thống kê cho admin dashboard"""
    db = TherapySession()
    try:
        stats = get_admin_stats(db)
        return jsonify({
            "success": True,
            "stats": stats
        })
    finally:
        db.close()