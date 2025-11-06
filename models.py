# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ConversationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # ID của người dùng (để biết lịch sử này của ai)
    user_id = db.Column(db.Integer, nullable=False) 
    
    # Phân biệt là chat với 'chatbot' hay 'expert'
    session_type = db.Column(db.String(50), nullable=False) 
    
    # Nội dung người dùng gửi
    user_message = db.Column(db.Text, nullable=True)
    
    # Nội dung hệ thống (bot/chuyên gia) trả lời
    system_response = db.Column(db.Text, nullable=True)
    
    # Dấu thời gian
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Chuyển đổi object sang dictionary để trả về JSON"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_type': self.session_type,
            'user_message': self.user_message,
            'system_response': self.system_response,
            'timestamp': self.timestamp.isoformat()
        }