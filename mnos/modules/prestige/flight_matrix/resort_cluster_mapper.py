from typing import List, Dict, Optional
from mnos.modules.prestige.flight_matrix.models import ResortClusterRecommendation

RESORT_CLUSTERS = {
    "speedboat_volume": [
        "Villa Nautica", "Bandos", "Meeru", "Sheraton", "Sun Siyam Olhuveli", "Hard Rock"
    ],
    "speedboat_luxury": [
        "Baros", "One&Only Reethi Rah", "OZEN LIFE Maadhoo", "Velassaru", "Waldorf Astoria Ithaafushi"
    ],
    "uhNW_black_book": [
        "Cheval Blanc Randheli", "Velaa Private Island", "Soneva Jani", "Soneva Secret",
        "The Nautilus", "Kudadoo", "Waldorf Ithaafushi Private Island", "JOALI BEING", "One&Only Reethi Rah"
    ],
    "domestic_south": [
        "Mercure Kooddoo", "Pullman Maamutaa", "Canareef", "Sun Siyam Iru Veli", "Kandima"
    ],
    "family_all_inclusive": [
        "Siyam World", "Atmosphere Kanifushi", "Lily Beach", "Kuredu"
    ]
}

RESORT_ATOLL_MAP = {
    "Villa Nautica": "KAAFU_NORTH",
    "Bandos": "KAAFU_NORTH",
    "Baros": "KAAFU_NORTH",
    "One&Only Reethi Rah": "KAAFU_NORTH",
    "Waldorf Astoria Ithaafushi": "KAAFU_SOUTH",
    "Cheval Blanc Randheli": "NOONU",
    "Velaa Private Island": "NOONU",
    "Soneva Jani": "NOONU",
    "Mercure Kooddoo": "GAAFU_ALIFU",
    "JOALI BEING": "BAA"
}

class ResortClusterMapper:
    def get_cluster_for_resort(self, resort_name: str) -> Optional[str]:
        for cluster, resorts in RESORT_CLUSTERS.items():
            if resort_name in resorts:
                return cluster
        return None

    def get_resorts_in_cluster(self, cluster_id: str) -> List[str]:
        return RESORT_CLUSTERS.get(cluster_id, [])

    def get_atoll(self, resort_name: str) -> str:
        return RESORT_ATOLL_MAP.get(resort_name, "MLE")
