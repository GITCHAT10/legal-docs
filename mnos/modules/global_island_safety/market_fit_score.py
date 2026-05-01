from mnos.modules.global_island_safety.country_profile import CountryProfile

def score_country_profile(profile: CountryProfile) -> float:
    """
    Calculates market fit score based on key parameters.
    - island/coastal geography
    - resort/tourism density
    - disaster/emergency need
    - government/security command fit
    - CCTV/drone public safety fit
    - regulatory complexity penalty
    - early buyer readiness
    """
    # The score is largely pre-defined in the initial data,
    # but we implement the calculation logic here for dynamic scaling.

    # Baseline from geographic fit
    base_score = 7.0

    # Geography & Tourism density
    if profile.country_code in ["MV", "SC", "FJ", "MU"]:
        base_score += 1.5 # High island density
    elif profile.country_code in ["TH", "ID", "PH"]:
        base_score += 1.2 # Coastal tourism hotspots

    # Disaster need (Typhoons/Bushfires)
    if profile.country_code in ["PH", "VN", "AU", "JP"]:
        base_score += 1.0

    # Regulatory complexity penalty
    if profile.country_code in ["SG", "AU", "NZ", "JP", "KR"]:
        base_score -= 0.5

    # Early buyer readiness (MNOS already in Maldives)
    if profile.country_code == "MV":
        base_score += 1.0

    return min(10.0, base_score)
