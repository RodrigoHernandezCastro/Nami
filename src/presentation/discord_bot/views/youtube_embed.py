import discord
from datetime import datetime
import re

from src.domain.entities.youtube_channel import YouTubeChannel

class YouTubeEmbedBuilder:
    """Constructor de embeds para anuncios de YouTube."""

    @staticmethod
    def build_video_embed(video: dict, channel: 'YouTubeChannel') -> discord.Embed:
        title = video.get("title", "Sin título")[:256]
        thumbnail = video.get("thumbnail", "")
        video_url = f"https://youtube.com/watch?v={video['video_id']}"

        is_live = video.get("liveBroadcastContent") == "live"
        is_short = YouTubeEmbedBuilder._is_short(video)

        if is_live:
            embed = discord.Embed(
                title=f"LIVE — {title}",
                url=video_url,
                color=discord.Color.from_str("#FF0000"),
            )
        elif is_short:
            embed = discord.Embed(
                title=f"SHORT: {title}",
                url=video_url,
                color=discord.Color.red(),
            )
        else:
            embed = discord.Embed(
                title=title,
                url=video_url,
                color=discord.Color.red(),
            )

        embed.set_image(url=thumbnail)
        embed.set_footer(text=f"{channel.channel_name} • YouTube")
        return embed

    @staticmethod
    def _is_short(video: dict) -> bool:
        """Detecta shorts por #shorts en título."""
        title = video.get("title", "").lower()
        return "#shorts" in title or "shorts" in title

    @staticmethod
    def build_mention_content(channel: 'YouTubeChannel', is_live: bool = False) -> str:
        """Construye mención según configuración (y tipo de contenido)."""
        mention_type = channel.get_mention_type(is_live)
        role_ids = channel.get_mention_role_ids(is_live)

        mention = ""
        if mention_type == "everyone":
            mention = "@everyone"
        elif mention_type == "here":
            mention = "@here"
        elif mention_type == "rol" and role_ids:
            mentions = [f"<@&{rid}>" for rid in role_ids]
            mention = " ".join(mentions)

        message = channel.get_message(is_live)
        return f"{mention} {message}".strip()