# src/presentation/discord_bot/cogs/jankenpon_cog.py
"""
Cog del juego !jankenpon.

Cambios v5:
- Pasa `bot=self.bot` a los builders del embed para que puedan
  acceder al AppEmojiRegistry vía `bot.app_emojis`.
- El resto de la lógica (autodelete manual, no borrar mensaje del
  usuario, cooldown, i18n) se mantiene de v4.
"""
from __future__ import annotations

import asyncio
from typing import Optional

import discord
from discord.ext import commands

from src.application.interfaces.translator import ITranslator
from src.application.use_cases.get_global_leaderboard import (
    GetGlobalLeaderboardUseCase,
    GlobalLeaderboardQuery,
)
from src.application.use_cases.get_guild_leaderboard import (
    GetGuildLeaderboardUseCase,
    GuildLeaderboardQuery,
)
from src.application.use_cases.play_jankenpon import (
    PlayJankenponCommand,
    PlayJankenponUseCase,
)
from src.presentation.discord_bot.i18n_helper import GuildLanguageResolver
from src.presentation.discord_bot.jankenpon_parser import (
    parse_move,
    valid_examples,
)
from src.presentation.discord_bot.views.jankenpon_embed import (
    build_global_leaderboard_embed,
    build_guild_leaderboard_embed,
    build_match_embed,
)


AUTODELETE_SECONDS = 10
LEADERBOARD_LIMIT = 5


class JankenponCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        play_uc: PlayJankenponUseCase,
        guild_lb_uc: GetGuildLeaderboardUseCase,
        global_lb_uc: GetGlobalLeaderboardUseCase,
        lang_resolver: GuildLanguageResolver,
        translator: ITranslator,
    ) -> None:
        super().__init__()
        self.bot = bot
        self._play_uc = play_uc
        self._guild_lb_uc = guild_lb_uc
        self._global_lb_uc = global_lb_uc
        self._i18n = lang_resolver
        self._translator = translator
        # Logger del container, si está disponible.
        container = getattr(bot, "container", None)
        self._logger = container.logger if container else None

    # =====================================================================
    # !jankenpon <jugada>
    # =====================================================================
    @commands.command(
        name="jankenpon",
        aliases=[
            "piedra-papel-tijera",       # es
            "kamien-papier-nozyce",      # pl
        ],
    )
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    @commands.guild_only()
    async def jankenpon(
        self, ctx: commands.Context, *, jugada: Optional[str] = None
    ) -> None:
        if jugada is None:
            await self._send_autodelete(ctx, content=await self._t_usage(ctx))
            return

        move = parse_move(jugada)
        if move is None:
            await self._send_autodelete(
                ctx, content=await self._t_invalid(ctx, jugada)
            )
            return

        result = await self._play_uc.execute(
            PlayJankenponCommand(
                user_id=ctx.author.id,
                guild_id=ctx.guild.id,
                user_move=move,
            )
        )

        lang = await self._i18n.get_lang(ctx.guild.id)
        embed = build_match_embed(
            result=result,
            user_display=ctx.author.display_name,
            lang=lang,
            translator=self._translator,
            bot=self.bot,
        )

        await self._send_autodelete(ctx, embed=embed)

    # =====================================================================
    # !jankenpon-lb [global]
    # =====================================================================
    @commands.command(
        name="jankenpon-lb",
        aliases=[
            "jankenpon-leaderboard",
            "jankenpon-top",
            "jankenpon-ranking",
        ],
    )
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    @commands.guild_only()
    async def jankenpon_lb(
        self, ctx: commands.Context, scope: Optional[str] = None
    ) -> None:
        is_global = scope is not None and scope.strip().lower() in {
            "global", "g",
            "mundial", "todos",
            "globalny", "swiat",
            "世界", "グローバル",
        }

        lang = await self._i18n.get_lang(ctx.guild.id)

        if is_global:
            result = await self._global_lb_uc.execute(
                GlobalLeaderboardQuery(limit=LEADERBOARD_LIMIT)
            )
            embed = build_global_leaderboard_embed(
                result=result,
                lang=lang,
                translator=self._translator,
                bot=self.bot,
            )
        else:
            result = await self._guild_lb_uc.execute(
                GuildLeaderboardQuery(
                    guild_id=ctx.guild.id,
                    limit=LEADERBOARD_LIMIT,
                )
            )
            embed = build_guild_leaderboard_embed(
                result=result,
                guild_name=ctx.guild.name,
                lang=lang,
                translator=self._translator,
                bot=self.bot,
            )

        await self._send_autodelete(ctx, embed=embed)

    # =====================================================================
    # Errores locales
    # =====================================================================
    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            lang = await self._i18n.get_lang(
                ctx.guild.id if ctx.guild else None
            )
            msg = self._translator.t(
                "jankenpon.cooldown",
                lang,
                seconds=round(error.retry_after, 1),
            )
            await self._send_autodelete(ctx, content=msg)
            return

        if isinstance(error, commands.NoPrivateMessage):
            lang = await self._i18n.get_lang(None)
            msg = self._translator.t("jankenpon.guild_only", lang)
            try:
                await ctx.reply(msg, mention_author=False)
            except discord.HTTPException:
                pass
            return

        raise error

    # =====================================================================
    # Helpers de traducción
    # =====================================================================
    async def _t_usage(self, ctx: commands.Context) -> str:
        lang = await self._i18n.get_lang(ctx.guild.id)
        return self._translator.t(
            "jankenpon.usage", lang, examples=valid_examples()
        )

    async def _t_invalid(self, ctx: commands.Context, raw: str) -> str:
        lang = await self._i18n.get_lang(ctx.guild.id)
        safe_raw = discord.utils.escape_markdown(raw[:32])
        return self._translator.t(
            "jankenpon.invalid_move",
            lang,
            input=safe_raw,
            examples=valid_examples(),
        )

    # =====================================================================
    # Envío con autodelete MANUAL (no toca el mensaje del usuario)
    # =====================================================================
    async def _send_autodelete(
        self,
        ctx: commands.Context,
        *,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ) -> None:
        try:
            sent = await ctx.send(
                content=content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except discord.HTTPException as exc:
            if self._logger:
                self._logger.warning(
                    "jankenpon_send_failed",
                    error=str(exc),
                    has_content=content is not None,
                    has_embed=embed is not None,
                )
            return

        asyncio.create_task(self._delete_later(sent))

    async def _delete_later(self, message: discord.Message) -> None:
        try:
            await asyncio.sleep(AUTODELETE_SECONDS)
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            if self._logger:
                self._logger.warning(
                    "jankenpon_autodelete_no_perms",
                    channel_id=message.channel.id,
                    message_id=message.id,
                    hint="El bot necesita Manage Messages para auto-borrar.",
                )
        except discord.HTTPException as exc:
            if self._logger:
                self._logger.warning(
                    "jankenpon_autodelete_failed",
                    error=str(exc),
                    message_id=message.id,
                )