# clinicxz/schemas.py

from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date

# Pydantic V2 uses model_config instead of class Config
# and from_attributes instead of orm_mode
class_config = ConfigDict(from_attributes=True)

# Kid Schemas
class KidBase(BaseModel):
    sex: str
    age: int

class KidCreate(KidBase):
    pass

class Kid(KidBase):
    id: int
    patient_id: int
    model_config = class_config

# Session Schemas
class SessionBase(BaseModel):
    title: str
    date: date
    log: str

class SessionCreate(SessionBase):
    pass

class SessionUpdate(SessionBase):
    pass

class Session(SessionBase):
    id: int
    patient_id: int
    model_config = class_config

# NEW TrackedIssue Schemas
class TrackedIssueBase(BaseModel):
    name: str
    percentage_cured: int

class TrackedIssueCreate(TrackedIssueBase):
    pass

class TrackedIssueUpdate(TrackedIssueBase):
    pass

class TrackedIssue(TrackedIssueBase):
    id: int
    patient_id: int
    model_config = class_config

# CoreIssues Schemas
class CoreIssuesBase(BaseModel):
    is_about_belief: Optional[bool] = False
    niyyath_related: Optional[List[str]] = []
    wudu_time: Optional[str] = None
    namaz_time: Optional[str] = None
    najas_related: Optional[List[str]] = []
    dog_related: Optional[bool] = False
    pig_related: Optional[bool] = False
    over_soaping: Optional[bool] = False
    fear_of_death: Optional[bool] = False
    fear_of_disease: Optional[bool] = False
    door_locking_related: Optional[bool] = False
    other_issues: Optional[str] = None

class CoreIssues(CoreIssuesBase):
    id: int
    patient_id: int
    model_config = class_config

# Patient Schemas
class PatientBase(BaseModel):
    full_name: str
    phone_number: str
    age: Optional[int] = None
    place: Optional[str] = None
    father_name: Optional[str] = None
    school_class_studied: Optional[str] = None # Changed
    madrasa_class_studied: Optional[str] = None # Changed
    is_married: Optional[bool] = False
    husband_name: Optional[str] = None
    husband_job: Optional[str] = None
    kids_count: Optional[int] = None
    is_working: Optional[bool] = False
    has_siblings: Optional[bool] = False
    siblings_have_issues: Optional[bool] = False
    core_reason: Optional[str] = None
    when_it_started: Optional[str] = None
    previously_sought_help: Optional[List[str]] = []
    previously_sought_help_other: Optional[str] = None
    medicine_status: Optional[str] = None
    other_medications: Optional[str] = None
    other_diseases: Optional[str] = None
    is_genetic: Optional[bool] = False
    genetic_relative_name: Optional[str] = None

class PatientCreate(PatientBase):
    kids: List[KidCreate] = []

class PatientUpdate(PatientBase):
    core_issues: Optional[CoreIssuesBase]

class Patient(PatientBase):
    id: int
    kids: List[Kid] = []
    core_issues: Optional[CoreIssues]
    sessions: List[Session] = []
    tracked_issues: List[TrackedIssue] = [] # New
    model_config = class_config

# User Schemas
class User(BaseModel):
    username: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# ScheduleEvent Schemas
class ScheduleEventBase(BaseModel):
    title: str
    time: str

class ScheduleEventCreate(ScheduleEventBase):
    pass

class ScheduleEventUpdate(BaseModel):
    status: str

class ScheduleEvent(ScheduleEventBase):
    id: int
    status: str
    model_config = class_config