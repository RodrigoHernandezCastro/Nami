import discord
from datetime import datetime
from src.domain.entities.streamer import Streamer


class StreamEmbedBuilder:
    """Constructor de embeds para anuncios de stream en vivo."""

    @staticmethod
    def build_live_embed(streamer: Streamer, stream_data: dict) -> discord.Embed:
        title = stream_data.get("title", "Sin título")
        game = stream_data.get("game_name", "Sin categoría")
        viewers = stream_data.get("viewer_count", 0)
        thumbnail_url = stream_data.get("thumbnail_url", "").format(
            width=1280, height=720
        )
        url = f"https://twitch.tv/{streamer.username}"

        embed = discord.Embed(
            title=f"{streamer.username} está EN VIVO",
            description=f"**{title}**",
            url=url,
            color=discord.Color.purple(),
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="🎮 Jugando", value=game, inline=True)
        embed.add_field(name="👥 Espectadores", value=str(viewers), inline=True)
        embed.add_field(
            name="🔗 Enlace",
            value=f"[Ver stream]({url})",
            inline=False,
        )

        if thumbnail_url:
            # Evita que Discord cachee la misma imagen
            cache_buster = int(datetime.utcnow().timestamp())
            embed.set_image(url=f"{thumbnail_url}?t={cache_buster}")

        embed.set_footer(text="Twitch • Nami Bot")
        return embed

    @staticmethod
    def build_mention_content(streamer: Streamer) -> str:
        """Construye el texto de mención según la configuración."""
        mention = ""
        if streamer.mention_type == "everyone":
            mention = "@everyone"
        elif streamer.mention_type == "here":
            mention = "@here"
        elif streamer.mention_type == "rol" and streamer.mention_role_ids:
            mentions = [f"<@&{rid}>" for rid in streamer.mention_role_ids]
            mention = " ".join(mentions)

        message = streamer.custom_message or "¡Ya está en vivo!"
        return f"{mention} {message}".strip()