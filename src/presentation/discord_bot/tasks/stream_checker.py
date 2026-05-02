import asyncio

import aiohttp
import discord
from discord.ext import commands, tasks
from src.application.use_cases.check_live_streams import CheckLiveStreamsUseCase
from src.application.interfaces.guild_repository import IGuildRepository
from src.application.interfaces.logger import ILogger
from src.presentation.discord_bot.views.stream_embed import StreamEmbedBuilder


class StreamCheckerTask(commands.Cog):
    """
    Tarea en segundo plano que consulta Twitch periódicamente
    y publica anuncios cuando un streamer pasa a estar en vivo.
    """

    def __init__(
        self,
        bot: commands.Bot,
        check_live_uc: CheckLiveStreamsUseCase,
        guild_repo: IGuildRepository,
        logger: ILogger,
        interval_seconds: int = 60,
    ) -> None:
        self.bot = bot
        self._check_live_uc = check_live_uc
        self._guild_repo = guild_repo
        self._logger = logger
        self.check_streams.change_interval(seconds=interval_seconds)

    async def cog_load(self) -> None:
        """Arranca el loop al registrar el Cog en el bot."""
        self.check_streams.start()

    async def cog_unload(self) -> None:
        """Detiene el loop limpiamente al desregistrar el Cog."""
        self.check_streams.cancel()

    @tasks.loop(seconds=60)
    async def check_streams(self) -> None:
        """
        Loop principal. Intervalo configurable vía interval_seconds en el constructor.
        Captura ClientConnectorError por separado para evitar crash loops
        en fallos de red transitorios, con pausa de 5s antes del siguiente ciclo.
        """
        try:
            newly_live = await self._check_live_uc.execute()

            for streamer, stream_data in newly_live:
                await self._announce_stream(streamer, stream_data)
        except aiohttp.ClientConnectorError as e:
            # Capturamos el error de DNS/Red y evitamos el crash loop
            self._logger.warning(
                "check_streams_network_error",
                error=str(e),
                msg="Fallo de conexión o DNS con Twitch. Se intentará en el próximo ciclo."
            )
            # Pequeña pausa para no saturar si la red está intermitente
            await asyncio.sleep(5)
        except Exception as e:
            self._logger.error(
                "check_streams_task_failed",
                error=str(e),
                exc_info=True,
            )

    @check_streams.before_loop
    async def before_check(self) -> None:
        """Espera a que el bot esté completamente listo antes del primer ciclo."""
        await self.bot.wait_until_ready()
        self._logger.info("stream_checker_started")

    async def _announce_stream(self, streamer, stream_data: dict) -> None:
        """Envía el embed al canal configurado del servidor."""
        config = await self._guild_repo.get_by_id(streamer.guild_id)
        if not config or not config.announcement_channel_id:
            return

        channel = self.bot.get_channel(config.announcement_channel_id)
        if channel is None:
            self._logger.warning(
                "announcement_channel_not_found",
                guild_id=streamer.guild_id,
                channel_id=config.announcement_channel_id,
            )
            return

        embed = StreamEmbedBuilder.build_live_embed(streamer, stream_data)
        content = StreamEmbedBuilder.build_mention_content(streamer)

        try:
            await channel.send(
                content=content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    everyone=True, roles=True
                ),
            )
            self._logger.info(
                "stream_announced",
                guild_id=streamer.guild_id,
                username=streamer.username,
            )
        except discord.Forbidden:
            self._logger.warning(
                "no_permission_to_announce",
                guild_id=streamer.guild_id,
                channel_id=channel.id,
            )