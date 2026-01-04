import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
#print("GEMINI_API_KEY =", os.getenv("GEMINI_API_KEY"))


os.environ["EVENTLET_NO_GREENDNS"] = "yes"
import eventlet
eventlet.monkey_patch()

from flask import Flask, session, render_template
from Game.game_routes import game_bp
from quiz.quiz import quiz_bp
from diary.diary import diary_bp
from Aerial.Chatbot import chatbot_bp

from loginforum.extensions import socketio
from loginforum.chat import chat
from  profile_dealing.expertUpdateProfile import expert_bp
from streak.routes import streak_bp
from admin_verify.routes import admin_bp
from admin_verify.routes import expert_profile_bp

from db import close_db, init_db
from loginforum.history_conversation import history_bp
from loginforum.auth import auth
from loginforum.forum import forum
from loginforum.chat_expert import chat_expert_bp
from Booking.booking import booking_bp
from Search.search_specialization import search_specialization_bp

from database import TherapySession
from models import User


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
app.register_blueprint(expert_bp)

app.register_blueprint(diary_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(search_specialization_bp)
app.register_blueprint(streak_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(expert_profile_bp)

@app.route("/")
def index():
    user_id = session.get("user_id")

    expert_profile = None
    if user_id:
        with TherapySession() as db:
            user = db.query(User).filter_by(id=user_id).first()
            if user and user.role == "EXPERT":
                expert_profile = user.expert_profile

    return render_template(
        "index.html",
        expert_profile=expert_profile
    )

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
