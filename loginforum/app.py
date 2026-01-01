# loginforum/app.py
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, session, redirect
import os

# IMPORT THEO PACKAGE (QUAN TRỌNG)
from .extensions import socketio
from .history_conversation import history_bp
from .chat import chat
from .auth import auth
from .forum import forum
from .chat_expert import chat_expert_bp
from .db import close_db, init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = "my-dev-secret-key"

    # --- teardown db ---
    app.teardown_appcontext(close_db)

    # --- register blueprints ---
    app.register_blueprint(auth)
    app.register_blueprint(forum)
    app.register_blueprint(chat)
    app.register_blueprint(chat_expert_bp)
    app.register_blueprint(history_bp)

    # --- routes ---
    @app.route("/", endpoint="home")
    def home():
        # muốn về forum hay dashboard thì tùy bạn
        return redirect(url_for("forum.show_forum"))
        # hoặc: return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect("/login")

        if session.get("role") == "student":
            return redirect("/dashboard_student")
        return redirect("/dashboard_expert")

    @app.route("/dashboard_student")
    def dashboard_student():
        if "user_id" not in session:
            return redirect("/login")

        return render_template(
            "dashboard.html",
            username=session["username"],
            role=session["role"],
            user_id=session["user_id"],
            status_tag=session.get("status_tag"),
            chat_opt_in=session.get("chat_opt_in"),
        )

    @app.route("/dashboard_expert")
    def dashboard_expert():
        if "user_id" not in session:
            return redirect("/login")

        return render_template(
            "dashboard.html",
            username=session["username"],
            role=session["role"],
            user_id=session["user_id"],
        )

    socketio.init_app(app)
    return app


# =============================
# CHẠY RIÊNG ĐỂ TEST
# =============================
if __name__ == "__main__":
    app = create_app()

    # tạo DB forum nếu chưa có
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "forum.db")):
        init_db()

    print("🚀 LoginForum test server running...")
    socketio.run(
        app,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
