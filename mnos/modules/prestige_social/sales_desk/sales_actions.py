from ..audit.shadow_quote_events import create_shadow_event

def generate_whatsapp_link(whatsapp_e164: str, guest_name: str, agent_name: str,
                           nights: int, guest_count: int, resort_name: str,
                           lead_id: str, quote_id: str, campaign_id: str,
                           human_agent_id: str, shadow_correlation_id: str):

    message = (
        f"Hello {guest_name}, this is {agent_name} from Prestige Holidays Maldives. "
        f"Thank you for your Maldives inquiry. I have your request here for {nights} nights, "
        f"{guest_count} guests, {resort_name}. I will send you the verified options and quote details now."
    )

    # URL encode message
    encoded_message = message.replace(" ", "%20").replace(",", "%2C")
    link = f"https://wa.me/{whatsapp_e164}?text={encoded_message}"

    # Log SHADOW event
    create_shadow_event(
        event_type="WHATSAPP_OPENED_BY_HUMAN",
        lead_id=lead_id,
        actor_type="human",
        actor_id=human_agent_id,
        parent_hash=shadow_correlation_id,
        correlation_id=shadow_correlation_id,
        payload={"quote_id": quote_id},
        quote_id=quote_id,
        campaign_id=campaign_id
    )

    return link
