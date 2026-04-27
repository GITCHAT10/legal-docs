import re

class PdpaRedactor:
    """
    Maldives PDPA Compliance: Data Redactor.
    Masks sensitive personal information from logs and exports.
    """
    def __init__(self):
        # Sensitive patterns
        self.id_pattern = re.compile(r'\b[A-Z]\d{6}\b') # Example Maldives ID format
        self.phone_pattern = re.compile(r'\b\+960\d{7}\b')

    def redact_text(self, text: str) -> str:
        text = self.id_pattern.sub("[ID-REDACTED]", text)
        text = self.phone_pattern.sub("[PHONE-REDACTED]", text)
        return text

    def redact_payload(self, payload: dict) -> dict:
        redacted = {}
        for k, v in payload.items():
            if isinstance(v, str):
                redacted[k] = self.redact_text(v)
            elif isinstance(v, dict):
                redacted[k] = self.redact_payload(v)
            else:
                redacted[k] = v
        return redacted
