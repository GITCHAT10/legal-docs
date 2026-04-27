from typing import Dict, Optional

class MultilingualChatEngine:
    """
    AIR CHAT™ Multilingual Support: Dhivehi, English, Arabic.
    Enables sovereign communication for staff and guests.
    """
    def __init__(self):
        self.translations = {
            "invoice_ready": {
                "en": "Your invoice is ready for review.",
                "dv": "ތިޔަބޭފުޅާގެ އިންވޮއިސް ތައްޔާރުވެއްޖެ.",
                "ar": "فاتورتك جاهزة للمراجعة."
            },
            "delivery_confirmed": {
                "en": "Delivery confirmed and settled.",
                "dv": "ޑެލިވަރީ ކަށަވަރުކޮށް ސެޓްލް ކުރެވިއްޖެ.",
                "ar": "تم تأكيد التسليم وتسويته."
            }
        }

    def get_message(self, key: str, lang: str = "en") -> str:
        return self.translations.get(key, {}).get(lang, self.translations.get(key, {}).get("en", "Message not found."))

    def format_rtl(self, text: str, lang: str) -> str:
        # Simplified RTL formatting logic
        if lang in ["dv", "ar"]:
            return f"\u202b{text}\u202c"
        return text
