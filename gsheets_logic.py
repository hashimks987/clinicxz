# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import schemas
# from datetime import date
# from typing import List, Dict, Any

# # --- Configuration ---
# SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# CREDS_FILE = 'client_secret.json'
# SPREADSHEET_NAME = 'ClinicXZ_Data'

# # --- Helper Functions ---
# def get_spreadsheet():
#     """Authenticates and returns the spreadsheet object, ensuring it's fully initialized."""
#     try:
#         creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
#         client = gspread.authorize(creds)
#         try:
#             spreadsheet = client.open(SPREADSHEET_NAME)
#         except gspread.SpreadsheetNotFound:
#             print(f"Spreadsheet '{SPREADSHEET_NAME}' not found. Creating it.")
#             spreadsheet = client.create(SPREADSHEET_NAME)
#             # Share the sheet with the service account email to ensure permissions
#             spreadsheet.share(creds.service_account_email, perm_type='user', role='writer')
        
#         # This robust check ensures all required worksheets exist.
#         init_worksheets(spreadsheet)
#         return spreadsheet

#     except FileNotFoundError:
#         print(f"FATAL ERROR: Credentials file '{CREDS_FILE}' not found. Please ensure it is in the root directory.")
#         return None
#     except Exception as e:
#         print(f"An error occurred during Google Sheets authentication: {e}")
#         return None

# def init_worksheets(spreadsheet):
#     """Creates any missing worksheets and their headers."""
#     worksheet_titles = [ws.title for ws in spreadsheet.worksheets()]
#     headers = {
#         "Patients": ['id', 'name', 'age', 'place', 'phone_number', 'education', 'core_reason', 'issue_start_date', 'severity', 'previous_treatments', 'other_meds', 'other_diseases', 'partner_name', 'mother_name', 'is_married', 'has_siblings', 'has_kids', 'kids_count', 'is_genetic', 'is_working', 'consultation_mode'],
#         "Visits": ['id', 'patient_id', 'description', 'visit_date'],
#         "SubIssues": ['id', 'patient_id', 'name', 'progress_percentage'],
#         "Schedules": ['id', 'attendee_name', 'appointment_time', 'status'],
#         "Users": ['id', 'username', 'hashed_password', 'is_active']
#     }
#     for title, header_row in headers.items():
#         if title not in worksheet_titles:
#             print(f"Creating missing worksheet: {title}")
#             worksheet = spreadsheet.add_worksheet(title=title, rows="1", cols=len(header_row))
#             worksheet.append_row(header_row)

# def get_next_id(worksheet):
#     """Calculates the next sequential ID for a new row."""
#     ids = worksheet.col_values(1)[1:]  # Get all IDs except the header
#     if not ids:
#         return 1
#     return max([int(i) for i in ids if i.isdigit()]) + 1

# # --- Data Functions ---
# def get_all_users() -> List[Dict[str, Any]]:
#     ss = get_spreadsheet()
#     if not ss: return []
#     try:
#         worksheet = ss.worksheet("Users")
#         return worksheet.get_all_records()
#     except gspread.exceptions.WorksheetNotFound:
#         return []

# def create_user(user: schemas.UserCreate, hashed_pass: str):
#     ss = get_spreadsheet()
#     if not ss: return
#     worksheet = ss.worksheet("Users")
#     next_id = get_next_id(worksheet)
#     # The 'is_active' column is set to TRUE for Google Sheets compatibility
#     new_row = [next_id, user.username, hashed_pass, 'TRUE']
#     worksheet.append_row(new_row)

# def get_user(username: str) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     if not ss: return None
#     try:
#         worksheet = ss.worksheet("Users")
#         cell = worksheet.find(username, in_column=2)
#         if not cell: return None
#         headers = worksheet.row_values(1)
#         values = worksheet.row_values(cell.row)
#         return dict(zip(headers, values))
#     except gspread.exceptions.WorksheetNotFound:
#         print("Warning: 'Users' worksheet not found during user lookup.")
#         return None
#     except gspread.exceptions.CellNotFound:
#         return None
        
# # PATIENTS
# def get_all_patients() -> List[Dict[str, Any]]:
#     ss = get_spreadsheet()
#     if not ss: return []
#     worksheet = ss.worksheet("Patients")
#     return worksheet.get_all_records()

# def get_patient_by_id(patient_id: int) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     if not ss: return None
#     worksheet = ss.worksheet("Patients")
#     try:
#         patient_cell = worksheet.find(str(patient_id), in_column=1)
#         if not patient_cell: return None
#         patient_data = worksheet.get_all_records()[patient_cell.row - 2]
#         patient_data['sub_issues'] = get_subissues_for_patient(patient_id)
#         patient_data['visits'] = get_visits_for_patient(patient_id)
#         return patient_data
#     except gspread.exceptions.CellNotFound:
#         return None

