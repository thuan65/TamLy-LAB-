# app.py
# dùng để login, vào forum, chat với chuyên gia
from flask import Flask, render_template, session, redirect
from auth import auth
from forum import forum
from chat_expert import chat
from db import close_db, init_db
import os

app = Flask(__name__)
app.secret_key = "my-dev-secret-key"

# Kết nối và đóng DB
app.teardown_appcontext(close_db)

# Đăng ký các blueprint
app.register_blueprint(auth)
app.register_blueprint(forum)
app.register_blueprint(chat)

# ---- DASHBOARD ----
@app.route("/dashboard")
def dashboard():
    """
    Chuyển hướng theo role
    """
    if "user_id" not in session:
        return redirect("/login")
    role = session.get("role")
    if role == "student":
        return redirect("/dashboard_student")
    else:
        return redirect("/dashboard_expert")


@app.route("/dashboard_student")
def dashboard_student():
    if "user_id" not in session:
        return redirect("/login")
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        user_id=session["user_id"]
    )


@app.route("/dashboard_expert")
def dashboard_expert():
    if "user_id" not in session:
        return redirect("/login")
    return render_template(
        "dashboard.html",
        username=session["username"],
        role=session["role"],
        user_id=session["user_id"]
    )


if __name__ == "__main__":
    # Tạo DB nếu chưa có
    if not os.path.exists("forum.db"):
        init_db()

    app.run(debug=True, use_reloader=False)
