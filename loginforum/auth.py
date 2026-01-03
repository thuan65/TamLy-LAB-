from flask import Blueprint, render_template, request, redirect, session
from db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from database import TherapySession
from models import User, ExpertProfile, StudentProfile
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

        is_expert = bool(request.form.get("is_expert")) # 1: Expert, 0: studnt
        role = "EXPERT" if is_expert else "STUDENT"

        hashed_pw = generate_password_hash(password)
        with TherapySession() as session:

       # Kiểm tra username đã tồn tại chưa
            existing_user = session.query(User).filter_by(username=username).first()
            if existing_user:
                return render_template(
                    "error.html",
                    message="Tên người dùng đã tồn tại!",
                    back_url="/register"
                )

            # Tạo User mới
            new_user = User(
                username=username,
                password=hashed_pw,
                role=role
            )
            session.add(new_user)
            session.flush()  # Để new_user.id có giá trị trước khi tạo profile

            # Tạo Profile tương ứng
            if not is_expert:
                student_profile = StudentProfile(
                    user_id=new_user.id,
                    full_name=username,
                    email=None,
                    is_active=True
                )
                session.add(student_profile)
            else:
                expert_profile = ExpertProfile(
                    user_id=new_user.id,
                    full_name=username,
                    verification_status="PENDING",
                    is_active=False
                )
                session.add(expert_profile)
            
            session.commit()
            #@@@@@@@@@@@@@@@@@@@@@@@@@@ moi them vao de tao Student tuong ung trong therapy.db


        return redirect(url_for("auth.login"))

    return render_template("register.html")

# Trang đăng nhập
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        with TherapySession() as db:
       # Lấy user theo username
            user = db.query(User).filter_by(username=username).first()

        # Nếu không tìm thấy user
        if user is None:
            return render_template("error.html", message="Tên người dùng không tồn tại!", back_url="/login")

        # Nếu mật khẩu sai
        if not check_password_hash(user.password, password):
            return render_template("error.html", message="Sai mật khẩu!", back_url="/login")

        # Nếu đúng
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        
        session["chat_opt_in"] = user.chat_opt_in
        session["status_tag"] = user.status_tag
        #them de direct ve home hoac ve trang request
        next_url = request.form.get("next")

        # --- Chuyển hướng ---
        return redirect(next_url or "/")
    
    next_url = request.args.get("next")
    return render_template("login.html", next=next_url)


# Đăng xuất
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")

