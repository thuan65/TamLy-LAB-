from flask import Blueprint, render_template, request, redirect, session, url_for
from datetime import datetime, timedelta
from models import User, ExpertProfile, StudentProfile, Appointment
from database import TherapySession
from sqlalchemy.orm import joinedload

# Khai báo Blueprint
booking_bp = Blueprint("booking", __name__, url_prefix="/booking", template_folder="templates")


def to_dict(obj):
    """Chuyển object database thành dictionary python thuần túy"""
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def generate_slots(date_obj):
    slots = []
    # Các khung giờ bắt đầu: 9h, 11h, 13h, 15h
    start_hours = [9, 11, 13, 15]
    for h in start_hours:
        s_time = date_obj.replace(hour=h, minute=0, second=0, microsecond=0)
        e_time = s_time + timedelta(hours=2)
        slots.append((s_time, e_time))
    return slots

# =========================================================
# ROUTE 1: DANH SÁCH BÁC SĨ
# =========================================================
@booking_bp.route("/select-therapist")
def select_therapist():
    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.full_path))
    
    db = TherapySession()

    therapists_objs = (db.query(User)
    .join(ExpertProfile, ExpertProfile.user_id == User.id)
    .options(joinedload(User.expert_profile))
    .filter(User.role == "EXPERT")
    .filter(ExpertProfile.is_active == True)
    .filter(ExpertProfile.verification_status == "VERIFIED")
    .all()
)

    for therapist in therapists_objs:
        print(therapist)
    
    #therapists_list = [to_dict(t) for t in therapists_objs]

    therapists_list = []
    for therapist in therapists_objs:
        expert_profile = therapist.expert_profile
        therapists_list.append({
            "id": therapist.id,
            "full_name": expert_profile.full_name if expert_profile else "Expert", #Default name
            "image": getattr(expert_profile, "image", None),    
            "field": expert_profile.specialization,
        })

    db.close()
    
    return render_template("booking_list.html", therapists=therapists_list)

# =========================================================
# ROUTE 2: LỊCH VÀ ĐẶT HẸN
# =========================================================
@booking_bp.route("/calendar/<int:therapist_id>", methods=["GET", "POST"])
def calendar(therapist_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = TherapySession()
    therapist_obj = db.query(User).filter_by(id=therapist_id).first()
    student = db.query(User).filter_by(id=session["user_id"]).first()
    
    if not student or not therapist_obj:
        db.close()
        return "Lỗi: Không tìm thấy dữ liệu học sinh hoặc chuyên gia."

    # Lưu thông tin cần thiết ra biến riêng/dict trước khi xử lý tiếp
    therapist_dict = to_dict(therapist_obj)
    if therapist_obj.expert_profile:
        therapist_dict['full_name'] = therapist_obj.expert_profile.full_name
    else:
        therapist_dict['full_name'] = "Expert" # Tên mặc định nếu chưa có profile
    # -------------------------------------------------------------
    student_id = student.id

    # --- XỬ LÝ POST (LƯU LỊCH HẸN) ---
    if request.method == "POST":
        slot_str = request.form.get("slot_time")
        meet_type = request.form.get("meet_type")
        start_dt = datetime.strptime(slot_str, "%Y-%m-%d %H:%M:%S")
        end_dt = start_dt + timedelta(hours=2)
        
        # Check logic: Mỗi người chỉ đặt 1 lần cho 1 therapist trong tương lai
        existing = db.query(Appointment).filter(
            Appointment.student_id == student_id,
            Appointment.therapist_id == therapist_id,
            Appointment.start_time >= datetime.now().strftime("%Y-%m-%d")
        ).all()
        
        if existing:
            error_msg = "Bạn đã có lịch hẹn với chuyên gia này sắp tới. Vui lòng hoàn thành trước khi đặt tiếp."
            db.close()
            return render_template("booking_error.html", message=error_msg, back_url=url_for('booking.select_therapist'))

        location = "227 Nguyễn Văn Cừ" if meet_type == "offline" else "Google Meet Link (sẽ gửi qua mail)"
        
        new_app = Appointment(
            student_id=student_id,
            therapist_id=therapist_id,
            start_time=str(start_dt),
            end_time=str(end_dt),
            meet_type=meet_type,
            location=location,
            status="confirmed"
        )
        db.add(new_app)
        db.commit()
        db.close()
        
        return render_template("booking_success.html", 
                               expert=therapist_dict['full_name'], 
                               time=slot_str, 
                               type=meet_type, 
                               location=location)

    # --- XỬ LÝ GET (HIỂN THỊ LỊCH TRỐNG) ---
    today = datetime.now()
    days_data = []
    
    for i in range(1, 8):
        current_day = today + timedelta(days=i)
        
        # Bỏ qua Thứ 7 (5) và CN (6)
        if current_day.weekday() >= 5: 
            continue
            
        daily_slots = generate_slots(current_day)
        available_slots = []
        
        for s_start, s_end in daily_slots:
            # Check DB xem giờ này đã có ai đặt chưa
            is_taken = db.query(Appointment).filter(
                Appointment.therapist_id == therapist_id,
                Appointment.start_time == str(s_start)
            ).first()
            
            if not is_taken:
                available_slots.append({
                    "display": f"{s_start.strftime('%H:%M')} - {s_end.strftime('%H:%M')}",
                    "value": str(s_start)
                })
        
        if available_slots:
            days_data.append({
                "date_str": current_day.strftime("Ngày %d/%m (%A)"),
                "slots": available_slots
            })
            
    db.close()
    
    return render_template("booking_calendar.html", therapist=therapist_dict, days_data=days_data)

# =========================================================
# ROUTE 3: LỊCH SỬ CUỘC HẸN (MỚI THÊM)
# =========================================================
@booking_bp.route("/my-appointments")
def my_appointments():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    db = TherapySession()
    
    student = db.query(User).filter_by(id=session["user_id"]).first()
    if not student:
        db.close()
        return "Không tìm thấy thông tin học sinh."

#appointments được lấy ra theo student id
    appointments = db.query(Appointment).filter_by(student_id=student.id)\
                    .order_by(Appointment.start_time.desc()).all()
    
    app_list = []
    for app in appointments:
        therapist = app.therapist
        expert_profile = therapist.expert_profile
        app_list.append({
            "start_time": app.start_time,
            "end_time": app.end_time,
            "therapist_name": expert_profile.full_name if expert_profile else "Expert", #Default name
            "therapist_img": getattr(expert_profile, "image", None),    
            "meet_type": app.meet_type,
            "location": app.location,
            "status": app.status
        })
    
    db.close()
    
    return render_template("my_appointments.html", appointments=app_list)
