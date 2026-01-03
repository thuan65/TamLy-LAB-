import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from Game.game_routes import game_bp
from quiz.quiz import quiz_bp
from diary.diary import diary_bp
from Aerial.Chatbot import chatbot_bp

from loginforum.extensions import socketio
from loginforum.chat import chat
from db import close_db, init_db
from loginforum.history_conversation import history_bp
from loginforum.auth import auth
from loginforum.forum import forum
from loginforum.chat_expert import chat_expert_bp
from Booking.booking import booking_bp

import os

app = Flask(__name__)
app.secret_key = "my-dev-secret-key"

# init socketio cho app ngoài
socketio.init_app(app)

# --- Teardown DB ---
app.teardown_appcontext(close_db)

# --- Đăng ký blueprint ---
app.register_blueprint(auth)
app.register_blueprint(forum)
app.register_blueprint(chat)
app.register_blueprint(chat_expert_bp)
app.register_blueprint(history_bp)
app.register_blueprint(game_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(diary_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(booking_bp)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/index")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    # tạo db nếu cần
    print(app.url_map) #in ra endpoint de debug
    socketio.run(app, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
