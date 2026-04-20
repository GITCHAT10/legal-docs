class FeedAdapter:
    """
    Bucket B: External validation feeds (AQICN, IQAir, etc.)
    """
    def fetch_air_quality(self, location: str):
        # Mocked adapter interface
        return {"aqi": 25, "source": "mock"}
