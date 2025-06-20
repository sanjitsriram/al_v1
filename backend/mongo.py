"""
Asynchronous MongoDB access layer using Motor.
Handles patient records, appointments, staff queries, and specific field-based lookups.
"""

import logging
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from backend.config import MONGO_URI, MONGO_DB_NAME
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# -------------------- Logging Setup --------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.FileHandler("logs/chatbot.log")
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# -------------------- Event-Loop-Safe Mongo Client --------------------
_clients = {}

def get_db():
    """
    Ensures each asyncio event loop gets its own MongoDB client.
    Prevents cross-loop RuntimeError in apps like Streamlit.
    """
    loop = asyncio.get_event_loop()
    if loop not in _clients:
        logger.debug("[MONGO] Initializing AsyncIOMotorClient for current event loop.")
        _clients[loop] = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _clients[loop][MONGO_DB_NAME]

# -------------------- Retry Decorator --------------------
retry_mongo = retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(PyMongoError)
)

# -------------------- PATIENT HISTORY --------------------
@retry_mongo
async def get_patient_history(name: str) -> dict:
    try:
        db = get_db()
        logger.debug(f"[MONGO] Searching for patient name: {name}")
        patient = await db.patients.find_one({"name": {"$regex": name, "$options": "i"}})

        if not patient:
            logger.info(f"[MONGO] No patient found with name: {name}")
            return {"error": "Patient not found."}

        patient_id = patient.get("patient_id")
        logger.debug(f"[MONGO] Found patient_id: {patient_id}")
        logger.debug(f"[MONGO] Patient document: {patient}")

        admissions = await db.admissions.find({"patient_id": patient_id}).to_list(length=100)
        prescriptions = await db.prescriptions.find({"patient_id": patient_id}).to_list(length=100)
        diagnoses = await db.diagnoses_icd.find({"patient_id": patient_id}).to_list(length=100)
        labs = await db.labevents.find({"patient_id": patient_id}).to_list(length=100)

        return {
            "patient": patient,
            "admissions": admissions,
            "prescriptions": prescriptions,
            "diagnoses": diagnoses,
            "labs": labs
        }

    except Exception:
        logger.exception(f"[MONGO] Error retrieving patient history for {name}")
        return {"error": "Error retrieving patient history."}

# -------------------- GET PATIENT DOB --------------------
@retry_mongo
async def get_patient_dob(name: str) -> dict:
    try:
        db = get_db()
        logger.debug(f"[MONGO] Querying DOB for: {name}")
        patient = await db.patients.find_one(
            {"name": {"$regex": name, "$options": "i"}},
            {"dob": 1, "name": 1, "_id": 0}
        )
        if patient:
            logger.debug(f"[MONGO] Found DOB for {name}: {patient['dob']}")
            return patient
        else:
            logger.warning(f"[MONGO] No DOB found for: {name}")
            return {"error": "Patient not found."}
    except Exception:
        logger.exception(f"[MONGO] Error fetching DOB for {name}")
        return {"error": "Could not retrieve date of birth."}

# -------------------- GET PATIENT CONTACT --------------------
@retry_mongo
async def get_patient_contact(name: str) -> dict:
    try:
        db = get_db()
        logger.debug(f"[MONGO] Querying contact for: {name}")
        patient = await db.patients.find_one(
            {"name": {"$regex": name, "$options": "i"}},
            {"contact": 1, "name": 1, "_id": 0}
        )
        if patient:
            logger.debug(f"[MONGO] Found contact for {name}: {patient['contact']}")
            return patient
        else:
            logger.warning(f"[MONGO] No contact found for: {name}")
            return {"error": "Patient not found."}
    except Exception:
        logger.exception(f"[MONGO] Error fetching contact for {name}")
        return {"error": "Could not retrieve contact number."}

# -------------------- APPOINTMENTS TODAY --------------------
@retry_mongo
async def get_todays_appointments() -> list:
    try:
        db = get_db()
        today = datetime.today().strftime('%Y-%m-%d')
        logger.debug(f"[MONGO] Querying appointments for today: {today}")
        appointments = await db.appointments.find({"date": today}).to_list(length=100)
        return appointments
    except Exception:
        logger.exception("[MONGO] Error fetching today's appointments.")
        return [{"error": "Error fetching today's appointments."}]

# -------------------- APPOINTMENTS ON DATE --------------------
@retry_mongo
async def get_appointments_on_date(date_str: str) -> list:
    try:
        db = get_db()
        logger.debug(f"[MONGO] Querying appointments for date: {date_str}")
        appointments = await db.appointments.find({"date": date_str}).to_list(length=100)
        return appointments
    except Exception:
        logger.exception(f"[MONGO] Error fetching appointments for {date_str}")
        return [{"error": "Error fetching appointments for given date."}]

# -------------------- GET ACTIVE STAFF --------------------
@retry_mongo
async def get_all_staff() -> list:
    try:
        db = get_db()
        logger.debug("[MONGO] Fetching all active staff members")
        staff = await db.staff.find({"status": "active"}).to_list(length=100)
        return staff
    except Exception:
        logger.exception("[MONGO] Error fetching staff members.")
        return [{"error": "Error retrieving staff list."}]
