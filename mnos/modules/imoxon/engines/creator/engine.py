class CreatorEngine:
    def __init__(self, shadow, events):
        self.shadow = shadow
        self.events = events

    def publish_content(self, creator_id: str, content_type: str, metadata: dict):
        content = {
            "creator_id": creator_id,
            "type": content_type,
            "metadata": metadata,
            "status": "PUBLISHED"
        }
        self.shadow.commit("creator.content_published", content)
        self.events.publish("CONTENT_PUBLISHED", content)
        return content
