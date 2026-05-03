from enum import Enum

class QuoteStatus(str, Enum):
    PENDING = "pending"
    PENDING_HUMAN_VERIFICATION = "pending_human_verification"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVISION_REQUESTED = "revision_requested"
    FAILED = "failed"
    NO_QUOTE = "no_quote"
