class DomainError(Exception):
    """
    Base de errores de dominio.

    El mensaje del constructor es un texto EN INGLÉS para logs/debug —
    NUNCA se muestra al usuario. El texto de cara al usuario se resuelve
    en presentación vía i18n usando el TIPO de excepción + `self.params`.
    """
    def __init__(self, message: str = "", **params) -> None:
        self.params: dict = params
        super().__init__(message)


class StreamerAlreadyExistsError(DomainError):
    def __init__(self, username: str = "") -> None:
        super().__init__(f"Streamer already registered: {username!r}", username=username)


class StreamerNotFoundError(DomainError):
    def __init__(self, username: str = "") -> None:
        super().__init__(f"Streamer not found: {username!r}", username=username)


class StreamerLimitReachedError(DomainError):
    def __init__(self, limit: int = 0) -> None:
        super().__init__(f"Streamer limit reached: {limit}", limit=limit)


class StreamerNotOnTwitchError(DomainError):
    def __init__(self, username: str = "") -> None:
        super().__init__(f"User not on Twitch: {username!r}", username=username)


class ChannelNotConfiguredError(DomainError):
    def __init__(self) -> None:
        super().__init__("Announcement channel not configured")


class YouTubeChannelNotFoundError(DomainError):
    def __init__(self, channel: str = "") -> None:
        super().__init__(f"YouTube channel not monitored: {channel!r}", channel=channel)


class ChannelNotFoundError(DomainError):
    def __init__(self, channel: str = "") -> None:
        super().__init__(f"YouTube channel does not exist: {channel!r}", channel=channel)


class ChannelLimitReachedError(DomainError):
    def __init__(self, limit: int = 0) -> None:
        super().__init__(f"Channel limit reached: {limit}", limit=limit)
