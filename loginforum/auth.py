from flask import Blueprint, render_template, request, redirect, session
from .db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from db_session import TherapySession
from createTherapyDB import Student
from flask import url_for


auth = Blueprint("auth", __name__, url_prefix="/auth", template_folder="htmltemplates")



# Trang đăng ký
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if not username or not password:
            return render_template("error.html", message="Vui lòng nhập đủ thông tin!", back_url="/register")

        conn = get_db()
        # Kiểm tra username đã tồn tại chưa
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return render_template("error.html", message="Tên người dùng đã tồn tại!", back_url="/register")

        hashed_pw = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
        conn.commit()
        #@@@@@@@@@@@@@@@@@@@@@@@@@@ moi them vao de tao Student tuong ung trong therapy.db 
        #Lấy user_id vừa tạo
        user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()["id"]

        # Tạo Student trong therapy.db

        ts = TherapySession()

        existed = ts.query(Student).filter_by(user_id=user_id).first()
        if not existed:
            ts.add(Student(
                user_id=user_id,
                full_name=username,  # tạm dùng username
                email=None
            ))
            ts.commit()

        ts.close()
        #@@@@@@@@@@@@@@@@@@@@@@@@@@ moi them vao de tao Student tuong ung trong therapy.db


        return redirect(url_for("auth.login"))

    return render_template("register.html")

# Trang đăng nhập
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        # Nếu không tìm thấy user
        if user is None:
            return render_template("error.html", message="Tên người dùng không tồn tại!", back_url="/login")

        # Nếu mật khẩu sai
        if not check_password_hash(user["password"], password):
            return render_template("error.html", message="Sai mật khẩu!", back_url="/login")

        # Nếu đúng
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        
        # --- NỘI DUNG MỚI ---
        session["chat_opt_in"] = user["chat_opt_in"]
        session["status_tag"] = user["status_tag"]

        # --- Chuyển hướng ---
        return redirect("/")
        
    return render_template("login.html")

# Đăng xuất
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")

