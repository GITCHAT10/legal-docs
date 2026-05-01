from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

class RolloutPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class CountryProfile:
    country_code: str
    country_name: str
    primary_product_name: str
    market_fit_score: float
    best_use_cases: List[str]
    aviation_authority: str
    security_authority: str
    disaster_authority: str
    telecom_or_radio_authority: str
    tourism_authority: str
    main_customers: List[str]
    best_first_buyer: str
    required_compliance_workflows: List[str]
    restricted_zone_notes: List[str]
    privacy_notes: List[str]
    recommended_package: str
    rollout_priority: int
    authority_escalation_model: str

COUNTRY_PROFILES: Dict[str, CountryProfile] = {
    "MV": CountryProfile(
        country_code="MV",
        country_name="Maldives",
        primary_product_name="MIG SHIELD Island Guard / Resort Lifeguard Node",
        market_fit_score=9.6,
        best_use_cases=[
            "island emergency response", "resort drowning response", "medical emergency support",
            "fire/smoke verification", "missing guest search", "jetty/boat incident",
            "MNDF central command", "seaplane/airspace-risk coordination"
        ],
        aviation_authority="Maldives CAA",
        security_authority="MNDF",
        disaster_authority="NDMA",
        telecom_or_radio_authority="local telecom / relevant regulator",
        tourism_authority="Ministry of Tourism",
        main_customers=["resorts", "MNDF", "island councils", "airports", "ports"],
        best_first_buyer="Resort / MNDF",
        required_compliance_workflows=[
            "MNDF approval workflow", "CAA permit workflow", "resort / island authority approval",
            "SHADOW mission audit", "AEGIS operator/device authority"
        ],
        restricted_zone_notes=["seaplane corridors", "airports", "military/security areas", "resort privacy zones"],
        privacy_notes=["guest privacy zones required", "no unrestricted surveillance"],
        recommended_package="Resort Lifeguard Node + Island Guard Node",
        rollout_priority=1,
        authority_escalation_model="Council/Resort reports → MNDF approves → CAA/authority compliance → SHADOW report"
    ),
    "LK": CountryProfile(
        country_code="LK",
        country_name="Sri Lanka",
        primary_product_name="MIG SHIELD Sri Lanka Coastal Safety Node",
        market_fit_score=8.7,
        best_use_cases=[
            "coastal resort safety", "drowning/beach response", "medical emergency support",
            "flood monitoring", "fire/smoke verification", "port and harbor monitoring",
            "tourist-zone CCTV + drone command"
        ],
        aviation_authority="Civil Aviation Authority of Sri Lanka",
        security_authority="Police / Defence / relevant security agencies",
        disaster_authority="Disaster Management Centre / relevant agencies",
        telecom_or_radio_authority="local telecom / radio authority",
        tourism_authority="Sri Lanka Tourism authorities",
        main_customers=["coastal resorts", "disaster agencies", "port authorities", "tourism zones"],
        best_first_buyer="Coastal resorts",
        required_compliance_workflows=[
            "local aviation permit workflow", "police/fire/disaster escalation",
            "resort geofence workflow", "SHADOW incident report"
        ],
        restricted_zone_notes=["airports", "ports", "military/security zones", "public privacy zones"],
        privacy_notes=["privacy masking recommended", "incident-based CCTV access"],
        recommended_package="Coastal Safety Node",
        rollout_priority=2,
        authority_escalation_model="Resort/Council report → Police/Fire/Disaster escalation → SHADOW report"
    ),
    "TH": CountryProfile(
        country_code="TH",
        country_name="Thailand",
        primary_product_name="MIG SHIELD Thailand Resort Emergency Node",
        market_fit_score=8.5,
        best_use_cases=[
            "Phuket resort safety", "Koh Samui island response", "marine tourism rescue",
            "fire/smoke response", "medical incident coordination", "CCTV + drone resort command",
            "tourist event monitoring"
        ],
        aviation_authority="CAAT",
        security_authority="Police / local authority",
        disaster_authority="disaster-response agencies",
        telecom_or_radio_authority="NBTC",
        tourism_authority="Tourism Authority / relevant tourism bodies",
        main_customers=["Phuket resorts", "Koh Samui resorts", "marine tourism operators", "island municipalities"],
        best_first_buyer="Phuket / Samui resorts",
        required_compliance_workflows=[
            "CAAT compliance workflow", "NBTC registration workflow", "insurance document tracking",
            "no-fly zone rules", "tourist privacy controls", "local authority escalation"
        ],
        restricted_zone_notes=["airports", "military zones", "national parks", "event/public crowd areas"],
        privacy_notes=["tourist privacy masking", "no facial recognition by default"],
        recommended_package="Resort Emergency Node",
        rollout_priority=3,
        authority_escalation_model="Resort report → Local authority/police/fire escalation → aviation/telecom compliance records → SHADOW report"
    ),
    "ID": CountryProfile(
        country_code="ID",
        country_name="Indonesia / Bali",
        primary_product_name="MIG SHIELD Bali Resort Safety Node",
        market_fit_score=8.3,
        best_use_cases=[
            "resort water safety", "fire/smoke verification", "medical route support",
            "cliff/beach search support", "CCTV + emergency command", "storm/flood damage mapping",
            "VIP villa security response"
        ],
        aviation_authority="DGCA / relevant Indonesian aviation authority",
        security_authority="Police / local authority",
        disaster_authority="BNPB / regional disaster agencies where applicable",
        telecom_or_radio_authority="local telecom / relevant radio authority",
        tourism_authority="Indonesian / Bali tourism authorities",
        main_customers=["Bali luxury resorts", "villas", "tourism zones", "local authorities"],
        best_first_buyer="Bali luxury resorts",
        required_compliance_workflows=[
            "local aviation permit workflow", "resort-only geofencing", "airport restriction zones",
            "temple/cultural privacy zones", "tourism-police escalation", "local permit records"
        ],
        restricted_zone_notes=["airports", "temples/cultural sites", "public ceremonies", "government/security areas"],
        privacy_notes=["cultural privacy zones required", "guest privacy masking"],
        recommended_package="Bali Resort Safety Node",
        rollout_priority=4,
        authority_escalation_model="Resort report → Local police/tourism authority → compliance record → SHADOW report"
    ),
    "PH": CountryProfile(
        country_code="PH",
        country_name="Philippines",
        primary_product_name="MIG SHIELD Philippines Coastal Disaster & Resort Safety Node",
        market_fit_score=9.1,
        best_use_cases=[
            "island disaster response", "typhoon/flood damage mapping", "resort drowning response",
            "coastal search and rescue", "medical access support", "port/harbor safety"
        ],
        aviation_authority="CAAP",
        security_authority="Police / Coast Guard / relevant security authorities",
        disaster_authority="NDRRMC / local disaster agencies",
        telecom_or_radio_authority="local telecom/radio authority",
        tourism_authority="Department of Tourism / relevant tourism bodies",
        main_customers=["resorts", "local governments", "disaster agencies", "port/coast guard stakeholders"],
        best_first_buyer="island resorts + local disaster agencies",
        required_compliance_workflows=[
            "CAAP permit workflow", "disaster agency escalation", "coastal/port authority coordination",
            "SHADOW disaster incident report"
        ],
        restricted_zone_notes=["airports", "military zones", "disaster-restricted areas", "coast guard/security areas"],
        privacy_notes=["public safety privacy controls"],
        recommended_package="Coastal Disaster & Resort Safety Node",
        rollout_priority=3,
        authority_escalation_model="Local report → Disaster agency/coast guard/police escalation → SHADOW report"
    ),
    "MY": CountryProfile(
        country_code="MY",
        country_name="Malaysia",
        primary_product_name="MIG SHIELD Malaysia Island & Port Safety Node",
        market_fit_score=8.5,
        best_use_cases=[
            "Langkawi resort safety", "Sabah coastal/island monitoring", "port/harbor safety",
            "flood monitoring", "fire/smoke verification", "marine tourism response"
        ],
        aviation_authority="CAAM",
        security_authority="Police / maritime authorities / local authority",
        disaster_authority="NADMA / local disaster agencies",
        telecom_or_radio_authority="MCMC / relevant telecom authority",
        tourism_authority="Tourism Malaysia / local tourism authorities",
        main_customers=["resorts", "ports", "local authorities", "disaster agencies"],
        best_first_buyer="Langkawi / Sabah resorts",
        required_compliance_workflows=[
            "CAAM permit workflow", "telecom/radio compliance", "local authority escalation",
            "port authority coordination"
        ],
        restricted_zone_notes=["airports", "ports", "border/security areas"],
        privacy_notes=["role-based CCTV access"],
        recommended_package="Island & Port Safety Node",
        rollout_priority=5,
        authority_escalation_model="Resort/port report → local authority/security/disaster escalation → SHADOW report"
    ),
    "FJ": CountryProfile(
        country_code="FJ",
        country_name="Fiji",
        primary_product_name="MIG SHIELD Fiji Island Resilience Node",
        market_fit_score=8.4,
        best_use_cases=[
            "cyclone response", "island resort safety", "marine rescue support",
            "flood/storm damage mapping", "remote community emergency visibility"
        ],
        aviation_authority="Fiji CAA / relevant aviation authority",
        security_authority="Police / relevant security agencies",
        disaster_authority="National Disaster Management Office / relevant agencies",
        telecom_or_radio_authority="local telecom/radio authority",
        tourism_authority="Tourism Fiji / relevant tourism bodies",
        main_customers=["island resorts", "local governments", "disaster agencies"],
        best_first_buyer="island resorts + disaster agencies",
        required_compliance_workflows=["aviation permit workflow", "disaster response escalation", "island connectivity failover", "SHADOW disaster report"],
        restricted_zone_notes=["airports", "sensitive government/security areas"],
        privacy_notes=["community privacy policy required"],
        recommended_package="Island Resilience Node",
        rollout_priority=6,
        authority_escalation_model="Island report → disaster/police escalation → SHADOW report"
    ),
    "SC": CountryProfile(
        country_code="SC",
        country_name="Seychelles",
        primary_product_name="MIG SHIELD Seychelles Luxury Island Safety Node",
        market_fit_score=8.3,
        best_use_cases=[
            "luxury island resort safety", "marine conservation monitoring", "drowning response",
            "fire/smoke verification", "guest emergency support"
        ],
        aviation_authority="Seychelles CAA / relevant authority",
        security_authority="Police / relevant security agencies",
        disaster_authority="disaster/emergency agencies",
        telecom_or_radio_authority="local telecom/radio authority",
        tourism_authority="Seychelles tourism authorities",
        main_customers=["luxury resorts", "conservation operators", "island authorities"],
        best_first_buyer="luxury island resorts",
        required_compliance_workflows=["aviation permit workflow", "conservation/privacy controls", "resort authority approval", "SHADOW incident report"],
        restricted_zone_notes=["airports", "protected conservation zones", "sensitive resort privacy areas"],
        privacy_notes=["luxury guest privacy masking"],
        recommended_package="Luxury Island Safety Node",
        rollout_priority=6,
        authority_escalation_model="Resort report → police/emergency/conservation escalation → SHADOW report"
    ),
    "MU": CountryProfile(
        country_code="MU",
        country_name="Mauritius",
        primary_product_name="MIG SHIELD Mauritius Resort & Cyclone Safety Node",
        market_fit_score=8.2,
        best_use_cases=[
            "cyclone monitoring", "resort emergency response", "drowning/beach safety",
            "fire/smoke verification", "coastal infrastructure inspection"
        ],
        aviation_authority="Mauritius CAA / relevant authority",
        security_authority="Police / relevant security agencies",
        disaster_authority="National Disaster Risk Reduction / emergency agencies",
        telecom_or_radio_authority="local telecom/radio authority",
        tourism_authority="Mauritius tourism authorities",
        main_customers=["resorts", "coastal authorities", "disaster agencies"],
        best_first_buyer="coastal resorts",
        required_compliance_workflows=["aviation permit workflow", "cyclone/disaster response escalation", "resort approval", "SHADOW report"],
        restricted_zone_notes=["airports", "coastal protected zones", "sensitive tourism areas"],
        privacy_notes=["guest privacy controls"],
        recommended_package="Resort & Cyclone Safety Node",
        rollout_priority=7,
        authority_escalation_model="Resort/coastal report → police/disaster escalation → SHADOW report"
    ),
    "VN": CountryProfile(
        country_code="VN",
        country_name="Vietnam",
        primary_product_name="MIG SHIELD Vietnam Coastal Safety Node",
        market_fit_score=8.0,
        best_use_cases=[
            "coastal tourism safety", "flood/storm monitoring", "port/industrial fire support",
            "resort emergency response", "traffic/crowd monitoring in tourism zones"
        ],
        aviation_authority="Vietnam aviation authority / relevant regulator",
        security_authority="Police / local authority",
        disaster_authority="disaster-response agencies",
        telecom_or_radio_authority="local telecom/radio authority",
        tourism_authority="Vietnam tourism authorities",
        main_customers=["resorts", "ports", "industrial parks", "local authorities"],
        best_first_buyer="coastal resorts / ports",
        required_compliance_workflows=["aviation permit workflow", "local authority escalation", "industrial safety workflow", "SHADOW incident report"],
        restricted_zone_notes=["airports", "military/security zones", "industrial restricted sites"],
        privacy_notes=["role-based camera access"],
        recommended_package="Coastal Safety Node",
        rollout_priority=8,
        authority_escalation_model="Site report → police/fire/disaster escalation → SHADOW report"
    ),
    "AU": CountryProfile(
        country_code="AU",
        country_name="Australia",
        primary_product_name="MIG SHIELD Australia Coastal & Bushfire Support Node",
        market_fit_score=7.9,
        best_use_cases=[
            "bushfire support visibility", "coastal rescue support", "resort/island safety",
            "emergency mapping", "infrastructure inspection"
        ],
        aviation_authority="CASA",
        security_authority="Police / emergency services",
        disaster_authority="state emergency services / fire agencies",
        telecom_or_radio_authority="ACMA / telecom authority",
        tourism_authority="tourism bodies / local authorities",
        main_customers=["emergency services", "resorts", "coastal councils", "infrastructure operators"],
        best_first_buyer="coastal councils / resorts",
        required_compliance_workflows=["CASA compliance", "emergency services integration", "strict privacy and data governance"],
        restricted_zone_notes=["airports", "controlled airspace", "emergency incident zones"],
        privacy_notes=["strict privacy and data retention controls"],
        recommended_package="Coastal & Bushfire Support Node",
        rollout_priority=9,
        authority_escalation_model="Site/council report → emergency services → SHADOW report"
    ),
    "JP": CountryProfile(
        country_code="JP",
        country_name="Japan",
        primary_product_name="MIG SHIELD Japan Disaster & Island Safety Node",
        market_fit_score=7.8,
        best_use_cases=[
            "disaster response", "island community support", "aging population emergency visibility",
            "flood/earthquake damage mapping", "infrastructure inspection"
        ],
        aviation_authority="JCAB / relevant authority",
        security_authority="Police / local government",
        disaster_authority="disaster management agencies",
        telecom_or_radio_authority="telecom/radio authority",
        tourism_authority="tourism/local government bodies",
        main_customers=["local governments", "disaster agencies", "island communities"],
        best_first_buyer="local governments / disaster agencies",
        required_compliance_workflows=["aviation compliance", "disaster response integration", "privacy and municipal data governance"],
        restricted_zone_notes=["airports", "dense urban zones", "government/security zones"],
        privacy_notes=["strict data minimization"],
        recommended_package="Disaster & Island Safety Node",
        rollout_priority=10,
        authority_escalation_model="Local report → municipal/disaster/police escalation → SHADOW report"
    ),
    "KR": CountryProfile(
        country_code="KR",
        country_name="South Korea",
        primary_product_name="MIG SHIELD Korea Port & Smart City Safety Node",
        market_fit_score=7.6,
        best_use_cases=[
            "port safety", "smart city traffic/crowd monitoring", "coastal security support",
            "emergency response", "infrastructure inspection"
        ],
        aviation_authority="Korean aviation authority / relevant regulator",
        security_authority="Police / local authority",
        disaster_authority="disaster-response agencies",
        telecom_or_radio_authority="telecom/radio authority",
        tourism_authority="local/tourism bodies",
        main_customers=["ports", "smart cities", "local authorities", "resorts"],
        best_first_buyer="port/smart city operators",
        required_compliance_workflows=["aviation compliance", "city data governance", "police/emergency integration"],
        restricted_zone_notes=["airports", "military/security areas", "dense urban privacy zones"],
        privacy_notes=["strict privacy and data-retention policy"],
        recommended_package="Port & Smart City Safety Node",
        rollout_priority=11,
        authority_escalation_model="City/port report → police/emergency escalation → SHADOW report"
    ),
    "NZ": CountryProfile(
        country_code="NZ",
        country_name="New Zealand",
        primary_product_name="MIG SHIELD New Zealand Tourism & Search-Rescue Node",
        market_fit_score=7.5,
        best_use_cases=[
            "search and rescue", "coastal tourism safety", "disaster response",
            "rural/island emergency visibility", "infrastructure inspection"
        ],
        aviation_authority="CAA New Zealand",
        security_authority="Police / emergency services",
        disaster_authority="emergency management agencies",
        telecom_or_radio_authority="local telecom/radio authority",
        tourism_authority="tourism/local authorities",
        main_customers=["tourism operators", "emergency services", "local councils"],
        best_first_buyer="tourism operators / emergency services",
        required_compliance_workflows=["CAA compliance", "search/rescue workflow", "privacy controls"],
        restricted_zone_notes=["airports", "conservation areas", "emergency zones"],
        privacy_notes=["strict privacy and public safety access controls"],
        recommended_package="Tourism & Search-Rescue Node",
        rollout_priority=12,
        authority_escalation_model="Site report → police/emergency services → SHADOW report"
    ),
    "SG": CountryProfile(
        country_code="SG",
        country_name="Singapore",
        primary_product_name="MIG SHIELD Singapore Smart Port & Command Showcase Node",
        market_fit_score=7.2,
        best_use_cases=[
            "port safety", "smart city command showcase", "traffic/crowd monitoring",
            "emergency response visibility", "infrastructure inspection"
        ],
        aviation_authority="CAAS",
        security_authority="Police / civil defence / relevant agencies",
        disaster_authority="civil defence / emergency services",
        telecom_or_radio_authority="IMDA / telecom authority",
        tourism_authority="tourism/local authorities",
        main_customers=["port operators", "smart city programs", "government agencies", "infrastructure operators"],
        best_first_buyer="port/smart city operator",
        required_compliance_workflows=["CAAS compliance", "IMDA/telecom compliance", "strict urban privacy rules", "public safety workflow"],
        restricted_zone_notes=["dense controlled airspace", "airports", "port restrictions", "urban no-fly zones"],
        privacy_notes=["strict privacy masking and access logging"],
        recommended_package="Smart Port & Command Showcase Node",
        rollout_priority=13,
        authority_escalation_model="Operator report → police/civil defence/agencies → SHADOW report"
    )
}
