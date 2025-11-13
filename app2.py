from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from quiz.LogicDiem import tinh_muc_do, tao_loi_khuyen, CAU_HOI, TAN_SUAT, ANH_HUONG
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from createTherapyDB import Student, StressLog

app = Flask(__name__, template_folder="quiz/templates", static_folder="quiz/static")
CORS(app)

ket_qua_luu = []

@app.route('/')
def trang_chu():
    return render_template('quiz_mentalHealth.html')

@app.route('/api/lay-cau-hoi', methods=['GET'])
def lay_cau_hoi():
    return jsonify({
        'success': True,
        'cau_hoi': CAU_HOI,
        'tan_suat': TAN_SUAT,
        'anh_huong': ANH_HUONG
    })

@app.route("/api/nop-bai", methods=["POST"])
def nop_bai():
    data = request.get_json()

    try:
        engine = create_engine("sqlite:///therapy.db")
        Session = sessionmaker(bind=engine)
        s = Session()

        student_name = data.get("ho_ten", "").strip()
        student_code = data.get("mssv", "").strip()
        score = data.get("diem", 0)

        from createTherapyDB import Student, StressLog
        stu = s.query(Student).filter_by(student_code=student_code).first()
        if not stu:
            stu = Student(full_name=student_name or "Ẩn danh", student_code=student_code)
            s.add(stu)
            s.commit()

        log = StressLog(student_id=stu.id, score=score, scale_name="PHQ-9", note="Kết quả quiz PHQ-9")
        s.add(log)
        stu.last_stress_score = score
        s.commit()

        s.close()
        print(f"✅ Đã lưu điểm stress của {student_name} ({student_code}): {score}")

        # 🧠 Trả phản hồi JSON cho frontend
        return jsonify({
    "success": True,
    "msg": f"✅ Đã nộp form thành công! Điểm của {student_name or 'Ẩn danh'} ({student_code or 'N/A'}): {score}",
    "diem": score,
    "muc_do": tinh_muc_do(score)[0],  # Lấy mô tả mức độ từ LogicDiem
    "loi_khuyen": tao_loi_khuyen(score, tinh_muc_do(score)[0]),
    "anh_huong_text": "Tự động ghi nhận từ kết quả quiz"  # hoặc bạn có thể gửi giá trị thực nếu có
})



    except Exception as e:
        print("⚠️ Lỗi khi ghi vào therapy.db:", e)
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/lich-su', methods=['GET'])
def lich_su():
    return jsonify({'success': True, 'lich_su': ket_qua_luu})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
