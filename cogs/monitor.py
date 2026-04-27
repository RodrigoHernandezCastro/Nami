import discord
from discord import app_commands
from discord.app_commands import Cooldown
from discord.ext import commands, tasks
from obtain_twitch import obtener_streams_en_vivo
from database import db_manager as db
from typing import Optional
import re
from obtain_twitch import obtener_streams_en_vivo, streamer_existe, obtener_detalles_streams

def es_mod(interaction: discord.Interaction) -> bool:
    """Doble verificación de permisos."""
    perms = interaction.user.guild_permissions
    return perms.manage_guild or perms.administrator

def es_nombre_twitch_valido(nombre: str) -> bool:
    return bool(re.fullmatch(r"[a-zA-Z0-9_]{4,25}", nombre))

class MonitorTwitch(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.revisar_stream.start()

    def cog_unload(self):
        self.revisar_stream.cancel()

    # ============================================================
    # COMANDOS
    # ============================================================

    @app_commands.command(name="configurar_canal", description="Define el canal donde se enviarán los anuncios.")
    @app_commands.default_permissions(manage_guild=True)
    async def configurar_canal(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not es_mod(interaction):
            await interaction.response.send_message("No tienes permisos.", ephemeral=True)
            return

        db.registrar_guild(interaction.guild_id, canal.id)
        await interaction.response.send_message(
            f"Canal de anuncios configurado: {canal.mention}", ephemeral=True
        )

    @app_commands.command(name="monitorear", description="Agrega un streamer al monitoreo.")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.choices(tipo_mencion=[
        app_commands.Choice(name="Ninguno", value="ninguno"),
        app_commands.Choice(name="@everyone", value="everyone"),
        app_commands.Choice(name="@here", value="here"),
        app_commands.Choice(name="Rol(es) específico(s)", value="rol"),
    ])
    async def monitorear(
        self,
        interaction: discord.Interaction,
        streamer: str,
        mensaje: str = "live!",
        tipo_mencion: Optional[app_commands.Choice[str]] = None,
        rol: Optional[discord.Role] = None,
        rol2: Optional[discord.Role] = None,
        rol3: Optional[discord.Role] = None,
    ):
        # 1. Permisos
        if not es_mod(interaction):
            await interaction.response.send_message("No tienes permisos.", ephemeral=True)
            return

        # 2. Formato del nombre
        streamer = streamer.strip().lower()
        if not es_nombre_twitch_valido(streamer):
            await interaction.response.send_message(
                "Nombre inválido. Debe tener 4-25 caracteres (letras, números y `_`).",
                ephemeral=True
            )
            return

        # Sanitizar mensaje: eliminar @everyone / @here sueltos para evitar
        # menciones dobles o no deseadas al concatenar con la mención real.
        mensaje = re.sub(r"@(everyone|here)", "", mensaje).strip()

        # 3. Canal configurado
        guild_id = interaction.guild_id
        if not db.obtener_canal_anuncios(guild_id):
            await interaction.response.send_message(
                "Primero configura un canal con `/configurar_canal`.", ephemeral=True
            )
            return

        # 4. Límite
        limite = db.obtener_limite_streamers(guild_id)
        if db.contar_streamers_guild(guild_id) >= limite:
            await interaction.response.send_message(
                f"Has alcanzado el límite de **{limite}** streamers.", ephemeral=True
            )
            return

        # 5. Defer (porque Twitch puede tardar)
        await interaction.response.defer(ephemeral=True)

        # 6. Validar existencia en Twitch
        if not await streamer_existe(streamer):
            await interaction.followup.send(
                f"El streamer **{streamer}** no existe en Twitch.", ephemeral=True
            )
            return

        # 7. Tipo de mención
        tipo_val = tipo_mencion.value if tipo_mencion else "ninguno"
        roles_ids = None
        if tipo_val == "rol":
            # Excluir @everyone y @here: son roles especiales de Discord cuya
            # mención produce "@@everyone" o "@@here" en el mensaje enviado.
            roles_seleccionados = [
                r for r in (rol, rol2, rol3)
                if r is not None and not r.is_default() and r.name != "here"
            ]
            if not roles_seleccionados:
                await interaction.followup.send(
                    "Debes proporcionar al menos un rol válido. Los roles `@everyone` y `@here` no están permitidos aquí; "
                    "usa la opción **@everyone** o **@here** del menú `tipo_mencion`.",
                    ephemeral=True,
                )
                return
            # Eliminar duplicados manteniendo orden
            vistos = set()
            roles_ids = []
            for r in roles_seleccionados:
                if r.id not in vistos:
                    vistos.add(r.id)
                    roles_ids.append(r.id)

        # 8. Insertar en DB
        # roles_ids es una lista (o None); db.agregar_streamer debe aceptar ese formato.
        if not db.agregar_streamer(guild_id, streamer, mensaje, tipo_val, roles_ids):
            await interaction.followup.send(
                f"**{streamer}** ya está siendo monitoreado.", ephemeral=True
            )
            return

        await interaction.followup.send(
            f"Monitoreando a **{streamer}**.", ephemeral=True
        )

    @app_commands.command(name="quitar", description="Elimina un streamer del monitoreo.")
    @app_commands.default_permissions(manage_guild=True)
    async def quitar(self, interaction: discord.Interaction, streamer: str):
        if not es_mod(interaction):
            await interaction.response.send_message("No tienes permisos.", ephemeral=True)
            return

        if db.eliminar_streamer(interaction.guild_id, streamer):
            await interaction.response.send_message(
                f"**{streamer}** eliminado del monitoreo.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"**{streamer}** no estaba en la lista.", ephemeral=True
            )

    @app_commands.command(name="listar", description="Lista los streamers monitoreados.")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def listar(self, interaction: discord.Interaction):
        """Lee el estado directamente de la DB (actualizado por el loop)."""
        streamers = db.obtener_streamers_por_guild(interaction.guild_id)

        if not streamers:
            await interaction.response.send_message(
                "No hay streamers monitoreados en este servidor.", ephemeral=True
            )
            return

        lineas = []
        for s in streamers:
            estado = "En vivo" if s["esta_online"] else "Offline"
            tipo = s["tipo_mencion"]
            if tipo == "everyone":
                mencion_txt = " · @everyone"
            elif tipo == "here":
                mencion_txt = " · @here"
            elif tipo == "rol" and s["rol_mencion_id"]:
                mencion_txt = " · " + " ".join(f"<@&{rid}>" for rid in s["rol_mencion_id"])
            else:
                mencion_txt = ""

            lineas.append(f"{estado} — **{s['nombre_streamer']}**{mencion_txt}")

        embed = discord.Embed(
            title="Streamers monitoreados",
            description="\n".join(lineas),
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Total: {len(streamers)} · Estado actualizado cada 2 min")

        await interaction.response.send_message(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none()  # evita mencionar al mostrar
        )

    @app_commands.command(name="info", description="Muestra información del bot.")
    async def info(self, interaction: discord.Interaction):
        total_guilds = len(self.bot.guilds)
        total_streamers = db.contar_streamers_total()

        embed = discord.Embed(
            title="Información del bot",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Servidores", value=str(total_guilds), inline=True)
        embed.add_field(name="Streamers monitoreados", value=str(total_streamers), inline=True)
        embed.add_field(name="Latencia", value=f"{round(self.bot.latency * 1000)} ms", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ============================================================
    # LOOP DE MONITOREO (OPTIMIZADO CON BATCHING)
    # ============================================================

    @tasks.loop(minutes=2)
    async def revisar_stream(self):
        try:
            streamers = db.obtener_todos_streamers()
            if not streamers:
                return

            nombres_unicos = list({s["nombre_streamer"] for s in streamers})
            detalles_map = await obtener_detalles_streams(nombres_unicos)
            en_vivo_set = set(detalles_map.keys())

            for s in streamers:
                nombre = s["nombre_streamer"]
                estaba_online = bool(s["esta_online"])
                esta_en_vivo = nombre in en_vivo_set

                if esta_en_vivo and not estaba_online:
                    await self._enviar_anuncio(s, detalles_map.get(nombre))
                    db.actualizar_estado_stream(s["id"], True)
                elif not esta_en_vivo and estaba_online:
                    db.actualizar_estado_stream(s["id"], False)
        except Exception as e:
            print(f"[ERROR revisar_stream] {e}")

    
    @revisar_stream.before_loop
    async def antes_revisar(self):
        await self.bot.wait_until_ready()
        print("[Monitor] Loop listo, esperando primera ejecución...")

    # ============================================================
    # HELPERS
    # ============================================================

    async def _enviar_anuncio(self, s, detalles: dict = None):
        canal = self.bot.get_channel(s["canal_anuncios"])
        if canal is None:
            return

        # Construir mención
        tipo = s["tipo_mencion"]
        if tipo == "everyone":
            mencion = "@everyone"
        elif tipo == "here":
            mencion = "@here"
        elif tipo == "rol" and s["rol_mencion_id"]:
            mencion = " ".join(f"<@&{rid}>" for rid in s["rol_mencion_id"])
        else:
            mencion = ""

        nombre = s["nombre_streamer"]
        url = f"https://twitch.tv/{nombre}"

        # Embed visual
        embed = discord.Embed(
            title=detalles.get("title", s["mensaje_custom"]) if detalles else s["mensaje_custom"],
            url=url,
            description=f"Jugando a **{detalles.get('game', 'Desconocido')}**" if detalles else "",
            color=discord.Color.purple()
        )
        embed.set_author(name=f"{nombre} está EN VIVO", url=url)
        
        if detalles:
            if detalles.get("profile_image"):
                embed.set_thumbnail(url=detalles["profile_image"])
            if detalles.get("thumbnail"):
                embed.set_image(url=detalles["thumbnail"])
            embed.add_field(name="Viewers", value=str(detalles.get("viewers", 0)), inline=True)
        
        embed.set_footer(text="Twitch · Nami Bot")

        try:
            # La mención y el mensaje se construyen por separado para evitar
            # que caracteres '@' en mensaje_custom provoquen menciones dobles.
            content = f"{mencion}\n{s['mensaje_custom']}" if mencion else s["mensaje_custom"]
            await canal.send(
                content=content,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(everyone=True, roles=True)
            )
        except discord.Forbidden:
            print(f"[WARN] Sin permisos en canal {canal.id}")
        except Exception as e:
            print(f"[ERROR enviar_anuncio] {e}")

    @revisar_stream.error
    async def revisar_stream_error(self, error):
        """Captura errores que escapan del loop, para que no muera."""
        print(f"[CRÍTICO revisar_stream] {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(MonitorTwitch(bot))