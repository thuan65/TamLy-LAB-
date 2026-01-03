# temp_add_experts.py
# Chạy file này để:
# 1) Add therapist/expert thủ công (nhập từ bàn phím)
# 2) Hoặc seed 5+ therapist mẫu vào DB

import os
from datetime import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Import models
from models import User, ExpertProfile

# =========================
# DB CONFIG (tự bắt therapy.db ở cùng folder)
# =========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "therapy.db")
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# =========================
# SEED DATA: 5+ therapist mẫu
# (Sửa thoải mái trước khi chạy)
# =========================
SEED_EXPERTS = [
    {
        "username": "expert_thao",
        "password": "hashed_pw_here",
        "chat_opt_in": True,
        "profile": {
            "full_name": "ThS. Nguyễn Thảo",
            "title": "Tham vấn viên",
            "qualification": "Thạc sĩ Tâm lý học lâm sàng",
            "specialization": "Lo âu, stress học đường, kỹ năng đối phó",
            "organization": "Trung tâm Tham vấn Tâm lý - Đại học",
            "years_of_experience": 5,
            "verification_status": "PENDING",
            "bio": "Hỗ trợ sinh viên vượt qua lo âu và áp lực học tập bằng CBT/psychoeducation, bài tập thực hành theo tuần."
        }
    },
    {
        "username": "expert_khanh",
        "password": "hashed_pw_here",
        "chat_opt_in": True,
        "profile": {
            "full_name": "CN. Lê Khánh",
            "title": "Tham vấn viên",
            "qualification": "Cử nhân Tâm lý học",
            "specialization": "Lo âu xã hội, tự tin, kỹ năng giao tiếp",
            "organization": "CLB Sức khỏe Tinh thần Sinh viên",
            "years_of_experience": 3,
            "verification_status": "PENDING",
            "bio": "Tập trung vào kỹ năng xã hội, luyện tập giao tiếp, xây dựng tự tin qua tình huống cụ thể."
        }
    },
    {
        "username": "expert_huy",
        "password": "hashed_pw_here",
        "chat_opt_in": False,
        "profile": {
            "full_name": "ThS. Trần Minh Huy",
            "title": "Nhà trị liệu",
            "qualification": "Thạc sĩ Tham vấn tâm lý",
            "specialization": "Burnout, quản lý cảm xúc, cân bằng cuộc sống",
            "organization": "MindCare Clinic",
            "years_of_experience": 7,
            "verification_status": "PENDING",
            "bio": "Đồng hành với burnout và căng thẳng kéo dài; ưu tiên kế hoạch nhỏ, đo tiến trình, điều chỉnh thói quen."
        }
    },
    {
        "username": "expert_lam",
        "password": "hashed_pw_here",
        "chat_opt_in": True,
        "profile": {
            "full_name": "TS. Phạm Bảo Lâm",
            "title": "Chuyên gia",
            "qualification": "Tiến sĩ Tâm lý học",
            "specialization": "Trầm cảm, hoảng sợ, lo âu lan tỏa",
            "organization": "Phòng khám An Nhiên",
            "years_of_experience": 11,
            "verification_status": "PENDING",
            "bio": "Làm việc an toàn, cấu trúc rõ ràng; tập trung nhận diện suy nghĩ tự động, tái cấu trúc nhận thức, kỹ thuật giảm hoảng sợ."
        }
    },
    {
        "username": "expert_vy",
        "password": "hashed_pw_here",
        "chat_opt_in": False,
        "profile": {
            "full_name": "BS. CKI Lưu Bảo Vy",
            "title": "Bác sĩ chuyên khoa I",
            "qualification": "CKI Tâm thần",
            "specialization": "Sàng lọc nguy cơ, lo âu, trầm cảm",
            "organization": "Bệnh viện (Khoa Tâm thần)",
            "years_of_experience": 8,
            "verification_status": "PENDING",
            "bio": "Hỗ trợ đánh giá tình trạng và phối hợp hướng can thiệp phù hợp. Ưu tiên sàng lọc nguy cơ và kế hoạch hỗ trợ thực tế."
        }
    },
    # thêm 1 người nữa cho chắc “ít nhất 5”
    {
        "username": "expert_nhi",
        "password": "hashed_pw_here",
        "chat_opt_in": True,
        "profile": {
            "full_name": "ThS. Võ Thanh Nhi",
            "title": "Tham vấn viên",
            "qualification": "Thạc sĩ Tâm lý giáo dục",
            "specialization": "Khủng hoảng tuổi mới lớn, áp lực thành tích, định hướng mục tiêu",
            "organization": "Trung tâm Hỗ trợ Sinh viên",
            "years_of_experience": 6,
            "verification_status": "PENDING",
            "bio": "Tập trung vào kỹ năng tự học, giảm áp lực thành tích, thiết lập mục tiêu học tập và thói quen bền vững."
        }
    },
]


# =========================
# HELPERS
# =========================
def ensure_db_exists():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Không thấy therapy.db tại: {DB_PATH}")

