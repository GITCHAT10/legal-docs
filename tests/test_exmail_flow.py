import pytest
import os
from mnos.modules.exmail.service import ExMailService
from mnos.modules.exmail.adapter_mailchimp import MailchimpAdapter
from mnos.modules.orca_sales.engine import OrcaSalesEngine
from main import shadow_core, guard, events_core

@pytest.fixture
def exmail_stack():
    orca_sales = OrcaSalesEngine(shadow_core, guard)
    adapter = MailchimpAdapter("test_key", "test_secret")
    service = ExMailService(guard, shadow_core, events_core, orca_sales, adapter)
    return service, orca_sales

def test_exmail_webhook_to_crm_flow(exmail_stack):
    service, orca_sales = exmail_stack
    email = "lead@maldives-resort.mv"

    # 1. Ingest 'opened' event
    service.process_webhook_event({
        "email": email,
        "event": "opened",
        "campaign": "MALDIVES_SPRING_2026",
        "timestamp": "2026-01-01T10:00:00Z"
    })
    assert orca_sales.leads[email] == "CONTACTED"

    # 2. Ingest 'replied' event (triggers Irina's task)
    service.process_webhook_event({
        "email": email,
        "event": "replied",
        "campaign": "MALDIVES_SPRING_2026",
        "timestamp": "2026-01-01T12:00:00Z"
    })
    assert orca_sales.leads[email] == "IN TALKS"

    # Verify sales task created for Irina
    irina_tasks = orca_sales.get_tasks_for("Irina Rogova")
    assert len(irina_tasks) == 1
    assert irina_tasks[0]["email"] == email
    assert irina_tasks[0]["priority"] == "HIGH"

def test_exmail_shadow_audit(exmail_stack):
    service, _ = exmail_stack
    initial_chain_len = len(shadow_core.chain)

    service.process_webhook_event({
        "email": "audit@test.com",
        "event": "clicked",
        "campaign": "AUDIT_2026",
        "timestamp": "2026-02-02T15:00:00Z"
    })

    # +2 commits: 1 from exmail service, 1 from orca_sales lead update
    assert len(shadow_core.chain) == initial_chain_len + 2
    assert shadow_core.chain[-2]["event_type"] == "exmail.event.clicked"
    assert shadow_core.chain[-1]["event_type"] == "sales.lead.updated"
    assert shadow_core.verify_integrity() is True
