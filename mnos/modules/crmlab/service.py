class CrmLabAuthority:
    def get_guest_profile(self, guest_id: str):
        return {"guest_id": guest_id, "tier": "VVIP"}

crmlab = CrmLabAuthority()