def get_user_by_username(db, username: str):
    return db.execute(select(User).where(User.username == username)).scalar_one_or_none()

def create_expert(db, username: str, password: str, chat_opt_in: bool, profile: dict):
    # Nếu username đã tồn tại -> báo và skip
    existing = get_user_by_username(db, username)
    if existing:
        print(f"⚠️  Username '{username}' đã tồn tại (user_id={existing.id}) -> skip")
        return None

    user = User(
        username=username,
        password=password,
        role="expert",
        chat_opt_in=bool(chat_opt_in),
        is_online=False,
        last_seen=datetime.now(),
    )
    db.add(user)
    db.flush()  # lấy user.id ngay

    expert_profile = ExpertProfile(
        user_id=user.id,
        full_name=profile.get("full_name", "").strip() or "Unnamed Expert",
        title=profile.get("title"),
        qualification=profile.get("qualification"),
        specialization=profile.get("specialization"),
        organization=profile.get("organization"),
        years_of_experience=profile.get("years_of_experience"),
        verification_status=profile.get("verification_status", "PENDING"),
        bio=profile.get("bio"),
        is_active=profile.get("is_active", True),
    )
    db.add(expert_profile)

    print(f"✅ Added expert: {username} (user_id={user.id}) - {expert_profile.full_name}")
    return user.id

def seed_experts():
    ensure_db_exists()
    db = SessionLocal()
    try:
        count = 0
        for item in SEED_EXPERTS:
            user_id = create_expert(
                db=db,
                username=item["username"],
                password=item.get("password", "hashed_pw_here"),
                chat_opt_in=item.get("chat_opt_in", False),
                profile=item["profile"],
            )
            if user_id:
                count += 1

        db.commit()
        print(f"\n🎉 Seed xong. Thêm mới: {count} expert_profiles.")
    except Exception as e:
        db.rollback()
        print("❌ Lỗi seed:", e)
        raise
    finally:
        db.close()

def add_expert_manual():
    """
    Nhập thủ công 1 therapist/expert rồi insert vào DB
    """
    ensure_db_exists()
    print("\n=== ADD EXPERT MANUAL ===")
    username = input("username (unique): ").strip()
    password = input("password (hash hay raw tuỳ bạn): ").strip() or "hashed_pw_here"
    chat_opt_in = input("chat_opt_in? (y/n): ").strip().lower() == "y"

    full_name = input("full_name: ").strip()
    title = input("title (vd: Giảng viên / Tham vấn viên): ").strip() or None
    qualification = input("qualification (vd: ThS/TS/CKI...): ").strip() or None
    specialization = input("specialization (vd: Lo âu, stress...): ").strip() or None
    organization = input("organization: ").strip() or None

    years_raw = input("years_of_experience (number): ").strip()
    years_of_experience = int(years_raw) if years_raw.isdigit() else None

    verification_status = input("verification_status (PENDING/APPROVED/REJECTED): ").strip().upper() or "PENDING"
    bio = input("bio (mô tả ngắn): ").strip() or None

    db = SessionLocal()
    try:
        user_id = create_expert(
            db=db,
            username=username,
            password=password,
            chat_opt_in=chat_opt_in,
            profile=dict(
                full_name=full_name,
                title=title,
                qualification=qualification,
                specialization=specialization,
                organization=organization,
                years_of_experience=years_of_experience,
                verification_status=verification_status,
                bio=bio,
                is_active=True,
            ),
        )
        if user_id:
            db.commit()
            print("✅ Commit OK.")
        else:
            db.rollback()
            print("ℹ️ Không thêm mới (do trùng username).")
    except Exception as e:
        db.rollback()
        print("❌ Lỗi add manual:", e)
        raise
    finally:
        db.close()

def list_experts(limit=50):
    ensure_db_exists()
    db = SessionLocal()
    try:
        rows = db.execute(
            select(User.id, User.username, ExpertProfile.full_name, ExpertProfile.specialization, ExpertProfile.verification_status)
            .join(ExpertProfile, ExpertProfile.user_id == User.id)
            .where(User.role == "expert")
            .order_by(User.id.desc())
            .limit(limit)
        ).all()

        print("\n=== EXPERT LIST ===")
        for r in rows:
            print(f"- id={r.id} | {r.username} | {r.full_name} | {r.specialization} | {r.verification_status}")
        print(f"Total shown: {len(rows)}")
    finally:
        db.close()


# =========================
# MAIN MENU
# =========================
if __name__ == "__main__":
    print(f"DB: {DB_PATH}")
    print("1) Seed 5+ therapist mẫu")
    print("2) Add therapist thủ công (nhập tay)")
    print("3) List therapist/expert đang có")
    choice = input("Chọn (1/2/3): ").strip()

    if choice == "1":
        seed_experts()
    elif choice == "2":
        add_expert_manual()
    elif choice == "3":
        list_experts()
    else:
        print("Bye.")
