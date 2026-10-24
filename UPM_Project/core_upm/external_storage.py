from os import name
import uuid
import logging

logger = logging.getLogger(name)

# Dictionary to simulate a NoSQL database or a cloud storage bucket
_EXTERNAL_STORAGE = {} 

def save_code_content(content: str) -> str:
    """
    Simulates saving code content externally (e.g., S3, MongoDB) 
    and returns a unique reference key (UUID).
    """
    ref_key = str(uuid.uuid4())
    _EXTERNAL_STORAGE[ref_key] = content
    logger.info(f"External Storage: Content saved with ref_key: {ref_key}")
    return ref_key

def fetch_code_content(ref_key: str) -> str:
    """
    Simulates fetching code content from the external storage using the reference key.
    """
    logger.info(f"External Storage: Attempting fetch for ref_key: {ref_key}")
    return _EXTERNAL_STORAGE.get(ref_key, "Error: Content not found in external storage.")