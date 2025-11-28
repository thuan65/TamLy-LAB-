from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return "App hỗ trợ tâm lý"

@app.route('/game/tetris')
def tetris():
    return render_template('Tetris.html')

@app.route('/game/endlessRun')
def endless():
    return render_template('endless_run.html')

@app.route('/game/2048')
def G2048():
    return render_template('2048.html')

@app.route('/game/wordle')
def wordle():
    return render_template('wordle.html')

if __name__ == '__main__':
    app.run(debug=True)