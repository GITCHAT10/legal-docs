import pytest
from mnos.modules.shadow.service import shadow
from mnos.modules.knowledge.service import knowledge_core

@pytest.fixture(autouse=True)
def reset_system():
    # Reset SHADOW
    shadow.chain = []
    shadow._seed_ledger()
    # Reset Knowledge
    knowledge_core.db = {}
