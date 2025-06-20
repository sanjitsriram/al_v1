# backend/utils/helpers.py

"""
Helper utilities for formatting and cleaning data before display.
"""

from bson import ObjectId

# ---------------------- OBJECTID CONVERTER ----------------------

def clean_mongo_object(obj):
    """
    Recursively converts ObjectId and other non-serializable fields
    to string format so they can be passed to frontend or GPT.
    """
    if isinstance(obj, dict):
        return {k: clean_mongo_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_mongo_object(i) for i in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj
