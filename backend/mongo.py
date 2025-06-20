"""
Asynchronous MongoDB access layer using Motor.
Handles patient records, appointments, staff queries, and field‑based lookups for
admissions, lab applications, diagnosis, prescriptions, and notes.
"""

import logging
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import PyMongoError
from backend.config import MONGO_URI, MONGO_DB_NAME
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.FileHandler("logs/chatbot.log")
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

_clients = {}

def get_db():
    loop = asyncio.get_event_loop()
    if loop not in _clients:
        logger.debug("[MONGO] Initializing AsyncIOMotorClient for current event loop.")
        _clients[loop] = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _clients[loop][MONGO_DB_NAME]

retry_mongo = retry(stop=stop_after_attempt(3),
                    wait=wait_fixed(1),
                    retry=retry_if_exception_type(PyMongoError))

@retry_mongo
async def get_patient_history(name: str) -> dict:
    db = get_db()
    logger.debug(f"[MONGO] Searching for patient name: {name}")
    patient = await db.patients.find_one({"name": {"$regex": name, "$options": "i"}})
    if not patient:
        logger.info(f"[MONGO] No patient found with name: {name}")
        return {"error": "Patient not found."}
    pid = patient.get("patient_id")
    admissions = await db.admissions.find({"patient_id": pid}).to_list(100)
    prescriptions = await db.prescriptions.find({"patient_id": pid}).to_list(100)
    diagnoses = await db.diagnosis_icd.find({"patient_id": pid}).to_list(100)
    labs = await db.application.find({"patient_id": pid}).to_list(100)
    notes = await db.noteevents.find({"patient_id": pid}).to_list(100)
    return {
        "patient": patient,
        "admissions": admissions,
        "prescriptions": prescriptions,
        "diagnoses": diagnoses,
        "lab_applications": labs,
        "notes": notes
    }

@retry_mongo
async def get_patient_dob(name: str) -> dict:
    db = get_db()
    patient = await db.patients.find_one({"name": {"$regex": name, "$options": "i"}}, {"dob": 1, "name": 1, "_id": 0})
    return patient or {"error": "Patient not found."}

@retry_mongo
async def get_patient_contact(name: str) -> dict:
    db = get_db()
    patient = await db.patients.find_one({"name": {"$regex": name, "$options": "i"}}, {"contact": 1, "name": 1, "_id": 0})
    return patient or {"error": "Patient not found."}

@retry_mongo
async def get_todays_appointments() -> list:
    db = get_db()
    today = datetime.today().strftime('%Y-%m-%d')
    return await db.appointments.find({"date": today}).to_list(100)

@retry_mongo
async def get_appointments_on_date(date_str: str) -> list:
    db = get_db()
    return await db.appointments.find({"date": date_str}).to_list(100)

@retry_mongo
async def get_all_staff() -> list:
    db = get_db()
    return await db.staff.find({"status": "active"}).to_list(100)

# New lookup functions
@retry_mongo
async def get_admissions_for_patient(pid: str) -> list:
    db = get_db()
    return await db.admissions.find({"patient_id": pid}).to_list(100)

@retry_mongo
async def get_lab_applications_for_patient(pid: str) -> list:
    db = get_db()
    return await db.application.find({"patient_id": pid}).to_list(100)

@retry_mongo
async def get_lab_items_list() -> list:
    db = get_db()
    return await db.d_labitems.find().to_list(100)

@retry_mongo
async def get_diagnosis_for_admission(aid: str) -> list:
    db = get_db()
    return await db.diagnosis_icd.find({"admission_id": aid}).to_list(100)

@retry_mongo
async def get_prescriptions_for_admission(aid: str) -> list:
    db = get_db()
    return await db.prescriptions.find({"admission_id": aid}).to_list(100)

@retry_mongo
async def get_notes_for_admission(aid: str) -> list:
    db = get_db()
    return await db.noteevents.find({"admission_id": aid}).to_list(100)

