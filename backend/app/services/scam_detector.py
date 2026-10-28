import re
import logging
from typing import Dict, Any, List, Tuple

# ML classifier — lazy-loaded, fails gracefully
try:
    from app.ml.nlp_classifier import classify_scam as _ml_classify
    _ML_AVAILABLE = True
except Exception:
    _ML_AVAILABLE = False
    _ml_classify = None  # type: ignore

logger = logging.getLogger(__name__)

# Structured pattern definitions with tactic categorization and severity weights
TACTIC_DEFINITIONS: List[Tuple[str, float, str]] = [
    # (regex_pattern, severity_weight, tactic_category)
    # Critical Coercion & Intimidation
    (r"\bsend\s+money\s+immediately\b", 0.95, "Urgent Financial Coercion"),
    (r"\btransfer\s+funds?\s+now\b", 0.95, "Urgent Financial Coercion"),
    (r"\byour\s+account\s+will\s+be\s+(blocked|suspended|closed|terminated|frozen)\b", 0.90, "Account Threat / Freeze"),
    (r"\bdon'?t\s+hang\s+up\b", 0.85, "Call Retention Pressure"),
    (r"\byou\s+will\s+be\s+arrested\b", 0.92, "Legal Intimidation"),
    (r"\bwarrant\s+(has\s+been\s+issued|out\s+for\s+your\s+arrest)\b", 0.92, "Legal Intimidation"),
    (r"\byour\s+social\s+security\s+number\s+has\s+been\s+suspended\b", 0.92, "Government Identity Threat"),
    (r"\birs\b.*\b(owe|debt|legal\s+action|lawsuit)\b", 0.88, "Government Impersonation"),

    # Tech Support Exploits
    (r"\bwindows\s+defender\s+(alert|warning)\b", 0.85, "Tech Support Impersonation"),
    (r"\bmicrosoft\s+technical\s+support\b", 0.85, "Tech Support Impersonation"),
    (r"\bvirus\s+detected\s+on\s+your\s+computer\b", 0.88, "Fake Malware Warning"),
    (r"\bdownload\s+(anydesk|teamviewer|ultraviewer|quick\s+assist)\b", 0.95, "Remote Access Takeover"),
    (r"\bgive\s+me\s+remote\s+access\b", 0.92, "Remote Access Takeover"),

    # Untraceable Payment Demands
    (r"\bgo\s+to\s+a\s+bitcoin\s+atm\b", 0.98, "Cryptocurrency Extraction"),
    (r"\b(bitcoin|crypto)\s+(atm|kiosk|deposit)\b", 0.95, "Cryptocurrency Extraction"),
    (r"\bwithdraw\s+cash\s+and\s+deposit\b", 0.95, "Cash Extraction"),
    (r"\b(gift\s+card|google\s+play|itunes|apple\s+gift|target\s+card|steam\s+card)\s+(payment|pay|code)\b", 0.90, "Gift Card Demands"),
    (r"\bzelle\s+payment\b", 0.70, "Instant Transfer Demand"),
    (r"\bwire\s+transfer\b", 0.75, "Wire Transfer Demand"),
    (r"\bsafe\s+wallet\b", 0.85, "Fraudulent Safe Wallet"),

    # Information & Credential Harvesting
    (r"\bprovide\s+your\s+(credit\s+card|bank\s+account|routing\s+number|pin)\b", 0.88, "Credential Harvesting"),
    (r"\bverify\s+your\s+(account|identity|credit\s+card|ssn)\b", 0.65, "Identity Verification Request"),
    (r"\b(one-time\s+password|verification\s+code|otp)\b", 0.80, "MFA / OTP Harvesting"),

    # Isolation & Secrecy
    (r"\bdo\s+not\s+tell\s+(anyone|your\s+family|the\s+teller)\b", 0.90, "Victim Isolation"),
    (r"\bkeep\s+this\s+confidential\b", 0.80, "Victim Isolation"),

    # Emergency / Family Impersonation
    (r"\bi\s+am\s+in\s+jail\b", 0.88, "Emergency Impersonation"),
    (r"\bpleas?e\s+don'?t\s+tell\s+(mom|dad|my\s+parents)\b", 0.90, "Emergency Impersonation"),
    (r"\bi\s+need\s+bail\s+money\b", 0.92, "Emergency Impersonation"),
    (r"\bcar\s+accident\s+need\s+cash\b", 0.88, "Emergency Impersonation"),

    # Advance-Fee / Fake Prize
    (r"\bcongratulations[!,]?\s+you\s+(have\s+)?(won|been\s+selected)\b", 0.70, "Prize / Lottery Lure"),
    (r"\b(lottery|sweepstakes|grand\s+prize)\s+(winner|won|award)\b", 0.75, "Prize / Lottery Lure"),
    (r"\btax\s+refund\b", 0.55, "Tax Refund Bait"),

    # Moderate Urgency / Commercial Phrasing (Low to Moderate Risk)
    (r"\bact\s+now\b", 0.45, "Urgency Language"),
    (r"\burgent\s+(action|matter)\b", 0.60, "Urgency Language"),
    (r"\bfinal\s+(notice|warning)\b", 0.70, "Urgency Language"),
    (r"\bimmediate\s+(action|payment)\b", 0.75, "Urgency Language"),
    (r"\byou\s+owe\b", 0.50, "Debt Claim"),
    (r"\boverdue\s+payment\b", 0.55, "Debt Claim"),
    (r"\bback\s+taxes\b", 0.65, "Tax Debt Claim"),
    (r"\blimited\s+time\b", 0.30, "Promotional Urgency"),
    (r"\bspecial\s+offer\b", 0.20, "Promotional Urgency"),
]

