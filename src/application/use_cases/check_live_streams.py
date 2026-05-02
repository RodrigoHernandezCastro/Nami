from typing import List
from src.domain.entities.streamer import Streamer
from src.application.interfaces.streamer_repository import IStreamerRepository
from src.application.interfaces.twitch_service import ITwitchService
from src.application.interfaces.logger import ILogger


class CheckLiveStreamsUseCase:
    """
    Caso de uso: detecta cambios de estado (offline → online).
    Devuelve la lista de streamers que acaban de iniciar stream,
    junto con los detalles recibidos de Twitch.
    """

    def __init__(
        self,
        streamer_repo: IStreamerRepository,
        twitch_service: ITwitchService,
        logger: ILogger,
    ) -> None:
        self._streamer_repo = streamer_repo
        self._twitch = twitch_service
        self._logger = logger

    async def execute(self) -> List[tuple[Streamer, dict]]:
        """
        Consulta Twitch con todos los usernames registrados (1 sola petición
        por cada chunk de 100) y detecta transiciones de estado.
        Persiste el cambio en BD antes de retornar para evitar doble anuncio
        si el ciclo siguiente llega antes de que el bot procese la notificación.
        Devuelve solo los streamers que acaban de pasar a online este ciclo.
        """
        # 1) Obtener todos los streamers con canal configurado
        streamers = await self._streamer_repo.find_all_with_channel()
        if not streamers:
            return []

        usernames = [s.username for s in streamers]

        # 2) Consultar a Twitch
        live_details = await self._twitch.get_live_streams_details(usernames)

        # 3) Detectar transiciones
        newly_live: List[tuple[Streamer, dict]] = []

        for streamer in streamers:
            is_now_online = streamer.username.lower() in live_details

            if is_now_online and not streamer.is_online:
                # Cambio: offline → online
                await self._streamer_repo.update_status(streamer.id, True)
                streamer.mark_online()
                newly_live.append(
                    (streamer, live_details[streamer.username.lower()])
                )
                self._logger.info(
                    "streamer_went_live",
                    streamer_id=streamer.id,
                    username=streamer.username,
                )
            elif not is_now_online and streamer.is_online:
                # Cambio: online → offline
                await self._streamer_repo.update_status(streamer.id, False)
                streamer.mark_offline()
                self._logger.info(
                    "streamer_went_offline",
                    streamer_id=streamer.id,
                    username=streamer.username,
                )

        return newly_live