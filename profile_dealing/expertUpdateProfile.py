from flask import Blueprint, render_template, request, redirect, session as flask_session, url_for

from datetime import datetime, timedelta
from models import User, ExpertProfile, StudentProfile
from database import TherapySession


expert_bp = Blueprint("expert", __name__, url_prefix="/expert", template_folder="htmltemplates")

@expert_bp.route("/profile/edit", methods=["GET"])
def edit_profile():
    user_id = flask_session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    with TherapySession() as db:
        user = db.query(User).filter_by(id=user_id, role="EXPERT").first()
        if not user or not user.expert_profile:
            return "Không tìm thấy hồ sơ chuyên gia", 404

        profile = user.expert_profile

    return render_template("edit_profile.html", profile=profile)

@expert_bp.route("/profile/update", methods=["POST"])
def update_profile():
    user_id = flask_session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))

    with TherapySession() as db:
        profile = db.query(ExpertProfile).filter_by(user_id=user_id).first()
        if not profile:
            return "Không tìm thấy hồ sơ chuyên gia", 404

        profile.full_name = request.form["full_name"]
        profile.title = request.form.get("title")
        profile.qualification = request.form.get("qualification")
        profile.specialization = request.form.get("specialization")
        profile.bio = request.form.get("bio")


        profile.verification_status = "PENDING"
        profile.is_active = False

        db.commit()

    return redirect(url_for("index"))

