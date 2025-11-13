from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Therapist, TherapistRating

# --- Kết nối DB ---
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)
s = Session()

# --- Xóa toàn bộ feedback ---
deleted = s.query(TherapistRating).delete()
print(f"🗑️ Đã xóa {deleted} bản ghi feedback.")

# --- Reset điểm trung bình & số lượt đánh giá ---
therapists = s.query(Therapist).all()
for t in therapists:
    t.avg_rating = 0.0
    t.rating_count = 0
print(f"🔁 Đặt lại {len(therapists)} chuyên gia về điểm 0.")

s.commit()
s.close()
print("✅ Hoàn tất reset rating.")
