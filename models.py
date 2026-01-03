# createTherapyDB.py
import os
from sqlalchemy import (
    String, Text, Integer, ForeignKey, Column, Float, Date,
    DateTime, Boolean, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from database import Base

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_URL = f"sqlite:///{os.path.join(BASE_DIR, 'therapy.db')}"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="student")  
    status_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    chat_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen = Column(DateTime, default=func.now())
    is_online = Column(Boolean, default=False)

    posts = relationship("Post", back_populates="author")
    answers = relationship("Answer", back_populates="expert")
    expert_profile = relationship("ExpertProfile",uselist=False,back_populates="user", foreign_keys="ExpertProfile.user_id"
    )
    student_profile = relationship("StudentProfile", uselist=False, back_populates="user")

class ExpertProfile(Base):
    __tablename__ = "expert_profiles"

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        primary_key=True
    )

    full_name = Column(String(100), nullable=False)
    title = Column(String(100)) #Học hàm
    qualification = Column(String(255)) #Học vị
    specialization = Column(String(255))
    organization = Column(String(255)) #Tổ chức, phòng khám,...
    years_of_experience = Column(Integer)
    verification_status = Column(String, default= "PENDING")

    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime)

    bio = Column(Text) #Tiểu sử
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    user = relationship("User", back_populates="expert_profile", foreign_keys=[user_id])

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    full_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)  # "MALE", "FEMALE", "OTHER"
    dob = Column(Date, nullable=True)
    major = Column(String(255), nullable=True)
    school = Column(String(255), nullable=True)
    vip_level = Column(Integer, default=0)
    last_stress_score = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="student_profile")

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tag: Mapped[str] = mapped_column(String, default="unanswered")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    author = relationship("User", back_populates="posts")
    answers = relationship("Answer", back_populates="post")

class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    expert_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    expert = relationship("User", back_populates="answers")
    post = relationship("Post", back_populates="answers")

class ChatQueue(Base):
    __tablename__ = "chat_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    illness_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="waiting")
    requested_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_key: Mapped[str] = mapped_column(String, unique=True)
    seeker_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    helper_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String, default="active")
    is_expert_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    seeker = relationship("User", foreign_keys=[seeker_id])
    helper = relationship("User", foreign_keys=[helper_id])

class ChatAlert(Base):
    __tablename__ = "chat_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    message_content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="new")
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    session = relationship("ChatSession")

class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    session_type: Mapped[str] = mapped_column(String, nullable=False)
    session_key: Mapped[str] = mapped_column(String, nullable=False)
    user_message: Mapped[str | None] = mapped_column(Text)
    system_response: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    user = relationship("User")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_read = Column(Boolean, default=False)

    # Quan hệ với bảng users (tùy chọn)
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")

# class TherapistRating(Base):
#     __tablename__ = "therapist_ratings"
#     id = Column(Integer, primary_key=True)
#     student_id = Column(Integer, ForeignKey("students.id"))
#     therapist_id = Column(Integer, ForeignKey("therapists.id"))
#     score = Column(Float, nullable=False)
#     comment = Column(Text)
#     created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

class StressLog(Base):
    __tablename__ = "stress_logs"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float, nullable=False)
    scale_name = Column(String, default="DASS")
    note = Column(Text)
    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    start_time = Column(String, nullable=False) # Format: YYYY-MM-DD HH:MM:SS
    end_time = Column(String, nullable=False)   # Format: YYYY-MM-DD HH:MM:SS
    
    meet_type = Column(String, default='offline') 
    
    location = Column(String)
    
    status = Column(String, default='confirmed')
    
    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))

    student = relationship("User", foreign_keys=[student_id], backref="student_appointments")
    therapist = relationship("User", foreign_keys=[therapist_id], backref="therapist_appointments")

class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    mood = Column(String, default="Binh thuong")
    mood_score = Column(Integer, default=3)
    tags = Column(String)
    is_private = Column(Integer, default=1)  # 1: private, 0: public/share

    created_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at = Column(String, default=lambda: datetime.now().isoformat(timespec="seconds"))
