
class TenantGuard:
    @staticmethod
    def validate_isolation(source_event: dict, target_tenant: dict) -> bool:
        """
        ISOLATION blocks cross-brand and cross-TIN leakage.
        """
        event_tenant = source_event.get("context", {}).get("tenant", {})

        if not event_tenant or not target_tenant:
            return False

        if event_tenant.get("tin") != target_tenant.get("tin"):
            return False

        if event_tenant.get("brand") != target_tenant.get("brand"):
            return False

        return True

    @staticmethod
    def check_cross_tin_settlement(payer_tin: str, payee_tin: str) -> bool:
        # Cross-TIN settlement must fail closed if not authorized
        return payer_tin == payee_tin