# def create_patient(patient: schemas.PatientCreate) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("Patients")
#     next_id = get_next_id(worksheet)
#     patient_dict = patient.model_dump()
#     patient_dict['id'] = next_id
#     headers = worksheet.row_values(1)
#     new_row = [str(patient_dict.get(h, '')) for h in headers]
#     worksheet.append_row(new_row)
#     return patient_dict

# def delete_patient(patient_id: int) -> bool:
#     ss = get_spreadsheet()
#     try:
#         p_ws = ss.worksheet("Patients")
#         cell = p_ws.find(str(patient_id), in_column=1)
#         if not cell: return False
#         p_ws.delete_rows(cell.row)

#         v_ws = ss.worksheet("Visits")
#         cells_to_delete = v_ws.findall(str(patient_id), in_column=2)
#         for cell_to_del in reversed(sorted(cells_to_delete, key=lambda c: c.row)): v_ws.delete_rows(cell_to_del.row)

#         s_ws = ss.worksheet("SubIssues")
#         cells_to_delete = s_ws.findall(str(patient_id), in_column=2)
#         for cell_to_del in reversed(sorted(cells_to_delete, key=lambda c: c.row)): s_ws.delete_rows(cell_to_del.row)
#         return True
#     except gspread.exceptions.CellNotFound:
#         return False

# # VISITS AND SUB-ISSUES
# def get_all_visits() -> List[Dict[str, Any]]:
#     ss = get_spreadsheet()
#     if not ss: return []
#     worksheet = ss.worksheet("Visits")
#     return worksheet.get_all_records()

# def get_subissues_for_patient(patient_id: int) -> List[Dict[str, Any]]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("SubIssues")
#     all_records = worksheet.get_all_records()
#     return [record for record in all_records if str(record.get('patient_id')) == str(patient_id)]

# def get_visits_for_patient(patient_id: int) -> List[Dict[str, Any]]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("Visits")
#     all_records = worksheet.get_all_records()
#     return [record for record in all_records if str(record.get('patient_id')) == str(patient_id)]

# def create_visit(patient_id: int, visit: schemas.VisitCreate) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("Visits")
#     next_id = get_next_id(worksheet)
#     new_row = [next_id, patient_id, visit.description, date.today().isoformat()]
#     worksheet.append_row(new_row)
    
#     si_worksheet = ss.worksheet("SubIssues")
#     for update in visit.progress_updates:
#         try:
#             cell = si_worksheet.find(str(update.sub_issue_id), in_column=1)
#             if cell: si_worksheet.update_cell(cell.row, 4, update.progress_percentage)
#         except gspread.exceptions.CellNotFound: continue
            
#     return {"id": next_id, "patient_id": patient_id, "visit_date": date.today(), **visit.model_dump()}

# def create_subissue(patient_id: int, sub_issue: schemas.SubIssueCreate) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("SubIssues")
#     next_id = get_next_id(worksheet)
#     new_row = [next_id, patient_id, sub_issue.name, 0]
#     worksheet.append_row(new_row)
#     return {"id": next_id, "patient_id": patient_id, "progress_percentage": 0, **sub_issue.model_dump()}

# def delete_subissue(sub_issue_id: int) -> bool:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("SubIssues")
#     try:
#         cell = worksheet.find(str(sub_issue_id), in_column=1)
#         if not cell: return False
#         worksheet.delete_rows(cell.row)
#         return True
#     except gspread.exceptions.CellNotFound: return False

# # SCHEDULES
# def get_all_schedules() -> List[Dict[str, Any]]:
#     ss = get_spreadsheet()
#     if not ss: return []
#     worksheet = ss.worksheet("Schedules")
#     return worksheet.get_all_records()

# def create_schedule(schedule: schemas.ScheduleCreate) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("Schedules")
#     next_id = get_next_id(worksheet)
#     new_row = [next_id, schedule.attendee_name, schedule.appointment_time.isoformat(), schedule.status]
#     worksheet.append_row(new_row)
#     return {"id": next_id, **schedule.model_dump()}

# def update_schedule(schedule_id: int, status: str) -> Dict[str, Any]:
#     ss = get_spreadsheet()
#     worksheet = ss.worksheet("Schedules")
#     try:
#         cell = worksheet.find(str(schedule_id), in_column=1)
#         if not cell: return None
#         worksheet.update_cell(cell.row, 4, status)
#         updated_row = worksheet.row_values(cell.row)
#         return {"id": int(updated_row[0]), "attendee_name": updated_row[1], "appointment_time": updated_row[2], "status": updated_row[3]}
#     except gspread.exceptions.CellNotFound:
#         return None

