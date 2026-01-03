# db_sessions.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# FORUM_DB_PATH = os.path.join(BASE_DIR, "loginforum", "forum.db")   # users
THERAPY_DB_PATH = os.path.join(BASE_DIR, "therapy.db")            # students, diary
Base = declarative_base()

# ForumEngine = create_engine(f"sqlite:///{FORUM_DB_PATH}", echo=False)
TherapyEngine = create_engine(f"sqlite:///{THERAPY_DB_PATH}", echo=False)

# ForumSession = sessionmaker(bind=ForumEngine)
TherapySession = sessionmaker(bind=TherapyEngine)
