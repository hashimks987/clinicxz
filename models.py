# clinicxz/models.py

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, JSON
from sqlalchemy.orm import relationship
from database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    phone_number = Column(String, index=True)
    age = Column(Integer, nullable=True)
    place = Column(String, nullable=True)
    father_name = Column(String, nullable=True)
    school_class_studied = Column(String, nullable=True) # Changed
    madrasa_class_studied = Column(String, nullable=True) # Changed
    is_married = Column(Boolean, default=False)
    husband_name = Column(String, nullable=True)
    husband_job = Column(String, nullable=True)
    kids_count = Column(Integer, nullable=True)
    is_working = Column(Boolean, default=False)
    has_siblings = Column(Boolean, default=False)
    siblings_have_issues = Column(Boolean, default=False)
    core_reason = Column(String, nullable=True)
    when_it_started = Column(String, nullable=True)
    previously_sought_help = Column(JSON, nullable=True) # List of strings
    previously_sought_help_other = Column(String, nullable=True)
    medicine_status = Column(String, nullable=True)
    other_medications = Column(String, nullable=True)
    other_diseases = Column(String, nullable=True)
    is_genetic = Column(Boolean, default=False)
    genetic_relative_name = Column(String, nullable=True)
    
    kids = relationship("Kid", back_populates="patient", cascade="all, delete-orphan")
    core_issues = relationship("CoreIssues", uselist=False, back_populates="patient", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="patient", cascade="all, delete-orphan", order_by="desc(Session.date)")
    tracked_issues = relationship("TrackedIssue", back_populates="patient", cascade="all, delete-orphan") # New

class Kid(Base):
    __tablename__ = "kids"
    id = Column(Integer, primary_key=True, index=True)
    sex = Column(String)
    age = Column(Integer)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="kids")

class CoreIssues(Base):
    __tablename__ = "core_issues"
    id = Column(Integer, primary_key=True, index=True)
    is_about_belief = Column(Boolean, default=False)
    niyyath_related = Column(JSON, nullable=True) 
    wudu_time = Column(String, nullable=True)
    namaz_time = Column(String, nullable=True)
    najas_related = Column(JSON, nullable=True)
    dog_related = Column(Boolean, default=False)
    pig_related = Column(Boolean, default=False)
    over_soaping = Column(Boolean, default=False)
    fear_of_death = Column(Boolean, default=False)
    fear_of_disease = Column(Boolean, default=False)
    door_locking_related = Column(Boolean, default=False)
    other_issues = Column(String, nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="core_issues")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(Date)
    log = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="sessions")

# NEW MODEL for the new "Progress Tracking" tab
class TrackedIssue(Base):
    __tablename__ = "tracked_issues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    percentage_cured = Column(Integer)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="tracked_issues")
    
class ScheduleEvent(Base):
    __tablename__ = "schedule_events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    time = Column(String)
    status = Column(String, default="Scheduled")