from typing import Optional

from src.domain.exceptions.domain_exceptions import (
    DomainError, StreamerAlreadyExistsError, StreamerLimitReachedError,
    StreamerNotOnTwitchError, ChannelNotConfiguredError, StreamerNotFoundError,
    YouTubeChannelNotFoundError, ChannelNotFoundError, ChannelLimitReachedError,
)
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver


_ERROR_KEYS = {
    StreamerAlreadyExistsError:  "error.streamer_already_exists",
    StreamerLimitReachedError:   "error.streamer_limit_reached",
    StreamerNotOnTwitchError:    "error.streamer_not_on_twitch",
    ChannelNotConfiguredError:   "error.channel_not_configured",
    StreamerNotFoundError:       "error.streamer_not_found",
    YouTubeChannelNotFoundError: "error.youtube_channel_not_found",
    ChannelNotFoundError:        "error.channel_not_found",
    ChannelLimitReachedError:    "error.channel_limit_reached",
}


async def domain_error_message(
    error: Exception,
    guild_id: Optional[int],
    i18n: GuildLanguageResolver,
) -> str:
    """
    Traduce una excepción al idioma del guild. Única fuente de verdad para
    el texto de error de cara al usuario. Usada por el handler global, los
    cogs y admin_cog.
    """
    for exc_type, key in _ERROR_KEYS.items():
        if isinstance(error, exc_type):
            return await i18n.t(key, guild_id, **getattr(error, "params", {}))
    if isinstance(error, DomainError):
        return await i18n.t("error.domain_generic", guild_id)
    return await i18n.t("error.unexpected", guild_id)
