from flask import Blueprint, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Therapist, TherapistRating, Student

feedback_bp = Blueprint(
    "feedback",
    __name__,
    template_folder="templates",
    static_folder="../static"
)

# --- Kết nối DB ---
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)

# --- Route feedback ---
@feedback_bp.route("/feedback/<int:therapist_id>", methods=["GET", "POST"])
def feedback(therapist_id):
    s = Session()
    th = s.query(Therapist).filter_by(id=therapist_id).first()
    if not th:
        return "❌ Không tìm thấy chuyên gia", 404

    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        student_code = request.form.get("student_code", "").strip()

        # === Tìm hoặc thêm sinh viên mới ===
        stu = None
        if student_code:
            stu = s.query(Student).filter_by(student_code=student_code).first()
            if not stu:
                stu = Student(full_name=student_name or "Ẩn danh", student_code=student_code)
                s.add(stu)
                s.commit()

        # === Lấy điểm và nhận xét 5 câu ===
        scores = []
        comments = []
        for i in range(1, 6):
            score_val = request.form.get(f"q{i}_score")
            comment_val = request.form.get(f"q{i}_comment", "")
            if score_val:
                scores.append(int(score_val))
            comments.append(comment_val.strip())

        if len(scores) == 0:
            return "⚠️ Bạn chưa chấm điểm", 400

        avg_score = sum(scores) / len(scores)
        combined_comments = " | ".join(
            [f"C{i}: {c}" for i, c in enumerate(comments, start=1) if c]
        )

        # === Thêm record vào TherapistRating ===
        fb = TherapistRating(
            student_id=stu.id if stu else None,
            therapist_id=therapist_id,
            score=avg_score,
            comment=combined_comments
        )
        s.add(fb)
        s.commit()

        # === Cập nhật điểm trung bình của therapist ===
        rows = s.query(TherapistRating).filter_by(therapist_id=therapist_id).all()
        avg = sum(r.score for r in rows) / len(rows)
        th.avg_rating = round(avg, 2)
        th.rating_count = len(rows)
        s.commit()

        therapist_name = th.full_name
        s.close()
        return f"""
        <h3>Cảm ơn bạn đã đánh giá chuyên gia {therapist_name}!</h3>
        <p>Điểm trung bình bạn chấm: <b>{avg_score:.2f}</b> ⭐</p>
        <a href="/therapists">⬅️ Quay lại danh sách chuyên gia</a>
        """
    s.close()
    return render_template("feedback.html", therapist=th)
