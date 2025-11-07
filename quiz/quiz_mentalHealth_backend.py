from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Dữ liệu câu hỏi
CAU_HOI = [
    "Ít hứng thú hoặc không thích thú khi làm các việc hàng ngày",
    "Cảm thấy buồn bã, chán nản hoặc tuyệt vọng",
    "Khó ngủ, ngủ nông hoặc ngủ quá nhiều",
    "Cảm thấy mệt mỏi hoặc thiếu năng lượng",
    "Kém ăn hoặc ăn quá nhiều",
    "Cảm thấy bản thân là kẻ thất bại hoặc làm phiền người khác",
    "Khó tập trung vào công việc hoặc việc học",
    "Cử động hoặc nói chậm lại; hoặc bồn chồn, không thể ngồi yên",
    "Nghĩ rằng thà mình chết đi hoặc muốn tự làm đau bản thân"
]

TAN_SUAT = [
    "Không bao giờ",
    "Vài ngày",
    "Hơn một nửa số ngày",
    "Gần như mỗi ngày"
]

ANH_HUONG = [
    "Không gây ảnh hưởng",
    "Có chút ảnh hưởng",
    "Hơi khó khăn",
    "Rất khó khăn"
]

# Lưu trữ kết quả tạm
ket_qua_luu = []

def tinh_muc_do(diem):
    """Tính mức độ dựa trên tổng điểm"""
    if diem <= 4:
        return "Không/Ít triệu chứng", "success"
    elif diem <= 9:
        return "Nhẹ", "info"
    elif diem <= 14:
        return "Trung bình", "warning"
    elif diem <= 19:
        return "Tương đối nặng", "danger"
    else:
        return "Nặng", "danger"

def tao_loi_khuyen(diem, muc_do):
    """Tạo lời khuyên dựa trên kết quả"""
    loi_khuyen = []
    
    if diem <= 4:
        loi_khuyen.append("Bạn đang có tâm trạng tốt! Hãy duy trì lối sống tích cực.")
        loi_khuyen.append("Tiếp tục tập thể dục đều đặn và giữ kết nối với bạn bè.")
    elif diem <= 9:
        loi_khuyen.append("Bạn có một số triệu chứng nhẹ. Hãy chú ý chăm sóc sức khỏe tinh thần.")
        loi_khuyen.append("Thử áp dụng các kỹ thuật thư giãn như thiền, yoga.")
        loi_khuyen.append("Chia sẻ cảm xúc với người thân hoặc bạn bè.")
    elif diem <= 14:
        loi_khuyen.append("Bạn có triệu chứng ở mức trung bình. Nên cân nhắc tìm sự hỗ trợ.")
        loi_khuyen.append("Liên hệ với tư vấn viên tâm lý tại trường.")
        loi_khuyen.append("Xây dựng thói quen sinh hoạt lành mạnh hơn.")
    else:
        loi_khuyen.append("Bạn có triệu chứng nghiêm trọng. Hãy tìm kiếm sự hỗ trợ chuyên môn ngay.")
        loi_khuyen.append("Liên hệ với chuyên gia tâm lý hoặc bác sĩ càng sớm càng tốt.")
        loi_khuyen.append("Đừng ngần ngại chia sẻ với người thân để được hỗ trợ.")
        loi_khuyen.append("Hotline hỗ trợ tâm lý: xxxx-xxxx (có thể gọi 24/7)")
    
    return loi_khuyen

@app.route('/')
def trang_chu():
    """Render trang chủ"""
    return render_template('mental_health_quiz.html')

@app.route('/api/lay-cau-hoi', methods=['GET'])
def lay_cau_hoi():
    """API lấy danh sách câu hỏi"""
    return jsonify({
        'success': True,
        'cau_hoi': CAU_HOI,
        'tan_suat': TAN_SUAT,
        'anh_huong': ANH_HUONG
    })

@app.route('/api/nop-bai', methods=['POST'])
def nop_bai():
    """API nhận và xử lý kết quả bài test"""
    try:
        data = request.json
        tra_loi = data.get('tra_loi', [])
        anh_huong_chon = data.get('anh_huong', 0)
        
        # Kiểm tra dữ liệu
        if len(tra_loi) != 9:
            return jsonify({
                'success': False,
                'message': 'Vui lòng trả lời đầy đủ 9 câu hỏi'
            }), 400
        
        # Tính tổng điểm
        tong_diem = sum(tra_loi)
        
        # Xác định mức độ
        muc_do, loai = tinh_muc_do(tong_diem)
        
        # Tạo lời khuyên
        loi_khuyen = tao_loi_khuyen(tong_diem, muc_do)
        
        # Lưu kết quả
        ket_qua = {
            'thoi_gian': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'diem': tong_diem,
            'muc_do': muc_do,
            'tra_loi': tra_loi,
            'anh_huong': anh_huong_chon
        }
        ket_qua_luu.append(ket_qua)
        
        return jsonify({
    'success': True,
    'msg': '✅ Đã nộp form thành công!',
    'diem': tong_diem,
    'muc_do': muc_do,
    'loai': loai,
    'loi_khuyen': loi_khuyen,
    'anh_huong_text': ANH_HUONG[anh_huong_chon]
})

        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi xử lý: {str(e)}'
        }), 500

@app.route('/api/lich-su', methods=['GET'])
def lich_su():
    """API lấy lịch sử làm bài"""
    return jsonify({
        'success': True,
        'lich_su': ket_qua_luu
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)