# Compile patterns for efficiency
COMPILED_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), weight, category, pattern)
    for pattern, weight, category in TACTIC_DEFINITIONS
]


def _normalize_text(text: str) -> str:
    """Clean and normalize input text."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


async def detect_scam_tactics(transcript: str) -> Dict[str, Any]:
    """
    Analyze transcript for scam tactics using explainable pattern categories
    and calibrated contextual NLP blending.
    """
    if not transcript or len(transcript.strip()) < 5:
        return {
            "urgency_detected": False,
            "urgency_score": 0.0,
            "phrases_found": [],
            "tactics_detected": [],
            "ml_scam_probability": 0.0,
        }

    normalized = _normalize_text(transcript)
    phrases_found: List[str] = []
    tactics_detected: List[str] = []
    category_max_weights: Dict[str, float] = {}

    for compiled_pattern, weight, category, _ in COMPILED_PATTERNS:
        matches = compiled_pattern.findall(normalized)
        if matches:
            for match in matches:
                phrase = match if isinstance(match, str) else " ".join(filter(None, match))
                if phrase and phrase not in phrases_found:
                    phrases_found.append(phrase)
            if category not in tactics_detected:
                tactics_detected.append(category)
            category_max_weights[category] = max(category_max_weights.get(category, 0.0), weight)

    if not category_max_weights:
        pattern_score = 0.0
    else:
        # Base score is the highest individual matched category weight
        base_score = max(category_max_weights.values())
        num_categories = len(category_max_weights)

        # Multi-category synergy: distinct tactics appearing together represent high threat
        if num_categories > 1:
            synergy_bonus = min(0.08 * (num_categories - 1), 0.20)
            pattern_score = min(base_score + synergy_bonus, 1.0)
        else:
            pattern_score = base_score

    # ── ML blending ──────────────────────────────────────────────────────────
    ml_prob = 0.0
    if _ML_AVAILABLE and _ml_classify is not None:
        try:
            ml_result = await _ml_classify(transcript)
            ml_prob = ml_result.get("scam_probability", 0.0)
            # Both signals are now calibrated contextual scores
            if pattern_score > 0 and ml_prob > 0:
                final_score = round(0.5 * ml_prob + 0.5 * pattern_score, 4)
            elif pattern_score > 0:
                final_score = round(pattern_score, 4)
            else:
                final_score = round(ml_prob, 4)
        except Exception as e:
            logger.warning(f"ML classifier failed, using pattern only: {e}")
            final_score = round(pattern_score, 4)
    else:
        final_score = round(pattern_score, 4)

    # Threshold for positive scam urgency detection
    urgency_detected = final_score >= 0.40

    logger.info(
        f"Scam detection: pattern={pattern_score:.3f}, ml={ml_prob:.3f}, "
        f"final={final_score:.3f}, detected={urgency_detected}, tactics={tactics_detected}"
    )

    return {
        "urgency_detected": urgency_detected,
        "urgency_score": final_score,
        "phrases_found": phrases_found[:10],
        "tactics_detected": tactics_detected,
        "ml_scam_probability": round(ml_prob, 4),
    }
