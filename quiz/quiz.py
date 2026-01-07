# =======================
# quiz_routes.py (Blueprint)
# =======================

from flask import Blueprint, request, jsonify, render_template, session
from datetime import datetime
from flask_cors import CORS
from database import TherapySession
from models import User, StudentProfile, StressLog
from quiz.LogicDiem import (
    CAU_HOI,
    TAN_SUAT,
    ANH_HUONG,
    tinh_muc_do,
    tao_loi_khuyen,
)


# --------------------------------------
# Tạo Blueprint
# --------------------------------------
quiz_bp = Blueprint(
    "quiz_bp",
    __name__,
    url_prefix="/quiz", 
    template_folder="htmltemplates"
)

# Enable CORS
CORS(quiz_bp)


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
        "nguy_hiem": tra_loi[8]                # Câu 9: ý nghĩ tự hại
    }
    
    # Cảnh báo đặc biệt nếu câu 9 > 0
    if phan_tich["nguy_hiem"] > 0:
        phan_tich["canh_bao"] = "CẢNH BÁO: Có dấu hiệu ý nghĩ tự hại. Cần hỗ trợ khẩn cấp!"
    
    return phan_tich


# ======================================================================
# ROUTES
# ======================================================================

@quiz_bp.route("/")
def trang_quiz():
    """Hiển thị trang quiz"""
    return render_template("quiz.html")


@quiz_bp.get("/lay-cau-hoi")
def lay_cau_hoi():
    """API lấy danh sách câu hỏi"""
    return jsonify({
        "success": True,
        "cau_hoi": CAU_HOI,
        "tan_suat": TAN_SUAT,
        "anh_huong": ANH_HUONG
    })


@quiz_bp.post("/nop-bai")
def nop_bai():
    """API nộp bài quiz và lưu kết quả"""
    try:
        data = request.json
        ho_ten = data.get("ho_ten", "").strip()
        username = data.get("username", "").strip() 
        tra_loi = data.get("tra_loi", [])
        anh_huong_chon = data.get("anh_huong", 0)

        # Validation
        if not ho_ten or not username:
            return jsonify({
                "success": False, 
                "message": "Thiếu thông tin họ tên hoặc tên đăng nhập"
            }), 400

        if len(tra_loi) < 9: 
            return jsonify({
                "success": False, 
                "message": "Chưa trả lời đủ câu hỏi"
            }), 400

        # Tính điểm và phân tích
        tong_diem = sum(tra_loi)
        muc_do, loai, _ = tinh_muc_do(tong_diem)  # Bỏ icon
        loi_khuyen, hanh_dong = tao_loi_khuyen(tong_diem, muc_do)
        phan_tich = phan_tich_chi_tiet(tra_loi)

        # Lưu vào database
        with TherapySession() as s:
            # Tìm hoặc tạo User
            user = s.query(User).filter_by(username=username).first()
            
            if not user:
                # Tạo user mới với role student
                user = User(
                    username=username,
                    password="",
                    role="student"
                )
                s.add(user)
                s.flush()
                
                # Tạo StudentProfile
                student_profile = StudentProfile(
                    user_id=user.id,
                    full_name=ho_ten,
                    last_stress_score=tong_diem
                )
                s.add(student_profile)
            else:
                # Update StudentProfile nếu đã tồn tại
                if user.student_profile:
                    user.student_profile.last_stress_score = tong_diem
                    user.student_profile.full_name = ho_ten
                else:
                    # Tạo StudentProfile nếu user chưa có
                    student_profile = StudentProfile(
                        user_id=user.id,
                        full_name=ho_ten,
                        last_stress_score=tong_diem
                    )
                    s.add(student_profile)

            # Tạo note
            note = f"Ảnh hưởng: {ANH_HUONG[anh_huong_chon]}"
            if "canh_bao" in phan_tich:
                note += f" | {phan_tich['canh_bao']}"

            # Lưu StressLog
            log = StressLog(
                student_id=user.id,
                score=tong_diem, 
                scale_name="STRESS_TEST",  # Đổi từ PHQ-9
                note=note
            )
            s.add(log)
            s.commit()

            user_id = user.id

        return jsonify({
            "success": True,
            "diem": tong_diem,
            "muc_do": muc_do,
            "loai": loai,
            "loi_khuyen": loi_khuyen,
            "hanh_dong": hanh_dong,
            "anh_huong_text": ANH_HUONG[anh_huong_chon],
            "user_id": user_id,
            "canh_bao": phan_tich.get("canh_bao"),
            "message": "Đã lưu kết quả thành công!"
        })

    except Exception as e:
        print(f"ERROR in nop_bai: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"Lỗi server: {str(e)}"
        }), 500


@quiz_bp.get("/lich-su/<int:user_id>")
def lich_su(user_id):
    """API lấy lịch sử làm quiz của user"""
    try:
        with TherapySession() as s:
            # Kiểm tra user có tồn tại
            user = s.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    "success": False, 
                    "message": "Không tìm thấy người dùng"
                }), 404

            # Lấy danh sách logs
            logs = (
                s.query(StressLog)
                .filter_by(student_id=user_id)
                .order_by(StressLog.created_at.desc())
                .all()
            )

            result = []
            for log in logs:
                muc_do, _, icon_emoticon = tinh_muc_do(log.score)
                
                # Parse created_at (format ISO string)
                try:
                    if isinstance(log.created_at, str):
                        dt = datetime.fromisoformat(log.created_at)
                        thoi_gian = dt.strftime("%d/%m/%Y %H:%M")
                    else:
                        thoi_gian = log.created_at.strftime("%d/%m/%Y %H:%M")
                except:
                    thoi_gian = log.created_at if log.created_at else "N/A"
                
                result.append({
                    "thoi_gian": thoi_gian,
                    "diem": log.score,
                    "muc_do": muc_do,
                    "icon": icon_emoticon,
                    "note": log.note or "",
                    "scale_name": log.scale_name or "STRESS_TEST"
                })

            return jsonify({
                "success": True, 
                "lich_su": result,
                "user_name": user.username,
                "full_name": user.student_profile.full_name if user.student_profile else ""
            })
    
    except Exception as e:
        print(f"ERROR in lich_su: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False, 
            "message": f"Lỗi server: {str(e)}"
        }), 500


@quiz_bp.get("/lich-su")
def lich_su_current_user():
    """API lấy lịch sử của user đang đăng nhập"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({
            "success": False,
            "message": "Vui lòng đăng nhập để xem lịch sử"
        }), 401
    
    return lich_su(user_id)
