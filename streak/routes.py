from flask import Blueprint, session, jsonify
from database import TherapySession
from .utils import calc_streak

streak_bp = Blueprint("streak_bp", __name__, url_prefix="/api/streak")

@streak_bp.route("", methods=["GET"])
def get_streak():
    if "user_id" not in session:
        return jsonify({"error": "login required"}), 403

    db = TherapySession()
    return jsonify(calc_streak(db, session["user_id"]))
