from mnos.modules.prestige.brief.brief_models import PrestigeBrief

class BriefRenderer:
    def render_html(self, brief: PrestigeBrief) -> str:
        # Simple mock renderer
        return f"<html><body><h1>{brief.brief_type}</h1><p>Guest: {brief.guest_name}</p></body></html>"

    def render_json(self, brief: PrestigeBrief) -> dict:
        return brief.model_dump()
