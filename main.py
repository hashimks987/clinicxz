# clinicxz/main.py

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import timedelta

import auth, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create default users on startup if they don't exist
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    users_to_create = [
        {"username": "therapist1", "password": "password123"},
        {"username": "therapist2", "password": "password123"},
    ]
    for user_data in users_to_create:
        db_user = db.query(models.User).filter(models.User.username == user_data["username"]).first()
        if not db_user:
            hashed_password = auth.get_password_hash(user_data["password"])
            new_user = models.User(username=user_data["username"], hashed_password=hashed_password)
            db.add(new_user)
    db.commit()
    db.close()

# --- HTML Template Rendering ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Authentication Endpoints ---
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

# --- Patient Endpoints ---
@app.post("/api/patients", response_model=schemas.Patient, status_code=status.HTTP_201_CREATED)
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_patient = models.Patient(**patient.dict(exclude={"kids"}))
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    for kid_data in patient.kids:
        db_kid = models.Kid(**kid_data.dict(), patient_id=db_patient.id)
        db.add(db_kid)

    db_core_issues = models.CoreIssues(patient_id=db_patient.id)
    db.add(db_core_issues)
    
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/api/patients", response_model=List[schemas.Patient])
def read_patients(db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    patients = db.query(models.Patient).options(joinedload(models.Patient.kids)).order_by(models.Patient.full_name).all()
    return patients

@app.get("/api/patients/{patient_id}", response_model=schemas.Patient)
def read_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_patient = db.query(models.Patient).options(
        joinedload(models.Patient.kids),
        joinedload(models.Patient.core_issues),
        joinedload(models.Patient.sessions),
        joinedload(models.Patient.tracked_issues) # New
    ).filter(models.Patient.id == patient_id).first()

    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return db_patient

@app.put("/api/patients/{patient_id}", response_model=schemas.Patient)
def update_patient(patient_id: int, patient: schemas.PatientUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient_data = patient.dict(exclude_unset=True, exclude={"core_issues"})
    for key, value in patient_data.items():
        setattr(db_patient, key, value)
    
    if patient.core_issues:
        db_core_issues = db_patient.core_issues
        if not db_core_issues:
            db_core_issues = models.CoreIssues(patient_id=patient_id)
            db.add(db_core_issues)
        
        core_issues_data = patient.core_issues.dict(exclude_unset=True)
        for key, value in core_issues_data.items():
            setattr(db_core_issues, key, value)
            
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.delete("/api/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if db_patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(db_patient)
    db.commit()
    return

# --- Session Endpoints ---
@app.post("/api/patients/{patient_id}/sessions", response_model=schemas.Session, status_code=status.HTTP_201_CREATED)
def create_session_for_patient(patient_id: int, session: schemas.SessionCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_session = models.Session(**session.dict(), patient_id=patient_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.put("/api/sessions/{session_id}", response_model=schemas.Session) # New
def update_session(session_id: int, session: schemas.SessionUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = session.dict(exclude_unset=True)
    for key, value in session_data.items():
        setattr(db_session, key, value)
        
    db.commit()
    db.refresh(db_session)
    return db_session

# --- TrackedIssue Endpoints (New) ---
@app.post("/api/patients/{patient_id}/issues", response_model=schemas.TrackedIssue, status_code=status.HTTP_201_CREATED)
def create_tracked_issue(patient_id: int, issue: schemas.TrackedIssueCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not db_patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    db_issue = models.TrackedIssue(**issue.dict(), patient_id=patient_id)
    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)
    return db_issue

@app.put("/api/issues/{issue_id}", response_model=schemas.TrackedIssue)
def update_tracked_issue(issue_id: int, issue: schemas.TrackedIssueUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_issue = db.query(models.TrackedIssue).filter(models.TrackedIssue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Tracked issue not found")

    issue_data = issue.dict(exclude_unset=True)
    for key, value in issue_data.items():
        setattr(db_issue, key, value)
    
    db.commit()
    db.refresh(db_issue)
    return db_issue

@app.delete("/api/issues/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracked_issue(issue_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_issue = db.query(models.TrackedIssue).filter(models.TrackedIssue.id == issue_id).first()
    if not db_issue:
        raise HTTPException(status_code=404, detail="Tracked issue not found")
    db.delete(db_issue)
    db.commit()
    return

# --- Dashboard Stats ---
@app.get("/api/dashboard-stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    total_patients = db.query(models.Patient).count()
    upcoming_appointments = db.query(models.ScheduleEvent).filter(models.ScheduleEvent.status == "Scheduled").count()
    
    recent_sessions = db.query(models.Session).options(joinedload(models.Session.patient)).order_by(models.Session.date.desc()).limit(5).all()
    
    recent_patient_visits = []
    seen_patient_ids = set()
    for session in recent_sessions:
        if session.patient.id not in seen_patient_ids:
            recent_patient_visits.append({
                "name": session.patient.full_name,
                "last_visit": session.date.isoformat()
            })
            seen_patient_ids.add(session.patient.id)

    return {
        "total_patients": total_patients,
        "upcoming_appointments": upcoming_appointments,
        "recent_patient_visits": recent_patient_visits
    }

# --- Schedule Endpoints ---
@app.get("/api/schedule", response_model=List[schemas.ScheduleEvent])
def get_schedule(db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    return db.query(models.ScheduleEvent).order_by(models.ScheduleEvent.time).all()

@app.post("/api/schedule", response_model=schemas.ScheduleEvent, status_code=status.HTTP_201_CREATED)
def create_schedule_event(event: schemas.ScheduleEventCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_event = models.ScheduleEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@app.put("/api/schedule/{event_id}", response_model=schemas.ScheduleEvent)
def update_schedule_event_status(event_id: int, event_update: schemas.ScheduleEventUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_event = db.query(models.ScheduleEvent).filter(models.ScheduleEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db_event.status = event_update.status
    db.commit()
    db.refresh(db_event)
    return db_event

@app.delete("/api/schedule/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule_event(event_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(auth.get_current_user)):
    db_event = db.query(models.ScheduleEvent).filter(models.ScheduleEvent.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(db_event)
    db.commit()
    return