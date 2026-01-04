from datetime import datetime
from sqlalchemy import select
from models import User, ExpertProfile


def is_admin(db, user_id: int) -> bool:
    """Check xem user có phải admin không"""
    user = db.query(User).filter_by(id=user_id).first()
    return user is not None and user.role == "ADMIN"


def get_pending_experts_list(db):
    """
    Lấy danh sách chuyên gia có verification_status = PENDING
    Returns: list of dict
    """
    pending_profiles = db.query(ExpertProfile).filter_by(
        verification_status="PENDING"
    ).all()
    
    result = []
    for profile in pending_profiles:
        user = db.query(User).filter_by(id=profile.user_id).first()
        result.append({
            "user_id": profile.user_id,
            "username": user.username if user else "N/A",
            "full_name": profile.full_name,
            "title": profile.title,
            "qualification": profile.qualification,
            "specialization": profile.specialization,
            "organization": profile.organization,
            "years_of_experience": profile.years_of_experience,
            "bio": profile.bio,
            "created_at": profile.created_at.isoformat() if profile.created_at else None
        })
    
    return result


def get_all_experts_list(db):
    """
    Lấy tất cả chuyên gia (cả PENDING, VERIFIED, REJECTED)
    Returns: list of dict
    """
    all_profiles = db.query(ExpertProfile).all()
    
    result = []
    for profile in all_profiles:
        user = db.query(User).filter_by(id=profile.user_id).first()
        result.append({
            "user_id": profile.user_id,
            "username": user.username if user else "N/A",
            "full_name": profile.full_name,
            "verification_status": profile.verification_status,
            "specialization": profile.specialization,
            "years_of_experience": profile.years_of_experience,
            "is_active": profile.is_active,
            "verified_at": profile.verified_at.isoformat() if profile.verified_at else None
        })
    
    return result


def verify_expert_profile(db, user_id: int, admin_id: int):
    """
    Duyệt chuyên gia: PENDING -> VERIFIED
    
    Args:
        db: database session
        user_id: ID của user là chuyên gia cần verify
        admin_id: ID của admin đang thực hiện verify
    
    Returns:
        dict: {"success": bool, "message": str, ...}
    """
    # Tìm expert profile theo user_id
    profile = db.query(ExpertProfile).filter_by(user_id=user_id).first()
    
    if not profile:
        return {
            "success": False,
            "message": "Không tìm thấy profile chuyên gia"
        }
    
    if profile.verification_status == "VERIFIED":
        return {
            "success": False,
            "message": "Chuyên gia này đã được verify rồi"
        }
    
    # Cập nhật trạng thái
    profile.verification_status = "VERIFIED"
    profile.verified_by = admin_id
    profile.verified_at = datetime.now()
    profile.is_active = True  # Kích hoạt account
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Đã verify thành công chuyên gia {profile.full_name}",
        "user_id": user_id,
        "full_name": profile.full_name
    }


def reject_expert_profile(db, user_id: int, reason: str = ""):
    """
    Từ chối chuyên gia: PENDING -> REJECTED (hoặc xóa)
    
    Args:
        db: database session
        user_id: ID của user là chuyên gia cần reject
        reason: Lý do từ chối
    
    Returns:
        dict: {"success": bool, "message": str, ...}
    """
    profile = db.query(ExpertProfile).filter_by(user_id=user_id).first()
    
    if not profile:
        return {
            "success": False,
            "message": "Không tìm thấy profile chuyên gia"
        }
    
    #  Đặt status = REJECTED
    profile.verification_status = "REJECTED"
    profile.is_active = False
        
    db.commit()
    
    return {
        "success": True,
        "message": f"Đã từ chối chuyên gia {profile.full_name}",
        "user_id": user_id,
        "reason": reason
    }


def get_admin_stats(db):
    """
    Lấy thống kê tổng quan cho admin dashboard
    Returns: dict
    """
    total_users = db.query(User).count()
    total_students = db.query(User).filter_by(role="STUDENT").count()
    total_experts = db.query(User).filter_by(role="EXPERT").count()
    total_admins = db.query(User).filter_by(role="ADMIN").count()
    
    pending_experts = db.query(ExpertProfile).filter_by(
        verification_status="PENDING"
    ).count()
    
    verified_experts = db.query(ExpertProfile).filter_by(
        verification_status="VERIFIED"
    ).count()
    
    rejected_experts = db.query(ExpertProfile).filter_by(
        verification_status="REJECTED"
    ).count()
    
    return {
        "total_users": total_users,
        "total_students": total_students,
        "total_experts": total_experts,
        "total_admins": total_admins,
        "pending_experts": pending_experts,
        "verified_experts": verified_experts,
        "rejected_experts": rejected_experts
    }