import re
from typing import List, Tuple

EMERGENCY_KEYWORDS = [
    r"chest pain",
    r"difficulty breathing",
    r"shortness of breath",
    r"suicidal",
    r"kill myself",
    r"anaphylaxis",
    r"severe allergic reaction",
    r"seizure",
    r"unconscious",
    r"cannot wake up",
    r"heavy bleeding",
    r"poisoning"
]

DANGEROUS_REQUESTS = [
    r"should i stop",
    r"can i stop",
    r"stop taking",
    r"double dose",
    r"extra dose",
    r"take twice",
    r"change my dose",
    r"increase my dose",
    r"decrease my dose"
]

def check_for_emergency(text: str) -> Tuple[bool, str]:
    """
    Checks if the user input contains any emergency keywords.
    Returns (is_emergency, warning_message).
    """
    text_lower = text.lower()
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, text_lower):
            return True, "EMERGENCY DETECTED: Please stop using this app and call 911 or go to the nearest emergency room immediately."
    return False, ""

def check_for_dangerous_request(text: str) -> Tuple[bool, str]:
    """
    Checks if the user is asking to change or stop medication.
    Returns (is_dangerous, guidance_message).
    """
    text_lower = text.lower()
    for pattern in DANGEROUS_REQUESTS:
        if re.search(pattern, text_lower):
            return True, "You should never change or stop your medication without consulting your prescribing physician. Please contact your doctor or pharmacist for guidance on your treatment plan."
    return False, ""
