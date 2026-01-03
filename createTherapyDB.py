# createTherapyDB.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'therapy.db')}"

Base = declarative_base()

class Therapist(Base):
    __tablename__ = "therapists"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    field = Column(String)
    image = Column(String)
    avg_rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    years_exp = Column(Integer, default=0)
    degree = Column(String)
    organization = Column(String)
    cv_link = Column(String)
    about = Column(Text)
    is_active = Column(Integer, default=1)

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    student_code = Column(String)
    full_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    gender = Column(String)
    dob = Column(String)
    major = Column(String)             
    school = Column(String)            
    vip_level = Column(Integer, default=0)
    last_stress_score = Column(Float, default=0.0)
    is_active = Column(Integer, default=1)
    #moi them vao de mapping diary student voi user id 
    user_id = Column(Integer, nullable=True, unique=True)


class TherapistRating(Base):
    __tablename__ = "therapist_ratings"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    therapist_id = Column(Integer, ForeignKey("therapists.id"))
    score = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

class StressLog(Base):
    __tablename__ = "stress_logs"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    score = Column(Float, nullable=False)
    scale_name = Column(String, default="DASS")
    note = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("therapists.id"), nullable=False)
    
    start_time = Column(String, nullable=False) # Format: YYYY-MM-DD HH:MM:SS
    end_time = Column(String, nullable=False)   # Format: YYYY-MM-DD HH:MM:SS
    
    meet_type = Column(String, default='offline') 
    
    location = Column(String)
    
    status = Column(String, default='confirmed')
    
    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

    student = relationship("Student", backref="appointments")
    therapist = relationship("Therapist", backref="appointments")

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String, default="Binh thuong")
    mood_score = Column(Integer, default=3)
    tags = Column(String)
    is_private = Column(Integer, default=1)  # 1: private, 0: public/share

    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

engine = create_engine(DB_URL)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

if __name__ == "__main__":


    if not session.query(Therapist).first():
        t1 = Therapist(full_name="ThS. Nguyễn An", field="Stress, học đường", image="static/therapists/an.jpg",
                    years_exp=5, degree="Thạc sĩ Tâm lý", organization="TT Tham vấn ĐH KH Tự nhiên",
                    about="Tập trung vào stress sinh viên, áp lực học tập.")
        t2 = Therapist(full_name="TS. Lê Bình", field="Trị liệu gia đình", image="static/therapists/binh.jpg",
                    years_exp=9, degree="Tiến sĩ Tâm lý", organization="BV Tâm thần",
                    about="Kinh nghiệm xử lý xung đột và lo âu.")

        s1 = Student(full_name="Nguyễn Văn A", student_code="2412345", email="a@example.com",
                    major="Công nghệ thông tin", school="ĐH KH Tự nhiên")
        s2 = Student(full_name="Trần Thị B", student_code="2412346", email="b@example.com",
                    major="Tâm lý học", school="ĐH KHXH & NV")

        session.add_all([t1, t2, s1, s2])
        session.commit()

    session.close()
    print(" therapy.db created (v2 with major & school)")
