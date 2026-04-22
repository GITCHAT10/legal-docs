class LifeEngine:
    def __init__(self, shadow):
        self.shadow = shadow

    def save_recipe(self, user_id: str, recipe: dict):
        self.shadow.record_action("life.recipe_saved", {"user": user_id, "recipe": recipe["name"]})

    def log_meditation(self, user_id: str, duration: int):
        self.shadow.record_action("life.meditation_logged", {"user": user_id, "duration": duration})

    def home_management_alert(self, user_id: str, alert: str):
        self.shadow.record_action("life.home_alert", {"user": user_id, "alert": alert})
        return True
