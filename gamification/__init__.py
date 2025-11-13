from .db import init_db
from .bp import gamify

def setup(app):
    init_db()
    app.register_blueprint(gamify)
