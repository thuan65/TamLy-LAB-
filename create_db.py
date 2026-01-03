import models
from database import Base, TherapyEngine
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'therapy.db')}"


Base.metadata.create_all(TherapyEngine)