class VesselDispatchOracle:
    def calculate_consolidation_score(self, lf, fc, sla, esg):
        return round((lf*0.4)+(fc*0.3)+(sla*0.2)+(esg*0.1), 3)
dispatch_oracle = VesselDispatchOracle()
