# backend/main.py

import logging
from datetime import datetime, timedelta
import dateparser
from backend.nlp import detect_intent_and_entity
from backend.mongo import (
    get_patient_history,
    get_todays_appointments,
    get_appointments_on_date,
    get_all_staff,
    get_patient_dob,
    get_patient_contact
)
from backend.rag import generate_response

# -------------------- Logging Setup --------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.FileHandler("logs/chatbot.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# -------------------- Extended Intents --------------------
EXTRA_INTENTS = [
    "medication_interactions", "referral_status", "insurance_coverage",
    "treatment_plan_update", "immunization_status", "allergy_check",
    "vital_signs_history", "surgery_schedule", "radiology_reports",
    "billing_inquiry", "test_preparation", "post_op_followup",
    "mental_health_assessment", "nutrition_advice", "exercise_recommendation",
    "sleep_assessment", "smoking_cessation", "diabetes_management",
    "hypertension_management", "cardiology_consult", "neurology_consult",
    "oncology_update", "pediatrics_consult", "geriatrics_consult",
    "dermatology_consult", "ophthalmology_consult", "dental_consult",
    "otolaryngology_consult", "pulmonology_consult", "nephrology_consult",
    "hepatology_consult", "endocrinology_consult", "infusion_schedule",
    "infection_control", "antibiotic_review", "medication_adherence",
    "pregnancy_checkup", "postpartum_followup", "child_growth_monitoring",
    "mental_health_followup", "gynecology_consult", "urology_consult",
    "orthopedics_consult", "pulmonary_function_test", "sleep_study_results",
    "oncology_followup", "radiotherapy_schedule", "chemotherapy_status",
    "transplant_status", "clinical_trial_info", "genetics_counseling",
    "telehealth_setup", "emergency_protocol", "lab_order_status",
    "pharmacy_pickup", "physical_therapy_consult", "occupational_therapy_consult",
    "speech_therapy_consult", "home_care_arrangement","get_patient_dob"
]

# -------------------- Main Routing --------------------

async def process_query(user_query: str) -> str:
    logger.debug("[MAIN] Received query: %s", user_query)

    try:
        # NLP step
        intent, entity = detect_intent_and_entity(user_query)
        logger.debug("[MAIN] NLP result → intent: '%s', entity: '%s'", intent, entity)

        # ---- Appointments Today ----
        if intent in ("appointments_today", "appointments"):
            logger.debug("[MAIN] Routing to get_todays_appointments()")
            data = await get_todays_appointments()

        # ---- Appointments on Specific Date ----
        elif intent == "appointments_on_date":
            if not entity:
                logger.warning("[MAIN] No date provided by user.")
                return "⚠️ Please mention a specific date (e.g., 'appointments on 20th June')."

            parsed_date = None
            if entity.lower() == "tomorrow":
                parsed_date = datetime.today() + timedelta(days=1)
            elif entity.lower() == "today":
                parsed_date = datetime.today()
            else:
                parsed_date = dateparser.parse(entity)

            if not parsed_date:
                logger.warning("[MAIN] Could not parse entity as date: %s", entity)
                return "⚠️ Couldn't understand the date. Try formats like 'June 21st' or '2025-06-21'."

            date_str = parsed_date.strftime("%Y-%m-%d")
            logger.debug("[MAIN] Parsed date: %s", date_str)
            data = await get_appointments_on_date(date_str)

        # ---- Staff Info ----
        elif intent in ("staff", "staff_info"):
            logger.debug("[MAIN] Routing to get_all_staff()")
            data = await get_all_staff()

        # ---- Patient Info ----
        elif intent == "patient_info":
            if not entity:
                logger.warning("[MAIN] No patient name provided.")
                return "⚠️ Please provide a patient name (e.g., 'Show me details for Rahul Sharma')."
            logger.debug("[MAIN] Routing to get_patient_history('%s')", entity)
            data = await get_patient_history(entity)

        elif intent == "get_patient_dob":
            if not entity:
                return "⚠️ Please specify a patient's name to retrieve the date of birth."
            logger.debug("[MAIN] Routing to get_patient_dob('%s')", entity)
            data = await get_patient_dob(entity)


        # ---- Extended Intents (Stubbed) ----
        elif intent in EXTRA_INTENTS:
            logger.debug("[MAIN] Handling new intent: %s", intent)
            return f"⚠️ The feature for '{intent}' is under development."

        # ---- Unrecognized Intent ----
        else:
            logger.warning("[MAIN] Unrecognized intent: %s", intent)
            return (
                "🤖 Sorry, I didn’t understand that. "
                "Try asking about appointments, staff, or patient records."
            )

        # ---- RAG: Final response generation ----
        logger.debug("[MAIN] Sending context to RAG generator...")
        response = generate_response(user_query, data)
        logger.debug("[MAIN] Response ready.")
        return response

    except Exception as e:
        logger.exception("[MAIN] Exception occurred while processing query: %s", e)
        return (
            "❌ An internal error occurred while processing your request. "
            "Please try again later."
        )
