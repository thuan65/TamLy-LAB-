from models import User, ExpertProfile
from database import TherapySession
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import joinedload

def create_expert():
    with TherapySession() as db:
        # 1️⃣ Tạo User
        user = User(
            username="expert_demo_01",
            password=generate_password_hash("123456"),
            role="EXPERT",
            chat_opt_in=True
        )

        db.add(user)
        db.flush()  # ⭐ cực kỳ quan trọng (để có user.id)

        # 2️⃣ Tạo ExpertProfile (1-1)
        profile = ExpertProfile(
            user_id=user.id,       # hoặc gán bằng relationship
            full_name="Dr. Nguyễn Văn A",
            title="TS",
            qualification="PhD Psychology",
            specialization="Stress & Anxiety",
            years_of_experience=8,
            verification_status="VERIFIED",
            is_active=True
        )

        db.add(profile)

        db.commit()
        print(f"✅ Created expert user_id={user.id}")

def to_dict(obj):
    """Chuyển object database thành dictionary python thuần túy"""
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

def testing():
    db = TherapySession()

    therapists_objs = db.query(User)\
    .options(joinedload(User.expert_profile))\
    .filter(User.role=="EXPERT")\
    .filter(ExpertProfile.is_active==True)\
    .filter(ExpertProfile.verification_status== "VERIFIED")\
    .all()
    
    therapists_list = [to_dict(t) for t in therapists_objs]
    print(therapists_list)
    db.close()

if __name__ == "__main__":
    testing()
    # if not session.query(Therapist).first():
    #     t1 = Therapist(full_name="ThS. Nguyễn An", field="Stress, học đường", image="static/therapists/an.jpg",
    #                 years_exp=5, degree="Thạc sĩ Tâm lý", organization="TT Tham vấn ĐH KH Tự nhiên",
    #                 about="Tập trung vào stress sinh viên, áp lực học tập.")
    #     t2 = Therapist(full_name="TS. Lê Bình", field="Trị liệu gia đình", image="static/therapists/binh.jpg",
    #                 years_exp=9, degree="Tiến sĩ Tâm lý", organization="BV Tâm thần",
    #                 about="Kinh nghiệm xử lý xung đột và lo âu.")

    #     s1 = Student(full_name="Nguyễn Văn A", student_code="2412345", email="a@example.com",
    #                 major="Công nghệ thông tin", school="ĐH KH Tự nhiên")
    #     s2 = Student(full_name="Trần Thị B", student_code="2412346", email="b@example.com",
    #                 major="Tâm lý học", school="ĐH KHXH & NV")

    #     session.add_all([t1, t2, s1, s2])
    #     session.commit()

    # session.close()
    # print(" therapy.db created (v2 with major & school)")