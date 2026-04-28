import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, UTC

def test_finalize_invoice_flow():
    from mnos.modules.fce.service import finalize_invoice
    from mnos.modules.fce.models import Folio, FolioStatus

    db_session = MagicMock()
    folio = Folio(id=1, status=FolioStatus.OPEN, base_amount=100.0, tenant_id="test")
    db_session.query.return_value.filter.return_value.first.return_value = folio

    # 100 + 10 (SC) + (110 * 0.08) (TGST) = 110 + 8.8 = 118.8
    with patch("mnos.core.audit.shadow.commit_shadow_evidence"):
        result = finalize_invoice(db_session, 1, "sys@ut.mv")

    assert result["total_amount"] == 118.8
    assert "trace_id" in result

def test_sync_buffer_commit_before_clear():
    from mnos.core.db.sync_buffer import SyncBuffer
    buf = SyncBuffer()
    buf._buffer = [{"trace_id": "t1", "payload": {}}]
    db = MagicMock()
    db.commit.side_effect = Exception("DB error")

    with pytest.raises(Exception):
        buf.process_sync(db)
    assert len(buf._buffer) == 1  # 🔒 BUFFER PRESERVED ON ROLLBACK
