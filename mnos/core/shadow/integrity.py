from mnos.modules.shadow.ledger import ShadowLedger

def verify_chain_integrity(ledger: ShadowLedger) -> bool:
    return ledger.verify_integrity()
