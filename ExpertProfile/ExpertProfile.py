from models import User, ExpertProfile


def get_expert_profile(db, user_id: int):
    """
    Lấy thông tin profile của expert
    Returns: dict hoặc None
    """
    profile = db.query(ExpertProfile).filter_by(user_id=user_id).first()
    
    if not profile:
        return None
    
    return {
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "title": profile.title,
        "qualification": profile.qualification,
        "specialization": profile.specialization,
        "organization": profile.organization,
        "years_of_experience": profile.years_of_experience,
        "bio": profile.bio,
        "verification_status": profile.verification_status,
        "is_active": profile.is_active,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
    }


def update_expert_profile(db, user_id: int, **kwargs):
    """
    Cập nhật profile của expert
    
    Args:
        db: database session
        user_id: ID của expert
        **kwargs: các field cần update (title, qualification, years_of_experience, bio, etc.)
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    profile = db.query(ExpertProfile).filter_by(user_id=user_id).first()
    
    if not profile:
        return {
            "success": False,
            "message": "Không tìm thấy profile chuyên gia"
        }
    
    # Cập nhật các field
    if "title" in kwargs:
        profile.title = kwargs["title"]
    
    if "qualification" in kwargs:
        profile.qualification = kwargs["qualification"]
    
    if "years_of_experience" in kwargs:
        profile.years_of_experience = kwargs["years_of_experience"]
    
    if "bio" in kwargs:
        profile.bio = kwargs["bio"]
    
    if "specialization" in kwargs:
        profile.specialization = kwargs["specialization"]
    
    if "organization" in kwargs:
        profile.organization = kwargs["organization"]
    
    if profile.verification_status == "NONE":
        profile.verification_status = "PENDING"
    
    db.commit()
    
    return {
        "success": True,
        "message": "Cập nhật profile thành công! Vui lòng đợi admin verify.",
        "profile": get_expert_profile(db, user_id)
    }


def check_profile_completed(db, user_id: int) -> bool:
    """
    Check xem expert đã điền đủ thông tin profile chưa
    
    Required fields: qualification, years_of_experience, bio
    """
    profile = db.query(ExpertProfile).filter_by(user_id=user_id).first()
    
    if not profile:
        return False
    
    # Check các field bắt buộc
    required_fields = [
        profile.qualification,
        profile.years_of_experience,
        profile.bio
    ]
    
    # Tất cả field bắt buộc phải có giá trị
    return all(field is not None and str(field).strip() != "" for field in required_fields)