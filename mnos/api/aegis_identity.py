from fastapi import APIRouter, HTTPException


def create_identity_router(identity_core, policy_engine, gateway=None):
    router = APIRouter(prefix="/aegis/identity", tags=["identity"])

    @router.post("/create")
    async def create_identity(profile_data: dict):
        # Bootstrap identity creation is usually unguarded or use a SYSTEM token
        # For this audit, we allow it to publish if authorized manually or we wrap it.
        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.authorized_context({"identity_id": "SYSTEM", "role": "admin"}):
            identity_id = identity_core.create_profile(profile_data)
            return {"identity_id": identity_id, "status": "created"}

    @router.post("/verify")
    async def verify_identity(identity_id: str, verifier_id: str):
        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.authorized_context({"identity_id": verifier_id, "role": "admin"}):
            success = identity_core.verify_identity(identity_id, verifier_id)
            if not success:
                raise HTTPException(status_code=404, detail="Identity not found")
            return {"status": "verified"}

    @router.post("/device/bind")
    async def bind_device(identity_id: str, device_data: dict):
        from mnos.shared.execution_guard import ExecutionGuard
        with ExecutionGuard.authorized_context({"identity_id": identity_id, "role": "user"}):
            device_id = identity_core.bind_device(identity_id, device_data)
            return {"device_id": device_id, "status": "bound"}

    @router.post("/role/assign")
    async def assign_role(identity_id: str, role_name: str, scope: dict):
        binding_id = identity_core.assign_role(identity_id, role_name, scope)
        return {"binding_id": binding_id, "status": "assigned"}

    @router.post("/asset/bind")
    async def bind_asset(identity_id: str, asset_type: str, asset_ref: str):
        # Validate via policy
        valid, msg = policy_engine.validate_action("asset_assignment", {"identity_id": identity_id})
        if not valid:
            raise HTTPException(status_code=403, detail=msg)

        binding_id = identity_core.bind_asset(identity_id, asset_type, asset_ref)
        return {"binding_id": binding_id, "status": "bound"}

    @router.get("/{identity_id}")
    async def get_identity(identity_id: str):
        profile = identity_core.profiles.get(identity_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Identity not found")
        return profile

    @router.post("/login")
    async def login(realm: str, auth_method: str, credentials: dict):
        """Unified AEGIS Gateway Entry."""
        if not gateway:
            raise HTTPException(status_code=501, detail="Identity Gateway not initialized")
        try:
            return gateway.login(realm, auth_method, credentials)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router
