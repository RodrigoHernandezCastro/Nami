# src/application/use_cases/add_streamer.py
from dataclasses import dataclass
from typing import Optional, List
from src.domain.entities.streamer import Streamer
from src.domain.value_objects.twitch_username import TwitchUsername
from src.domain.exceptions.domain_exceptions import (
    StreamerAlreadyExistsError, StreamerLimitReachedError,
    StreamerNotOnTwitchError, ChannelNotConfiguredError,
)
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.twitch_service import ITwitchService
from src.application.interfaces.logger import ILogger


@dataclass
class AddStreamerCommand:
    guild_id: int
    username: str
    custom_message: str
    mention_type: str
    mention_role_ids: Optional[List[int]] = None


class AddStreamerUseCase:
    """
    Caso de uso puro: solo depende de interfaces.
    NO conoce SQLite, PostgreSQL, Discord ni aiohttp.
    """

    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        guild_repo: IGuildRepository,
        twitch_service: ITwitchService,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._guild_repo = guild_repo
        self._twitch = twitch_service
        self._logger = logger

    async def execute(self, command: AddStreamerCommand) -> Streamer:
        """
        Valida y persiste un nuevo streamer. Orden de validaciones:
        1. Formato de username (TwitchUsername value object)
        2. Canal de anuncios configurado en el servidor
        3. Límite de streamers no superado
        4. Usuario existe en Twitch (llamada a API)
        Lanza StreamerAlreadyExistsError si el repo detecta duplicado.
        """

        # 1) Validación de dominio
        username = TwitchUsername(command.username)

        # 2) Reglas de negocio
        guild_config = await self._guild_repo.get_by_id(command.guild_id)
        if not guild_config or not guild_config.announcement_channel_id:
            raise ChannelNotConfiguredError()

        current = await self._streamer_repo.count_by_guild(command.guild_id)
        if current >= guild_config.streamer_limit:
            raise StreamerLimitReachedError(limit=guild_config.streamer_limit)

        if not await self._twitch.user_exists(username.value):
            raise StreamerNotOnTwitchError(username=username.value)

        # 3) Persistir
        streamer = Streamer(
            guild_id=command.guild_id,
            username=username.value,
            custom_message=command.custom_message,
            mention_type=command.mention_type,
            mention_role_ids=command.mention_role_ids,
        )

        try:
            created = await self._streamer_repo.add(streamer)
        except StreamerAlreadyExistsError:
            self._logger.warning(
                "intento_duplicado",
                guild_id=command.guild_id,
                username=username.value,
            )
            raise

        self._logger.info(
            "streamer_añadido",
            guild_id=command.guild_id,
            username=username.value,
            streamer_id=created.id,
        )
        return created