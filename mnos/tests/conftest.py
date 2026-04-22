import pytest
from mnos.modules.shadow.service import shadow
from mnos.modules.knowledge.service import knowledge_core

@pytest.fixture(autouse=True)
def reset_system_state():
    """Resets global system state between tests to ensure isolation."""
    shadow.chain = []
    shadow._seed_ledger()
    # Reset knowledge core or other singletons if needed
    knowledge_core.ingest("TEST_DNA", "Sovereign Core Active")
