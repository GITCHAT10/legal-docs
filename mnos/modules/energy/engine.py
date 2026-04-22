class EnergyEngine:
    """
    iGEO HACEOSLAR Energy Engine
    Implements Renewable-First Algorithm (RFL) for the Maldives.
    """
    def __init__(self):
        self.wave_potential = 0.7  # kW per m
        self.solar_efficiency = 0.22

    def sync_power(self, demand_kw: float, sun_exposure: float, wave_height: float):
        """
        RFL Algorithm: Renewable-First Logic.
        Prioritizes HACE (Wave) and Ocean Solar before using Gensets.
        """
        solar_gen = sun_exposure * 100 * self.solar_efficiency # Simplified
        wave_gen = wave_height * self.wave_potential * 10 # Simplified

        renewable_total = solar_gen + wave_gen

        status = "RENEWABLE_ONLY" if renewable_total >= demand_kw else "HYBRID_SUPPORT"
        genset_need = max(0, demand_kw - renewable_total)

        return {
            "demand_kw": demand_kw,
            "solar_gen_kw": round(solar_gen, 2),
            "wave_gen_kw": round(wave_gen, 2),
            "renewable_total_kw": round(renewable_total, 2),
            "genset_need_kw": round(genset_need, 2),
            "status": status,
            "rfl_validation": "MIG_PATENTED_LOGIC"
        }

energy_engine = EnergyEngine()
