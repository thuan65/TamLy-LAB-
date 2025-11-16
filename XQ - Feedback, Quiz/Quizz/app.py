from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
from LogicDiem import tinh_muc_do, tao_loi_khuyen, CAU_HOI, TAN_SUAT, ANH_HUONG

app = Flask(__name__)
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

@app.route('/api/nop-bai', methods=['POST'])
def nop_bai():
    try:
        data = request.json
        tra_loi = data.get('tra_loi', [])
        anh_huong_chon = data.get('anh_huong', 0)

        if len(tra_loi) != 9:
            return jsonify({'success': False, 'message': 'Vui lòng trả lời đầy đủ 10 câu'}), 400

        tong_diem = sum(tra_loi)
        muc_do, loai = tinh_muc_do(tong_diem)
        loi_khuyen = tao_loi_khuyen(tong_diem, muc_do)

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
            'diem': tong_diem,
            'muc_do': muc_do,
            'loai': loai,
            'loi_khuyen': loi_khuyen,
            'anh_huong_text': ANH_HUONG[anh_huong_chon]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/lich-su', methods=['GET'])
def lich_su():
    return jsonify({'success': True, 'lich_su': ket_qua_luu})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
