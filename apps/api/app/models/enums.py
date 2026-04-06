from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    REVIEWER = "reviewer"
    CONTRIBUTOR = "contributor"
    VIEWER = "viewer"


class InputType(StrEnum):
    PASTE_TEXT = "paste_text"
    PDF = "pdf"


class CheckStatus(StrEnum):
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    ERROR = "error"


class Verdict(StrEnum):
    SAFE = "safe"
    VERIFY = "verify"
    BLOCKED = "blocked"


class Decision(StrEnum):
    APPROVED = "approved"
    HELD = "held"
    REJECTED = "rejected"


class SignalSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
