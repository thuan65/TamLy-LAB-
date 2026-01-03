from flask import Flask, render_template, Blueprint, session, jsonify
from sqlalchemy import UniqueConstraint
from streak.utils import mark_game
from database import TherapySession
import os 


game_bp = Blueprint("game_bp",__name__, url_prefix="/game", template_folder="htmltemplates")


@game_bp.route('/tetris')
def tetris():
    return render_template('Tetris.html')

@game_bp.route('/endlessRun')
def endless():
    return render_template('endless_run.html')

@game_bp.route('/2048')
def G2048():
    return render_template('2048.html')

@game_bp.route('/wordle')
def wordle():
    return render_template('wordle.html')

@game_bp.route("/start", methods=["POST"])
def game_start():
    if "user_id" not in session:
        return jsonify({"error": "login required"}), 403
    db = TherapySession()
    mark_game(db, user_id=session["user_id"])
    return jsonify({"ok": True})
