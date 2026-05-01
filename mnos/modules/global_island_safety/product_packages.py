from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ProductPackage:
    package_name: str
    target_customer: str
    included_systems: List[str]
    emergency_buttons: List[str]
    required_integrations: List[str]
    setup_price_range_usd: str
    monthly_saas_range_usd: str
    authority_access_model: str
    shadow_report_type: str

PRODUCT_PACKAGES: Dict[str, ProductPackage] = {
    "Resort Safety Node": ProductPackage(
        package_name="Resort Safety Node",
        target_customer="Resorts",
        included_systems=["Drone Station", "CCTV", "Emergency Dashboard"],
        emergency_buttons=["DROWNING", "MEDICAL", "FIRE_SMOKE", "MISSING_GUEST"],
        required_integrations=["AEGIS", "ORCA", "SHADOW"],
        setup_price_range_usd="150000-300000",
        monthly_saas_range_usd="12000-25000",
        authority_access_model="Resort triggers; Gov escalation available",
        shadow_report_type="RESORT_INCIDENT_REPORT"
    ),
    "Island Emergency Node": ProductPackage(
        package_name="Island Emergency Node",
        target_customer="Local Councils / Municipalities",
        included_systems=["Drone Station", "Emergency Dashboard", "Starlink Failover"],
        emergency_buttons=["MEDICAL", "STORM_DAMAGE", "EVACUATION_SUPPORT"],
        required_integrations=["MNDF", "CAA"],
        setup_price_range_usd="75000-150000",
        monthly_saas_range_usd="5000-10000",
        authority_access_model="Council reports; Central command approves",
        shadow_report_type="DISASTER_DAMAGE_REPORT"
    ),
    "Coastal Disaster Response Node": ProductPackage(
        package_name="Coastal Disaster Response Node",
        target_customer="Disaster Agencies",
        included_systems=["Drone Station", "CCTV", "Mobile Command Unit"],
        emergency_buttons=["STORM_DAMAGE", "FLOOD_MONITORING", "SEARCH_AND_RESCUE"],
        required_integrations=["Coast Guard", "NDMA"],
        setup_price_range_usd="125000-350000",
        monthly_saas_range_usd="10000-30000",
        authority_access_model="Central Agency control",
        shadow_report_type="DISASTER_DAMAGE_REPORT"
    ),
    "Smart Port Safety Node": ProductPackage(
        package_name="Smart Port Safety Node",
        target_customer="Port Authorities",
        included_systems=["CCTV", "Drone Patrol", "Crowd Risk Monitor"],
        emergency_buttons=["FIRE_SMOKE", "JETTY_BOAT_INCIDENT", "SECURITY_ALERT"],
        required_integrations=["Port Security", "Customs"],
        setup_price_range_usd="250000-750000",
        monthly_saas_range_usd="25000-75000",
        authority_access_model="Port Control Command",
        shadow_report_type="MARITIME_INCIDENT_REPORT"
    ),
    "Public Safety CCTV + Drone Node": ProductPackage(
        package_name="Public Safety CCTV + Drone Node",
        target_customer="Police / Public Safety Agencies",
        included_systems=["CCTV Network", "Drone Patrol", "Case Evidence Export"],
        emergency_buttons=["SECURITY_ALERT", "TRAFFIC_INCIDENT", "CROWD_RISK"],
        required_integrations=["Police HQ", "AEGIS"],
        setup_price_range_usd="150000-500000",
        monthly_saas_range_usd="15000-50000",
        authority_access_model="Police role-based access",
        shadow_report_type="POLICE_CASE_EVIDENCE_EXPORT"
    ),
    "Luxury Island Safety Node": ProductPackage(
        package_name="Luxury Island Safety Node",
        target_customer="Private Islands / Ultra-Luxury Resorts",
        included_systems=["Drone Station", "Privacy Masking CCTV", "Command Tunnel"],
        emergency_buttons=["DROWNING", "MEDICAL", "SECURITY_ALERT"],
        required_integrations=["AEGIS Private", "VVIP Key"],
        setup_price_range_usd="300000-750000",
        monthly_saas_range_usd="30000-75000",
        authority_access_model="Private Command; External escalation restricted",
        shadow_report_type="RESORT_INCIDENT_REPORT"
    ),
    "Atoll / Regional Command Node": ProductPackage(
        package_name="Atoll / Regional Command Node",
        target_customer="Regional Governments / Military Command",
        included_systems=["Regional Dashboard", "Multi-Drone Fleet", "Kacific Failover"],
        emergency_buttons=["EVACUATION_SUPPORT", "STORM_DAMAGE", "SECURITY_ALERT"],
        required_integrations=["MNDF", "Regional Police"],
        setup_price_range_usd="500000-1200000",
        monthly_saas_range_usd="35000-100000",
        authority_access_model="Centralized Regional Control",
        shadow_report_type="MNDF_NATIONAL_SECURITY_EVENT"
    ),
    "Strategic Fire Response Node": ProductPackage(
        package_name="Strategic Fire Response Node",
        target_customer="Fire Services / Industrial Parks",
        included_systems=["Thermal Drone", "Fire Dashboard", "IoT Sensors"],
        emergency_buttons=["FIRE_SMOKE", "TRAFFIC_INCIDENT"],
        required_integrations=["Fire Dept", "Hydrant Mapping"],
        setup_price_range_usd="500000-1200000",
        monthly_saas_range_usd="35000-75000",
        authority_access_model="Fire Command Center",
        shadow_report_type="FIRE_SMOKE_REPORT"
    ),
    "Traffic & Crowd Safety Node": ProductPackage(
        package_name="Traffic & Crowd Safety Node",
        target_customer="City Councils / Smart Cities",
        included_systems=["CCTV Network", "Traffic AI", "Crowd Monitor"],
        emergency_buttons=["TRAFFIC_INCIDENT", "CROWD_RISK"],
        required_integrations=["Transport Dept", "Police"],
        setup_price_range_usd="150000-500000",
        monthly_saas_range_usd="20000-75000",
        authority_access_model="City Traffic Control",
        shadow_report_type="TRAFFIC_INCIDENT_REPORT"
    )
}
