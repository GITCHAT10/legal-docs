class SovereignException(Exception):
    """Base exception for OGX sovereignty violations."""
    pass

class SecurityException(SovereignException):
    """Raised when identity or device trust verification fails."""
    pass

class FinancialException(SovereignException):
    """Raised when pre-authorization or payment fails."""
    pass
