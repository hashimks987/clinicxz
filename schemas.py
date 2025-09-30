from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime

# --- SubIssue Schemas ---
class SubIssueBase(BaseModel):
    name: str

class SubIssueCreate(SubIssueBase):
    pass

class ProgressUpdate(BaseModel):
    sub_issue_id: int
    progress_percentage: int

class SubIssue(SubIssueBase):
    id: int
    patient_id: int
    progress_percentage: int
    model_config = ConfigDict(from_attributes=True)

# --- Visit Schemas ---
class VisitBase(BaseModel):
    description: Optional[str] = None

class VisitCreate(VisitBase):
    progress_updates: List[ProgressUpdate] = []
    
class Visit(VisitBase):
    id: int
    patient_id: int
    visit_date: date
    model_config = ConfigDict(from_attributes=True)

# --- Schedule Schemas ---
class ScheduleBase(BaseModel):
    attendee_name: Optional[str] = None # Made this field optional to prevent validation errors
    appointment_time: datetime
    status: str

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    
# --- Patient Schemas ---
class PatientBase(BaseModel):
    name: str
    age: int
    place: Optional[str] = None
    phone_number: Optional[str] = None
    education: Optional[str] = None
    core_reason: str
    issue_start_date: Optional[str] = None
    severity: str
    previous_treatments: Optional[str] = None
    other_meds: Optional[str] = None
    other_diseases: Optional[str] = None
    partner_name: Optional[str] = None
    mother_name: Optional[str] = None
    is_married: bool = False
    has_siblings: bool = False
    has_kids: bool = False
    kids_count: int = 0
    is_genetic: bool = False
    is_working: bool = False
    consultation_mode: str = "Offline"

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class PatientDetail(Patient):
    sub_issues: List[SubIssue] = []
    visits: List[Visit] = []


# --- User & Token Schemas ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

