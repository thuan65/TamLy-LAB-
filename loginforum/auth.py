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
            return render_template("error.html", message="Vui lòng nhập đủ thông tin!", back_url="/auth/register")

        # ===== NHẬN CHECKBOX "TÔI LÀ CHUYÊN GIA" =====
        is_expert = bool(request.form.get("is_expert"))  # 1: Expert, 0: Student
        role = "EXPERT" if is_expert else "STUDENT"
        # =============================================

        hashed_pw = generate_password_hash(password)
        session_db = TherapySession()

        try:
            # Kiểm tra username đã tồn tại chưa
            existing_user = session_db.query(User).filter_by(username=username).first()
            if existing_user:
                return render_template(
                    "error.html",
                    message="Tên người dùng đã tồn tại!",
                    back_url="/auth/register"
                )

            # Tạo User mới
            new_user = User(
                username=username,
                password=hashed_pw,
                role=role
            )
            session_db.add(new_user)
            session_db.flush()  # Để new_user.id có giá trị trước khi tạo profile

            # ===== TẠO PROFILE TƯƠNG ỨNG =====
            if not is_expert:
                # Tạo Student Profile
                student_profile = StudentProfile(
                    user_id=new_user.id,
                    full_name=username,
                    email=None,
                    is_active=True
                )
                session_db.add(student_profile)
            else:
                # ===== TẠO EXPERT PROFILE =====
                expert_profile = ExpertProfile(
                    user_id=new_user.id,
                    full_name=username,
                    
                    # CÁC FIELD NÀY ĐỂ NULL - EXPERT SẼ CẬP NHẬT SAU
                    title=None,                    # Học hàm (GS, PGS)
                    qualification=None,            # Học vị (Tiến sĩ, Thạc sĩ, Bác sĩ)
                    specialization=None,           # Chuyên môn
                    organization=None,             # Tổ chức
                    years_of_experience=None,      # Số năm hành nghề
                    bio=None,                      # Mô tả
                    
                    # STATUS MẶC ĐỊNH - CHỜ ADMIN VERIFY
                    verification_status="PENDING",
                    is_active=False,
                    
                    verified_by=None,
                    verified_at=None
                )
                session_db.add(expert_profile)
            
            session_db.commit()

            return redirect(url_for("auth.login"))

        except Exception as e:
            session_db.rollback()
            return render_template(
                "error.html",
                message=f"Có lỗi xảy ra: {str(e)}",
                back_url="/auth/register"
            )
        finally:
            session_db.close()

    return render_template("register.html")


# Trang đăng nhập
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = TherapySession()
        
        try:
            # Lấy user theo username
            user = db.query(User).filter_by(username=username).first()

            # Nếu không tìm thấy user
            if user is None:
                return render_template("error.html", message="Tên người dùng không tồn tại!", back_url="/auth/login")

            # Nếu mật khẩu sai
            if not check_password_hash(user.password, password):
                return render_template("error.html", message="Sai mật khẩu!", back_url="/auth/login")

            # Nếu đúng
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role.lower()
            
            session["chat_opt_in"] = user.chat_opt_in
            session["status_tag"] = user.status_tag
            
            # Thêm để direct về home hoặc về trang request
            next_url = request.form.get("next")

            # --- Chuyển hướng ---
            return redirect(next_url or "/")
        finally:
            db.close()
    
    next_url = request.args.get("next")
    return render_template("login.html", next=next_url)


# Đăng xuất
@auth.route("/logout")
def logout():
    session.clear()
    return redirect("/")
