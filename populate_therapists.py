# populate_therapists.py
import os
import random
from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = "therapy.db"

# 1) XÓA DB CŨ TRƯỚC KHI TẠO ENGINE
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"🗑️ Đã xóa database cũ: {DB_PATH}")

# 2) TẠO ENGINE + BASE + SESSION
engine = create_engine(f"sqlite:///{DB_PATH}")
Base = declarative_base()

# 3) KHAI BÁO MODEL
class Therapist(Base):
    __tablename__ = "therapists"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    field = Column(String)
    image = Column(String)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    years_exp = Column(Integer, default=0)
    degree = Column(String)
    organization = Column(String)
    cv_link = Column(String)
    about = Column(Text)
    is_active = Column(Integer, default=1)

# 4) TẠO BẢNG
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 5) SINH DỮ LIỆU
fake = Faker("vi_VN")
fields = ["Trầm cảm", "Lo âu", "Stress", "Tư vấn học đường", "Gia đình", "Tâm lý hành vi"]
degrees = ["Cử nhân", "Thạc sĩ", "Tiến sĩ"]
orgs = [
    "TT Tâm lý HCM",
    "BV Tâm thần TW",
    "ĐH KHXH&NV",
    "Phòng khám Hy Vọng",
    "Trung tâm Tham vấn Q1",
]

therapists = []
for i in range(10):  # đổi số ở đây nếu muốn ít / nhiều hơn
    t = Therapist(
        full_name=fake.name(),
        field=random.choice(fields),
        image=f"static/therapists/default_{random.randint(1,3)}.jpg",
        years_exp=random.randint(1, 20),
        degree=random.choice(degrees),
        organization=random.choice(orgs),
        cv_link="",
        about=fake.text(max_nb_chars=120),
        avg_rating=round(random.uniform(3.5, 5.0), 2),
        rating_count=random.randint(5, 50),
    )
    therapists.append(t)

session.add_all(therapists)
session.commit()

print(f"✅ Đã tạo mới database '{DB_PATH}' và thêm {len(therapists)} chuyên gia.")

# 6) IN THỬ
print("\n🏆 TOP THERAPISTS (SORTED BY RATING):")
for t in session.query(Therapist).order_by(Therapist.avg_rating.desc()).limit(5):
    print(f"- {t.full_name} | ⭐ {t.avg_rating:.2f} | {t.field} | {t.organization}")


session.close()
