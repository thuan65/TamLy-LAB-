from flask import Flask, render_template, Blueprint
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

