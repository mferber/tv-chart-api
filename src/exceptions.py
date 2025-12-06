class ConfigurationError(Exception):
    """The app was not configured properly."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
