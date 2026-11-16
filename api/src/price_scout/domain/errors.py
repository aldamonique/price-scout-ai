class UpstreamError(Exception):
    pass


class RequestNotFoundError(Exception):
    pass


class ObservabilityUnavailableError(Exception):
    pass


class RequestInProgressError(Exception):
    pass


class RateLimitedError(Exception):
    pass
