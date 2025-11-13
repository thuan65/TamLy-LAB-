from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Therapist, Student, TherapistRating, StressLog

#Test logic đánh giá & stress qua terminal
# -----------------------------
# Kết nối DB
# -----------------------------
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)
session = Session()

# -----------------------------
# 1️⃣ Xếp hạng chuyên gia
# -----------------------------
def ranking():
    print("\n=== 🩺 RANKING CHUYÊN GIA ===")
    therapists = (
        session.query(Therapist)
        .order_by(Therapist.avg_rating.desc(), Therapist.rating_count.desc())
        .all()
    )
    for i, t in enumerate(therapists, start=1):
        print(f"{i}. {t.full_name:25} | Rating: {t.avg_rating:.2f} ({t.rating_count} lượt) | Lĩnh vực: {t.field}")

    # Cho phép người dùng chấm điểm
    try:
        tid = int(input("\n➡️  Nhập ID chuyên gia muốn đánh giá (0 để bỏ qua): "))
        if tid == 0:
            return
        sid = int(input("Nhập ID sinh viên (VD: 1): "))
        score = float(input("Nhập điểm đánh giá (1-5): "))
        comment = input("Nhận xét ngắn gọn: ")

        rating = TherapistRating(student_id=sid, therapist_id=tid, score=score, comment=comment)
        session.add(rating)

        # Cập nhật trung bình
        rows = session.query(TherapistRating).filter_by(therapist_id=tid).all()
        avg = sum([r.score for r in rows]) / len(rows)
        th = session.query(Therapist).filter_by(id=tid).first()
        th.avg_rating = avg
        th.rating_count = len(rows)
        session.commit()

        print(f"✅ Đã ghi đánh giá mới! Trung bình hiện tại: {avg:.2f} ({len(rows)} lượt).")
    except Exception as e:
        session.rollback()
        print(f"❌ Lỗi: {e}")

# -----------------------------
# 2️⃣ Ghi nhận & thống kê stress
# -----------------------------
def stress_log():
    print("\n=== 🧠 GHI NHẬN MỨC STRESS ===")
    try:
        sid = int(input("Nhập ID sinh viên: "))
        score = float(input("Điểm stress (0-42): "))
        scale = input("Tên thang đo (mặc định DASS): ") or "DASS"
        note = input("Ghi chú thêm: ")

        log = StressLog(student_id=sid, score=score, scale_name=scale, note=note)
        session.add(log)

        stu = session.query(Student).filter_by(id=sid).first()
        if stu:
            stu.last_stress_score = score
        session.commit()

        print("✅ Đã ghi nhận stress log!")

        # Thống kê nhanh
        avg = session.query(func.avg(StressLog.score)).scalar()
        max_score = session.query(func.max(StressLog.score)).scalar()
        total = session.query(StressLog).count()
        print(f"\n📊 Tổng log: {total}")
        print(f"📈 Trung bình stress: {avg:.2f}")
        print(f"🚨 Mức cao nhất: {max_score:.2f}")
    except Exception as e:
        session.rollback()
        print(f"❌ Lỗi: {e}")

# -----------------------------
# MAIN MENU
# -----------------------------
def main():
    while True:
        print("\n==============================")
        print("🧭 MENU TEST CHỨC NĂNG")
        print("1. Xếp hạng & đánh giá chuyên gia")
        print("2. Ghi nhận & thống kê mức stress")
        print("0. Thoát")
        choice = input("Chọn chức năng (0-2): ").strip()

        if choice == "1":
            ranking()
        elif choice == "2":
            stress_log()
        elif choice == "0":
            print("👋 Thoát chương trình.")
            break
        else:
            print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()
