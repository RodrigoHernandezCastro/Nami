# src/presentation/discord_bot/views/jankenpon_embed.py
"""
Constructores de embeds para !jankenpon.

Política de emojis:
- Application Emojis del bot (cargados al arrancar en `bot.app_emojis`)
  para jugadas y podio. Los nombres esperados son:
      rock, paper, scissors, first_place, second_place, third_place
- Si alguno no existe (no se cargó por error de red o no está creado en
  el Developer Portal), se cae a fallback Unicode automáticamente.

Las funciones reciben `bot` como parámetro nuevo para acceder al
registry. El cog ya tenía el bot disponible, así que solo cambian las
firmas en una capa.
"""
from __future__ import annotations
from typing import List

import discord
from discord.ext import commands

from src.application.interfaces.translator import ITranslator
from src.application.use_cases.get_global_leaderboard import (
    GlobalLeaderboardResult,
)
from src.application.use_cases.get_guild_leaderboard import (
    GuildLeaderboardResult,
)
from src.application.use_cases.play_jankenpon import PlayJankenponResult
from src.domain.value_objects.jankenpon_move import GameResult, Move


# Mapeo Move → nombre de emoji en el registry.
_MOVE_EMOJI_NAME = {
    Move.ROCK: "rock",
    Move.PAPER: "paper",
    Move.SCISSORS: "scissors",
}

# Color del embed por resultado.
_RESULT_COLOR = {
    GameResult.WIN: discord.Color.green(),
    GameResult.LOSS: discord.Color.red(),
    GameResult.DRAW: discord.Color.greyple(),
}


def _emoji(bot: commands.Bot, name: str) -> str:
    """
    Atajo: obtiene el emoji formateado del registry del bot.
    Si el bot no tiene registry (caso edge), devuelve string vacío.
    """
    registry = getattr(bot, "app_emojis", None)
    if registry is None:
        return ""
    return registry.get(name)


# ═════════════════════════════════════════════════════════════════════
# Match embed
# ═════════════════════════════════════════════════════════════════════
def build_match_embed(
    result: PlayJankenponResult,
    user_display: str,
    lang: str,
    translator: ITranslator,
    bot: commands.Bot,
) -> discord.Embed:
    """Embed de resultado. Muestra siempre nivel y XP actual."""
    t = translator.t

    if result.result is GameResult.WIN:
        title_key = "jankenpon.result.win"
    elif result.result is GameResult.LOSS:
        title_key = "jankenpon.result.loss"
    else:
        title_key = "jankenpon.result.draw"

    embed = discord.Embed(
        title=t(title_key, lang, xp_delta=_format_delta(result.xp_delta)),
        color=_RESULT_COLOR[result.result],
    )

    user_emoji = _emoji(bot, _MOVE_EMOJI_NAME[result.user_move])
    bot_emoji = _emoji(bot, _MOVE_EMOJI_NAME[result.bot_move])
    embed.description = (
        f"**{user_display}** {user_emoji}  "
        f"vs  {bot_emoji} **Bot**"
    )

    embed.add_field(
        name=t("jankenpon.field.level", lang),
        value=f"**{result.level_after}**",
        inline=True,
    )
    embed.add_field(
        name=t("jankenpon.field.xp", lang),
        value=f"**{result.xp_after}**",
        inline=True,
    )
    embed.add_field(
        name=t("jankenpon.field.xp_to_next", lang),
        value=f"{result.xp_to_next}",
        inline=True,
    )

    embed.add_field(
        name=t("jankenpon.field.stats", lang),
        value=t(
            "jankenpon.field.stats_value",
            lang,
            wins=result.wins,
            losses=result.losses,
            draws=result.draws,
            total=result.games_played,
        ),
        inline=False,
    )

    if result.leveled_up:
        embed.add_field(
            name="\u200b",
            value=t(
                "jankenpon.level_up", lang, level=result.level_after
            ),
            inline=False,
        )

    embed.set_footer(text=t("jankenpon.footer.autodelete", lang))
    return embed


# ═════════════════════════════════════════════════════════════════════
# Leaderboard embeds
# ═════════════════════════════════════════════════════════════════════
def build_guild_leaderboard_embed(
    result: GuildLeaderboardResult,
    guild_name: str,
    lang: str,
    translator: ITranslator,
    bot: commands.Bot,
) -> discord.Embed:
    t = translator.t

    if not result.rows:
        return discord.Embed(
            title=t("jankenpon.lb.title.server", lang, guild=guild_name),
            description=t("jankenpon.lb.empty", lang),
            color=discord.Color.blurple(),
        )

    embed = discord.Embed(
        title=t("jankenpon.lb.title.server", lang, guild=guild_name),
        color=discord.Color.blurple(),
    )

    lines: List[str] = []
    for row in result.rows:
        lines.append(
            t(
                "jankenpon.lb.entry",
                lang,
                medal=_rank_medal(row.rank, bot),
                rank=row.rank,
                user_id=row.user_id,
                level=row.level,
                xp=row.xp,
                games=row.games_played,
            )
        )
    embed.description = "\n".join(lines)
    embed.set_footer(text=t("jankenpon.lb.footer.server", lang))
    return embed


def build_global_leaderboard_embed(
    result: GlobalLeaderboardResult,
    lang: str,
    translator: ITranslator,
    bot: commands.Bot,
) -> discord.Embed:
    t = translator.t

    if not result.rows:
        return discord.Embed(
            title=t("jankenpon.lb.title.global", lang),
            description=t("jankenpon.lb.empty", lang),
            color=discord.Color.gold(),
        )

    embed = discord.Embed(
        title=t("jankenpon.lb.title.global", lang),
        color=discord.Color.gold(),
    )

    lines: List[str] = []
    for row in result.rows:
        lines.append(
            t(
                "jankenpon.lb.entry_global",
                lang,
                medal=_rank_medal(row.rank, bot),
                rank=row.rank,
                user_id=row.user_id,
                level=row.level,
                xp=row.total_xp,
                games=row.total_games,
            )
        )
    embed.description = "\n".join(lines)
    embed.set_footer(text=t("jankenpon.lb.footer.global", lang))
    return embed


# ═════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════
def _rank_medal(rank: int, bot: commands.Bot) -> str:
    """Top 3 con medallas custom; resto con #N plano."""
    if rank == 1:
        return _emoji(bot, "first_place")
    if rank == 2:
        return _emoji(bot, "second_place")
    if rank == 3:
        return _emoji(bot, "third_place")
    return f"**#{rank}**"


def _format_delta(delta: int) -> str:
    if delta > 0:
        return f"+{delta}"
    return str(delta)