# =======================
# quiz_routes.py (Blueprint)
# =======================

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_cors import CORS
from models import User, StressLog
from quiz.LogicDiem import (
    CAU_HOI,
    TAN_SUAT,
    ANH_HUONG,
    tinh_muc_do,
    tao_loi_khuyen,
)


# --------------------------------------
# Tạo Blueprint tên mới: quiz_bp
# --------------------------------------
quiz_bp = Blueprint(
    "quiz_bp",
    __name__,
    url_prefix="/quiz", template_folder="htmltemplates"
)

# Enable CORS cho blueprint
CORS(quiz_bp)

# Database
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)

# ======================================================================
# PHẦN 1: DỮ LIỆU CÂU HỎI PHQ-9
# ======================================================================

CAU_HOI = [
    "Ít hứng thú hoặc không thích thú khi làm các việc hàng ngày",
    "Cảm thấy buồn bã, chán nản hoặc tuyệt vọng",
    "Khó ngủ, ngủ nông hoặc ngủ quá nhiều",
    "Cảm thấy mệt mỏi hoặc thiếu năng lượng",
    "Kém ăn hoặc ăn quá nhiều",
    "Cảm thấy bản thân là kẻ thất bại hoặc làm phiền người khác",
    "Khó tập trung vào công việc hoặc việc học",
    "Cử động hoặc nói chậm lại; hoặc bồn chồn, không thể ngồi yên",
    "Nghĩ rằng thà mình chết đi hoặc muốn tự làm đau bản thân",
    "Những khó khăn trên đã ảnh hưởng đến học tập, công việc hoặc các sinh hoạt thường ngày?"
]

TAN_SUAT = ["Không bao giờ", "Vài ngày", "Hơn một nửa số ngày", "Gần như mỗi ngày"]
ANH_HUONG = ["Không gây ảnh hưởng", "Có chút ảnh hưởng", "Hơi khó khăn", "Rất khó khăn"]

def phan_tich_chi_tiet(tra_loi):
    """
    Phân tích chi tiết các câu trả lời
    Đặc biệt cảnh báo nếu câu 9 (ý nghĩ tự hại) > 0
    
    Returns:
        dict: Phân tích chi tiết và cảnh báo (nếu có)
    """
    phan_tich = {
        "tam_trang": tra_loi[0] + tra_loi[1],  # Câu 1, 2
        "giac_ngu": tra_loi[2],                # Câu 3
        "nang_luong": tra_loi[3],              # Câu 4
        "an_uong": tra_loi[4],                 # Câu 5
        "tu_danh_gia": tra_loi[5],            # Câu 6
        "tap_trung": tra_loi[6],               # Câu 7
        "van_dong": tra_loi[7],                # Câu 8
        "nguy_hiem": tra_loi[8]                # Câu 9: Ý nghĩ tự hại
    }
    
    # Cảnh báo đặc biệt nếu câu 9 > 0
    if phan_tich["nguy_hiem"] > 0:
        phan_tich["canh_bao"] = "⚠️ CẢNH BÁO: Có dấu hiệu ý nghĩ tự hại. Cần hỗ trợ khẩn cấp!"
    
    return phan_tich
# ======================================================================
# PHẦN 3: ROUTES
# ======================================================================

@quiz_bp.route("/")
def trang_quiz():
    return render_template("quiz.html")


@quiz_bp.get("/lay-cau-hoi")
def lay_cau_hoi():
    return jsonify({
        "success": True,
        "cau_hoi": CAU_HOI,
        "tan_suat": TAN_SUAT,
        "anh_huong": ANH_HUONG
    })


@quiz_bp.post("/nop-bai")
def nop_bai():
    try:
        data = request.json
        ho_ten = data.get("ho_ten", "").strip()
        mssv = data.get("mssv", "").strip()
        tra_loi = data.get("tra_loi", [])
        anh_huong_chon = data.get("anh_huong", 0)

        if not ho_ten or not mssv:
            return jsonify({"success": False, "message": "Thiếu thông tin"}), 400

        if len(tra_loi) < 10:
            return jsonify({"success": False, "message": "Chưa trả lời đủ câu hỏi"}), 400

        tong_diem = sum(tra_loi)
        muc_do, loai, icon = tinh_muc_do(tong_diem)
        loi_khuyen, hanh_dong = tao_loi_khuyen(tong_diem, muc_do)
        phan_tich = phan_tich_chi_tiet(tra_loi)

        s = Session()

        student = s.query(User).filter_by(student_code=mssv).first()
        if not student:
            student = User(full_name=ho_ten, student_code=mssv, last_stress_score=tong_diem)
            s.add(student)
            s.commit()
        else:
            student.last_stress_score = tong_diem
            s.commit()

        note = f"Ảnh hưởng: {ANH_HUONG[anh_huong_chon]}"
        if "canh_bao" in phan_tich:
            note += f" | {phan_tich['canh_bao']}"

        log = StressLog(student_id=student.id, score=tong_diem, scale_name="PHQ-9", note=note)
        s.add(log)
        s.commit()

        student_id = student.id  #luu truoc khi dong session
        s.close()

        return jsonify({
            "success": True,
            "diem": tong_diem,
            "muc_do": muc_do,
            "icon": icon,
            "loai": loai,
            "loi_khuyen": loi_khuyen,
            "hanh_dong": hanh_dong,
            "anh_huong_text": ANH_HUONG[anh_huong_chon],
            "student_id": student.id,
            "canh_bao": phan_tich.get("canh_bao")
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@quiz_bp.get("/lich-su/<int:student_id>")
def lich_su(student_id):
    s = Session()
    logs = (
        s.query(StressLog)
        .filter_by(student_id=student_id)
        .order_by(StressLog.created_at.desc())
        .all()
    )

    result = []
    for log in logs:
        muc_do, _, icon = tinh_muc_do(log.score)
        result.append({
            "thoi_gian": log.created_at,
            "diem": log.score,
            "muc_do": muc_do,
            "icon": icon,
            "note": log.note
        })

    s.close()
    return jsonify({"success": True, "lich_su": result})
