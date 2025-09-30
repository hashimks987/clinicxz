from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
from datetime import datetime

import models, schemas, auth, database

# Create all database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    # Check if users exist
    user = db.query(models.User).first()
    if not user:
        print("Creating default users...")
        # Create default users if they don't exist
        user1_in = schemas.UserCreate(username="therapist1", password="password123")
        user2_in = schemas.UserCreate(username="therapist2", password="password456")
        auth.create_user(db, user1_in)
        auth.create_user(db, user2_in)
    db.close()

# --- Frontend Rendering ---
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Authentication Endpoints ---
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- API Endpoints ---
# GET Current User
@app.get("/api/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user

# GET all patients (returns simple list)
@app.get("/api/patients", response_model=List[schemas.Patient])
def read_patients(db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    patients = db.query(models.Patient).order_by(models.Patient.name).all()
    return patients

# GET a single patient (returns detailed view)
@app.get("/api/patients/{patient_id}", response_model=schemas.PatientDetail)
def read_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_patient = db.query(models.Patient).options(
        joinedload(models.Patient.visits),
        joinedload(models.Patient.sub_issues)
    ).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

# CREATE a new patient
@app.post("/api/patients", response_model=schemas.Patient)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_patient = models.Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# DELETE a patient
@app.delete("/api/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(db_patient)
    db.commit()
    return

# CREATE a sub-issue for a patient
@app.post("/api/patients/{patient_id}/subissues", response_model=schemas.SubIssue)
def create_sub_issue_for_patient(patient_id: int, sub_issue: schemas.SubIssueCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_sub_issue = models.SubIssue(**sub_issue.model_dump(), patient_id=patient_id)
    db.add(db_sub_issue)
    db.commit()
    db.refresh(db_sub_issue)
    return db_sub_issue

# DELETE a sub-issue
@app.delete("/api/subissues/{sub_issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sub_issue(sub_issue_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_sub_issue = db.query(models.SubIssue).filter(models.SubIssue.id == sub_issue_id).first()
    if db_sub_issue is None:
        raise HTTPException(status_code=404, detail="Sub-issue not found")
    db.delete(db_sub_issue)
    db.commit()
    return

# CREATE a visit and update progress
@app.post("/api/patients/{patient_id}/visits", response_model=schemas.Visit)
def create_visit_for_patient(patient_id: int, visit: schemas.VisitCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    db_visit = models.Visit(description=visit.description, patient_id=patient_id)
    db.add(db_visit)
    
    for progress_update in visit.progress_updates:
        db_sub_issue = db.query(models.SubIssue).filter(models.SubIssue.id == progress_update.sub_issue_id).first()
        if db_sub_issue and db_sub_issue.patient_id == patient_id:
            db_sub_issue.progress_percentage = progress_update.progress_percentage
    
    db.commit()
    db.refresh(db_visit)
    return db_visit

# --- Schedule Endpoints ---
@app.get("/api/schedules", response_model=List[schemas.Schedule])
def get_schedules(db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    schedules = db.query(models.Schedule).order_by(models.Schedule.appointment_time).all()
    return schedules

@app.post("/api/schedules", response_model=schemas.Schedule)
def create_schedule(schedule: schemas.ScheduleCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_schedule = models.Schedule(**schedule.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@app.put("/api/schedules/{schedule_id}", response_model=schemas.Schedule)
def update_schedule_status(schedule_id: int, status_update: Dict[str, str], db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    db_schedule = db.query(models.Schedule).filter(models.Schedule.id == schedule_id).first()
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    new_status = status_update.get("status")
    if not new_status or new_status not in ["Scheduled", "Completed", "Canceled"]:
        raise HTTPException(status_code=400, detail="Invalid status provided")

    db_schedule.status = new_status
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

# --- Dashboard Endpoints ---
@app.get("/api/visits/recent", response_model=List[Dict[str, Any]])
def get_recent_visits(db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_active_user)):
    recent_visits = db.query(models.Visit).options(joinedload(models.Visit.patient)).order_by(models.Visit.visit_date.desc()).limit(5).all()
    seen_patient_ids = set()
    response = []
    for visit in recent_visits:
        if visit.patient and visit.patient.id not in seen_patient_ids:
            response.append({
                "patient_id": visit.patient_id, "patient_name": visit.patient.name, "visit_date": visit.visit_date
            })
            seen_patient_ids.add(visit.patient.id)
    return response

