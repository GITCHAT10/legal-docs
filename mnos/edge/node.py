class EdgeNode:
    def __init__(self, node_id, type):
        self.node_id = node_id
        self.queue = []
        self.is_online = True
    def execute(self, action, payload):
        if not self.is_online: self.queue.append(payload); return {"status": "queued"}
        return {"status": "executed"}
    def sync(self): self.queue = []; return {"synced": 1}
