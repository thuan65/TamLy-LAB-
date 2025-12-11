
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Student, StressLog

app = Flask(__name__)
CORS(app)

# Kết nối DB
engine = create_engine("sqlite:///therapy.db")
Session = sessionmaker(bind=engine)

# ============================================================================
# PHẦN 1: DỮ LIỆU CÂU HỎI PHQ-9
# ============================================================================

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
    "Những khó khăn trên đã ảnh hưởng đến học tập, công việc hoặc các sinh hoạt thường ngày của bạn như thế nào?"
]

TAN_SUAT = [
    "Không bao giờ",           # 0 điểm
    "Vài ngày",                # 1 điểm
    "Hơn một nửa số ngày",     # 2 điểm
    "Gần như mỗi ngày"         # 3 điểm
]

ANH_HUONG = [
    "Không gây ảnh hưởng",
    "Có chút ảnh hưởng",
    "Hơi khó khăn",
    "Rất khó khăn"
]

# ============================================================================
# PHẦN 2: LOGIC TÍNH ĐIỂM VÀ KHUYẾN NGHỊ
# ============================================================================

def tinh_muc_do(diem):
    """
    Xác định mức độ dựa trên tổng điểm PHQ-9 (0-27)
    
    Returns:
        tuple: (mô tả mức độ, loại bootstrap, icon)
    """
    if diem <= 4:
        return "Không/Ít triệu chứng", "success", "🟢"
    elif diem <= 9:
        return "Nhẹ", "info", "🟡"
    elif diem <= 14:
        return "Trung bình", "warning", "🟠"
    elif diem <= 19:
        return "Tương đối nặng", "danger", "🔴"
    else:
        return "Nặng", "danger", "🔴"

def tao_loi_khuyen(diem, muc_do):
    """
    Tạo danh sách lời khuyên và hành động dựa trên kết quả
    
    Returns:
        tuple: (danh sách lời khuyên, danh sách hành động)
    """
    loi_khuyen = []
    hanh_dong = []
    
    if diem <= 4:
        # Không/Ít triệu chứng
        loi_khuyen = [
            "🎉 Tuyệt vời! Bạn đang có tâm trạng tốt và ổn định.",
            "💪 Hãy duy trì lối sống tích cực và thói quen lành mạnh.",
            "🤝 Tiếp tục kết nối với bạn bè và gia đình."
        ]
        hanh_dong = [
            "Tiếp tục duy trì các hoạt động thư giãn như yoga, thiền định",
            "Tham gia các câu lạc bộ, hoạt động xã hội tại trường",
            "Chia sẻ kinh nghiệm tích cực với bạn bè",
            "Duy trì thói quen ngủ đủ giấc và ăn uống lành mạnh"
        ]
        
    elif diem <= 9:
        # Triệu chứng nhẹ
        loi_khuyen = [
            "⚠️ Bạn có một số triệu chứng nhẹ về tâm trạng.",
            "🧘 Đây là lúc nên chú ý chăm sóc sức khỏe tinh thần nhiều hơn.",
            "💬 Chia sẻ cảm xúc với người thân sẽ giúp bạn thoải mái hơn.",
            "📚 Tìm hiểu thêm về các kỹ thuật tự chăm sóc."
        ]
        hanh_dong = [
            "Thử các kỹ thuật thư giãn: thiền, yoga, breathing exercises",
            "Xây dựng thói quen ngủ đều đặn (7-8 giờ/đêm)",
            "Viết nhật ký cảm xúc để theo dõi tâm trạng hàng ngày",
            "Tăng cường hoạt động thể chất nhẹ nhàng",
            "Tham khảo tài liệu tự chăm sóc sức khỏe tinh thần"
        ]
        
    elif diem <= 14:
        # Triệu chứng trung bình
        loi_khuyen = [
            "🟠 Bạn có triệu chứng ở mức trung bình - cần quan tâm.",
            "🏥 Nên cân nhắc tìm sự hỗ trợ từ chuyên gia tư vấn.",
            "👨‍⚕️ Đừng ngần ngại, việc tìm kiếm hỗ trợ là dấu hiệu của sự mạnh mẽ.",
            "🤝 Hãy chia sẻ với người thân để được động viên và hỗ trợ."
        ]
        hanh_dong = [
            "📞 Liên hệ tư vấn viên tâm lý tại trường hoặc trung tâm",
            "🏃 Tăng cường hoạt động thể chất (30 phút/ngày)",
            "🥗 Chú ý chế độ ăn uống cân bằng, hạn chế caffeine",
            "👥 Tham gia nhóm hỗ trợ hoặc hoạt động cộng đồng",
            "📱 Xem danh sách chuyên gia tư vấn trong hệ thống",
            "📝 Theo dõi và ghi chép các triệu chứng hàng ngày"
        ]
        
    else:  # diem >= 15
        # Triệu chứng nặng
        loi_khuyen = [
            "🔴 Kết quả cho thấy bạn có triệu chứng nghiêm trọng.",
            "🆘 RẤT KHUYẾN NGHỊ tìm kiếm sự hỗ trợ chuyên môn NGAY.",
            "💚 Bạn không đơn độc - có nhiều người sẵn sàng giúp đỡ bạn.",
            "📞 Đừng chần chừ, hãy liên hệ với chuyên gia hoặc hotline hỗ trợ.",
            "⚠️ Đây là tình huống cần can thiệp chuyên môn."
        ]
        hanh_dong = [
            "🏥 Liên hệ NGAY với chuyên gia tâm lý hoặc bác sĩ tâm thần",
            "📱 Hotline hỗ trợ tâm lý 24/7: 1800-xxxx",
            "👨‍👩‍👧 Chia sẻ với gia đình/người thân để được hỗ trợ NGAY",
            "🚨 Nếu có ý nghĩ tự hại, gọi cấp cứu: 115",
            "💼 Xem danh sách chuyên gia có sẵn trong hệ thống",
            "🏥 Cân nhắc đến cơ sở y tế chuyên khoa tâm thần",
            "⏰ Không trì hoãn - hành động ngay hôm nay"
        ]
    
    return loi_khuyen, hanh_dong

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

