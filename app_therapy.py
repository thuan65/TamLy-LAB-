# app_therapy.py
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Therapist, Student, TherapistRating, StressLog



app = Flask(__name__)
from feedback.feedback import feedback_bp
app.register_blueprint(feedback_bp)

app.config["JSON_AS_ASCII"] = False

engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)

@app.route("/therapists")
def list_therapists():
    q = request.args.get("q", "")
    s = Session()
    if q:
        therapists = s.query(Therapist).filter(Therapist.full_name.like(f"%{q}%")).all()
    else:
        therapists = s.query(Therapist).order_by(Therapist.avg_rating.desc()).all()
    return render_template("therapists.html", therapists=therapists, keyword=q)

@app.route("/therapist/<int:therapist_id>")
def therapist_detail(therapist_id):
    s = Session()
    th = s.query(Therapist).filter_by(id=therapist_id).first()
    if not th:
        return "Không tìm thấy chuyên gia", 404
    ratings = s.query(TherapistRating).filter_by(therapist_id=therapist_id).all()
    return render_template("therapist_detail.html", therapist=th, ratings=ratings)

@app.route("/students")
def list_students():
    s = Session()
    students = s.query(Student).all()
    return render_template("students.html", students=students)

@app.route("/api/rating", methods=["POST"])
def api_rating():
    data = request.get_json()
    student_id = data.get("student_id")
    therapist_id = data.get("therapist_id")
    score = float(data.get("score", 0))
    comment = data.get("comment", "")
    s = Session()
    r = TherapistRating(student_id=student_id, therapist_id=therapist_id, score=score, comment=comment)
    s.add(r)
    s.commit()
    rows = s.query(TherapistRating).filter_by(therapist_id=therapist_id).all()
    avg = sum([x.score for x in rows]) / len(rows)
    th = s.query(Therapist).filter_by(id=therapist_id).first()
    th.avg_rating = avg
    th.rating_count = len(rows)
    s.commit()
    return jsonify({"ok": True, "avg_rating": avg, "rating_count": len(rows)})

@app.route("/api/stresslog", methods=["POST"])
def api_stresslog():
    data = request.get_json()
    student_id = data.get("student_id")
    score = float(data.get("score", 0))
    scale_name = data.get("scale_name", "DASS")
    note = data.get("note", "")
    s = Session()
    log = StressLog(student_id=student_id, score=score, scale_name=scale_name, note=note)
    s.add(log)
    stu = s.query(Student).filter_by(id=student_id).first()
    if stu:
        stu.last_stress_score = score
    s.commit()
    return jsonify({"ok": True})

@app.route("/top_therapist")
def top_therapist():
    s = Session()

    # Lấy chuyên gia có avg_rating cao nhất (nếu bằng thì xét rating_count)
    top = (
        s.query(Therapist)
        .order_by(Therapist.avg_rating.desc(), Therapist.rating_count.desc())
        .first()
    )

    if not top:
        return "<h3>Chưa có chuyên gia nào được đánh giá.</h3>"

    html = f"""
    <h2>🏆 Chuyên gia được đánh giá cao nhất</h2>
    <div style='border:1px solid #ccc; padding:20px; max-width:500px; font-family:Arial'>
        <h3>{top.full_name}</h3>
        <p><b>Lĩnh vực:</b> {top.field}</p>
        <p><b>Tổ chức:</b> {top.organization}</p>
        <p><b>Điểm trung bình:</b> ⭐ {round(top.avg_rating, 2)}</p>
        <p><b>Số lượt đánh giá:</b> {top.rating_count}</p>
        <p><b>Kinh nghiệm:</b> {top.years_exp} năm</p>
    </div>
    <br><a href='/therapists'>⬅️ Quay lại danh sách chuyên gia</a>
    """

    s.close()
    return html

if __name__ == "__main__":
    app.run(debug=False)
