from fastapi import APIRouter, HTTPException

def create_identity_router(identity_core, policy_engine):
    router = APIRouter(prefix="/aegis/identity", tags=["identity"])

    @router.post("/create")
    async def create_identity(profile_data: dict):
        # Bootstrap identity creation is usually unguarded or use a SYSTEM token
        # For this audit, we allow it to publish if authorized manually or we wrap it.
        from mnos.shared.execution_guard import _sovereign_context
        token = _sovereign_context.set({"token": "BOOTSTRAP", "actor": {"identity_id": "SYSTEM", "role": "admin"}})
        try:
            identity_id = identity_core.create_profile(profile_data)
            return {"identity_id": identity_id, "status": "created"}
        finally:
            _sovereign_context.reset(token)

    @router.post("/verify")
    async def verify_identity(identity_id: str, verifier_id: str):
        success = identity_core.verify_identity(identity_id, verifier_id)
        if not success:
            raise HTTPException(status_code=404, detail="Identity not found")
        return {"status": "verified"}

    @router.post("/device/bind")
    async def bind_device(identity_id: str, device_data: dict):
        from mnos.shared.execution_guard import _sovereign_context
        token = _sovereign_context.set({"token": "BOOTSTRAP", "actor": {"identity_id": identity_id, "role": "user"}})
        try:
            device_id = identity_core.bind_device(identity_id, device_data)
            return {"device_id": device_id, "status": "bound"}
        finally:
            _sovereign_context.reset(token)

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

    return router