# ============================================================================
# PHẦN 3: FLASK ROUTES
# ============================================================================

@app.route('/')
def trang_chu():
    """Render trang quiz đầu vào"""
    return render_template('quiz_mentalHealth.html')

@app.route('/api/lay-cau-hoi', methods=['GET'])
def lay_cau_hoi():
    """API lấy danh sách câu hỏi PHQ-9"""
    return jsonify({
        'success': True,
        'cau_hoi': CAU_HOI,
        'tan_suat': TAN_SUAT,
        'anh_huong': ANH_HUONG
    })

@app.route('/api/nop-bai', methods=['POST'])
def nop_bai():
    try:
        data = request.json
        ho_ten = data.get('ho_ten', '').strip()
        mssv = data.get('mssv', '').strip()
        tra_loi = data.get('tra_loi', [])
        anh_huong_chon = data.get('anh_huong', 0)
        
        # Kiểm tra dữ liệu
        if not ho_ten or not mssv:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập đầy đủ họ tên và MSSV'
            }), 400
            
        if len(tra_loi) != 9:
            return jsonify({
                'success': False,
                'message': 'Vui lòng trả lời đầy đủ 9 câu hỏi'
            }), 400
        
        # Tính tổng điểm (0-27)
        tong_diem = sum(tra_loi)
        
        # Xác định mức độ
        muc_do, loai, icon = tinh_muc_do(tong_diem)
        
        # Tạo lời khuyên
        loi_khuyen, hanh_dong = tao_loi_khuyen(tong_diem, muc_do)
        
        # Phân tích chi tiết
        phan_tich = phan_tich_chi_tiet(tra_loi)
        
        # Lưu vào database
        s = Session()
        
        # Tìm hoặc tạo sinh viên
        student = s.query(Student).filter_by(student_code=mssv).first()
        if not student:
            student = Student(
                full_name=ho_ten,
                student_code=mssv,
                last_stress_score=tong_diem
            )
            s.add(student)
            s.commit()
        else:
            student.last_stress_score = tong_diem
            s.commit()
        
        # Lưu stress log
        note = f"Ảnh hưởng: {ANH_HUONG[anh_huong_chon]}"
        if "canh_bao" in phan_tich:
            note += f" | {phan_tich['canh_bao']}"
        
        log = StressLog(
            student_id=student.id,
            score=tong_diem,
            scale_name="PHQ-9",
            note=note
        )
        s.add(log)
        s.commit()
        s.close()
        
        return jsonify({
            'success': True,
            'msg': 'Đã hoàn thành bài đánh giá!',
            'diem': tong_diem,
            'diem_max': 27,
            'muc_do': muc_do,
            'icon': icon,
            'loai': loai,
            'loi_khuyen': loi_khuyen,
            'hanh_dong': hanh_dong,
            'anh_huong_text': ANH_HUONG[anh_huong_chon],
            'student_id': student.id,
            'canh_bao': phan_tich.get('canh_bao')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi xử lý: {str(e)}'
        }), 500

@app.route('/api/lich-su/<int:student_id>', methods=['GET'])
def lich_su(student_id):
    """API lấy lịch sử làm bài của sinh viên"""
    s = Session()
    logs = s.query(StressLog).filter_by(student_id=student_id).order_by(StressLog.created_at.desc()).all()
    
    result = []
    for log in logs:
        muc_do, _, icon = tinh_muc_do(log.score)
        result.append({
            'thoi_gian': log.created_at,
            'diem': log.score,
            'muc_do': muc_do,
            'icon': icon,
            'scale': log.scale_name,
            'note': log.note
        })
    
    s.close()
    return jsonify({
        'success': True,
        'lich_su': result
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
