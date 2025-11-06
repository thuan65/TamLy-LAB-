# app.py
from flask import Flask, request, jsonify, render_template
from models import db, ConversationHistory
import os

# --- 1. Khởi tạo và Cấu hình App ---
app = Flask(__name__)

# Cấu hình đường dẫn cho database SQLite
# Nó sẽ tạo file history.db trong thư mục 'instance'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'history.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Khởi tạo database với app
db.init_app(app)

# Tạo thư mục 'instance' nếu chưa có
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Tạo database tables trước khi chạy request đầu tiên
@app.before_request
def create_tables():
    # Sử dụng app_context để đảm bảo db hoạt động đúng
    with app.app_context():
        db.create_all()

# --- 2. API Endpoints (Theo thiết kế của bạn) ---

@app.route('/api/save_history', methods=['POST'])
def save_history():
    """
    API để lưu một cặp tin nhắn (user và system) vào database.
    """
    data = request.json
    
    try:
        # Lấy dữ liệu từ JSON request
        user_id = data['user_id']
        session_type = data['session_type'] # 'chatbot' hoặc 'expert'
        user_message = data.get('user_message') # .get để tránh lỗi nếu key không có
        system_response = data.get('system_response')

        # Tạo bản ghi mới
        new_record = ConversationHistory(
            user_id=user_id,
            session_type=session_type,
            user_message=user_message,
            system_response=system_response
        )
        print(new_record)
        # Thêm vào session và commit
        db.session.add(new_record)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'History saved', 'record_id': new_record.id}), 201
    
    except KeyError:
        return jsonify({'status': 'error', 'message': 'Missing required fields (user_id, session_type)'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get_history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    """
    API để lấy toàn bộ lịch sử chat của một user_id cụ thể.
    """
    try:
        # Truy vấn tất cả bản ghi của user_id, sắp xếp theo thời gian
        records = ConversationHistory.query.filter_by(user_id=user_id).order_by(ConversationHistory.timestamp.asc()).all()
        
        # Chuyển đổi danh sách records sang list of dictionaries
        history_list = [record.to_dict() for record in records]
        
        return jsonify({'status': 'success', 'history': history_list}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# --- 3. Route để hiển thị trang Chat (Để test) ---
@app.route('/')
def chat_interface():
    """
    Render trang chat.html để ta có thể test
    """
    # Ta sẽ giả lập là user 1 và chat với 'chatbot'
    return render_template('chat.html', user_id=1, session_type='chatbot')


# --- 4. Chạy App ---
if __name__ == '__main__':
    app.run(debug=True) # debug=True để tự động reload khi code thay đổi
