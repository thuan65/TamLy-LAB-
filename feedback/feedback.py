from flask import Blueprint, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Therapist

feedback_bp = Blueprint(
    "feedback",
    __name__,
    template_folder="templates",
    url_prefix="/feedback"
)

# --- Kết nối DB ---
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)

# --- Route feedback ---
@feedback_bp.route("/<int:therapist_id>", methods=["GET"])
def feedback(therapist_id):
    """Hiển thị trang landing để mở Google Form đánh giá"""
    s = Session()
    th = s.query(Therapist).filter_by(id=therapist_id).first()
    
    if not th:
        s.close()
        return "Không tìm thấy chuyên gia", 404
    
    s.close()
    return render_template("feedback.html", therapist=th)

