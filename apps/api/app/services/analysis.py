"""Deterministic stub analysis for paste-text checks.

This module will be replaced by OpenAI integration in a later slice.
All logic here is keyword-based and intentionally simple.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field


@dataclass
class ExtractedFields:
    vendor_name: str | None = None
    vendor_contact_email: str | None = None
    vendor_contact_phone: str | None = None
    bank_name: str | None = None
    bank_account_raw: str | None = None
    bank_routing_raw: str | None = None


@dataclass
class Signal:
    signal_type: str
    severity: str
    title: str
    description: str


@dataclass
class AnalysisResult:
    vendor_name: str | None = None
    vendor_contact_email: str | None = None
    vendor_contact_phone: str | None = None
    bank_name: str | None = None
    bank_account_hash: str | None = None
    bank_routing_hash: str | None = None
    bank_account_masked: str | None = None
    bank_routing_masked: str | None = None
    verdict: str = "safe"
    verdict_explanation: str = ""
    recommended_action: str = ""
    risk_score: int = 0
    signals: list[Signal] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_ACCOUNT_RE = re.compile(r"(?:account|acct)[#:\s]*(\d[\d\s-]{4,})", re.IGNORECASE)
_ROUTING_RE = re.compile(r"(?:routing|aba|aba/routing)[#:\s]*(\d{9})", re.IGNORECASE)

_BANK_NAMES = [
    "chase", "bank of america", "wells fargo", "citibank", "citi",
    "us bank", "pnc", "capital one", "td bank", "regions",
    "truist", "fifth third", "huntington", "m&t bank", "key bank",
]

_URGENCY_WORDS = [
    "urgent", "immediately", "asap", "right away", "time-sensitive",
    "as soon as possible", "critical", "deadline", "overdue", "rush",
]

_BANK_CHANGE_PHRASES = [
    "updated bank", "new bank", "changed bank", "new account",
    "updated account", "change bank", "new routing", "updated routing",
    "switch bank", "different account", "revised bank", "bank details have changed",
    "account information has been updated",
]


def _normalize_for_hash(value: str) -> str:
    """Strip whitespace, dashes, spaces, lowercase — per locked hashing spec."""
    return re.sub(r"[\s-]", "", value).lower()


def _hash_value(value: str) -> str:
    normalized = _normalize_for_hash(value)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _mask_value(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) <= 4:
        return f"****{digits}"
    return f"****{digits[-4:]}"


def _extract_fields(text: str) -> ExtractedFields:
    fields = ExtractedFields()

    # Email
    emails = _EMAIL_RE.findall(text)
    if emails:
        fields.vendor_contact_email = emails[0]

    # Phone
    phones = _PHONE_RE.findall(text)
    if phones:
        fields.vendor_contact_phone = phones[0]

    # Bank account
    acct_match = _ACCOUNT_RE.search(text)
    if acct_match:
        fields.bank_account_raw = re.sub(r"\s", "", acct_match.group(1)).strip("-")

    # Routing number
    routing_match = _ROUTING_RE.search(text)
    if routing_match:
        fields.bank_routing_raw = routing_match.group(1)

    # Bank name
    text_lower = text.lower()
    for bank in _BANK_NAMES:
        if bank in text_lower:
            fields.bank_name = bank.title()
            break

    # Vendor name — use the first line as a heuristic (common in pasted vendor letters)
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if lines:
        first_line = lines[0]
        # If the first line looks like a name/company (short, no email/URL)
        if len(first_line) < 80 and "@" not in first_line and "http" not in first_line.lower():
            fields.vendor_name = first_line
        else:
            fields.vendor_name = "Unknown Vendor"
    else:
        fields.vendor_name = "Unknown Vendor"

    return fields


# ---------------------------------------------------------------------------
# Signal detection
# ---------------------------------------------------------------------------

def _detect_signals(text: str, fields: ExtractedFields) -> list[Signal]:
    signals: list[Signal] = []
    text_lower = text.lower()

    # Urgency language
    found_urgency = [w for w in _URGENCY_WORDS if w in text_lower]
    if found_urgency:
        signals.append(Signal(
            signal_type="urgency_language",
            severity="medium",
            title="Urgency language detected",
            description=f"Request contains urgency indicators: {', '.join(found_urgency)}.",
        ))

    # Bank change phrases
    found_bank_change = [p for p in _BANK_CHANGE_PHRASES if p in text_lower]
    if found_bank_change:
        signals.append(Signal(
            signal_type="bank_change_detected",
            severity="high",
            title="Bank change request detected",
            description="The message explicitly mentions changing or updating bank details.",
        ))

    # Domain mismatch (vendor name vs email domain)
    if fields.vendor_contact_email and fields.vendor_name:
        email_domain = fields.vendor_contact_email.split("@")[-1].lower()
        vendor_lower = fields.vendor_name.lower()
        # Check if the vendor name words appear in the email domain
        free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"}
        if email_domain in free_domains:
            signals.append(Signal(
                signal_type="domain_mismatch",
                severity="medium",
                title="Email uses free provider",
                description=f"Contact email uses {email_domain}, not a company domain.",
            ))

    # Missing fields
    missing = []
    if not fields.vendor_name or fields.vendor_name == "Unknown Vendor":
        missing.append("vendor name")
    if not fields.bank_account_raw:
        missing.append("bank account number")
    if not fields.bank_routing_raw:
        missing.append("routing number")
    if missing:
        signals.append(Signal(
            signal_type="missing_fields",
            severity="low",
            title="Missing expected fields",
            description=f"Could not extract: {', '.join(missing)}.",
        ))

    return signals


# ---------------------------------------------------------------------------
# Verdict computation
# ---------------------------------------------------------------------------

def _compute_verdict(signals: list[Signal]) -> tuple[str, int]:
    """Return (verdict, risk_score) based on signal severities."""
    severity_scores = {"low": 10, "medium": 25, "high": 40, "critical": 60}
    total = sum(severity_scores.get(s.severity, 0) for s in signals)
    score = min(total, 100)

    if score >= 60:
        return "blocked", score
    elif score >= 30:
        return "verify", score
    else:
        return "safe", score


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def analyze_paste_text(text: str) -> AnalysisResult:
    """Run deterministic stub analysis on pasted text. No LLM call."""
    fields = _extract_fields(text)
    signals = _detect_signals(text, fields)
    verdict, risk_score = _compute_verdict(signals)

    # Build explanation and recommendation
    if verdict == "blocked":
        explanation = "Multiple high-risk indicators detected. This request should be blocked pending manual verification."
        action = "Do not process this payment. Contact the vendor using a known phone number to verify the request."
    elif verdict == "verify":
        explanation = "Some risk indicators were found. Verify the details before processing."
        action = "Contact the vendor directly using previously known contact information to confirm the bank change."
    else:
        explanation = "No significant risk indicators detected."
        action = "This request appears safe to process. Follow standard approval procedures."

    return AnalysisResult(
        vendor_name=fields.vendor_name,
        vendor_contact_email=fields.vendor_contact_email,
        vendor_contact_phone=fields.vendor_contact_phone,
        bank_name=fields.bank_name,
        bank_account_hash=_hash_value(fields.bank_account_raw) if fields.bank_account_raw else None,
        bank_routing_hash=_hash_value(fields.bank_routing_raw) if fields.bank_routing_raw else None,
        bank_account_masked=_mask_value(fields.bank_account_raw) if fields.bank_account_raw else None,
        bank_routing_masked=_mask_value(fields.bank_routing_raw) if fields.bank_routing_raw else None,
        verdict=verdict,
        verdict_explanation=explanation,
        recommended_action=action,
        risk_score=risk_score,
        signals=signals,
    )
