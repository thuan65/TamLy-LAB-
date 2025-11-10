from flask import Flask
from auth import auth
from forum import forum
from db import close_db
import os

app = Flask(__name__)
# app.secret_key = os.urandom(24)  # tạo ngẫu nhiên 24 bytes
app.secret_key = "my-dev-secret-key"

app.teardown_appcontext(close_db)

# Đăng ký blueprint
app.register_blueprint(auth)
app.register_blueprint(forum)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

