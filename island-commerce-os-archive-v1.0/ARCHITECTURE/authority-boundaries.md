# ⚖️ Authority Boundaries & Sovereign Security Rules

1. **Isolation of Payment Authority**: Only the BUBBLE WALLET service can release funds or debit guest balances.
2. **Deterministic Tax Enforcement**: Tax logic (TGST/SC/GST) is hardcoded into the database level via triggers and verified by the Wallet layer.
3. **Zero Client Trust**: All pricing, tax calculations, and identity resolution occur server-side.
4. **Immutable Audit Persistence**: Every state-changing action must produce a SHADOW LEDGER entry before execution success is returned to the user.
