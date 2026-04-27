from discord.ext import commands
from src.presentation.discord_bot.cog_registry import CogRegistry
from src.presentation.discord_bot.cogs.monitor_cog import MonitorCog


@CogRegistry.register
class MonitorCogFactory:
    def build(self, bot: commands.Bot, container) -> commands.Cog:
        return MonitorCog(
            bot=bot,
            add_streamer_uc=container.add_streamer_uc,
            remove_streamer_uc=container.remove_streamer_uc,
            list_streamers_uc=container.list_streamers_uc,
        )