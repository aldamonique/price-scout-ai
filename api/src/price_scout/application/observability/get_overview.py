from price_scout.domain.observability.models import Overview
from price_scout.domain.observability.ports import ObservabilityReader


class GetObservability:
    def __init__(self, reader: ObservabilityReader) -> None:
        self._reader = reader

    def execute(self) -> Overview:
        return self._reader.overview()
