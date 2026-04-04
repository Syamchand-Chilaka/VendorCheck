from enum import StrEnum


class SignalType(StrEnum):
    BANK_CHANGE_DETECTED = "bank_change_detected"
    NEW_VENDOR = "new_vendor"
    DOMAIN_MISMATCH = "domain_mismatch"
    URGENCY_LANGUAGE = "urgency_language"
    FORMATTING_ANOMALY = "formatting_anomaly"
    CONTACT_INFO_CHANGED = "contact_info_changed"
    MISSING_FIELDS = "missing_fields"
    AI_RISK_FLAG = "ai_risk_flag"
