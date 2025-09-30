from sqlalchemy import create_engine, Column, Integer, String, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import date

from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    place = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    education = Column(String, nullable=True)
    core_reason = Column(String)
    issue_start_date = Column(String, nullable=True)
    severity = Column(String)
    previous_treatments = Column(String, nullable=True)
    other_meds = Column(String, nullable=True)
    other_diseases = Column(String, nullable=True)
    partner_name = Column(String, nullable=True)
    mother_name = Column(String, nullable=True)
    is_married = Column(Boolean, default=False)
    has_siblings = Column(Boolean, default=False)
    has_kids = Column(Boolean, default=False)
    kids_count = Column(Integer, default=0)
    is_genetic = Column(Boolean, default=False)
    is_working = Column(Boolean, default=False)
    consultation_mode = Column(String, default="Offline")
    
    sub_issues = relationship("SubIssue", back_populates="patient", cascade="all, delete-orphan")
    visits = relationship("Visit", back_populates="patient", cascade="all, delete-orphan")

class SubIssue(Base):
    __tablename__ = "sub_issues"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    progress_percentage = Column(Integer, default=0)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="sub_issues")

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=True)
    # Corrected from DateTime to Date to match the schema
    visit_date = Column(Date, default=date.today)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    patient = relationship("Patient", back_populates="visits")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    attendee_name = Column(String)
    appointment_time = Column(DateTime)
    status = Column(String, default="Scheduled")

