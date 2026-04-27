import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
from database import db_manager as db
from obtain_twitch import cerrar_session

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True

bot = commands.AutoShardedBot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user} ({bot.user.id})")
    print(f"En {len(bot.guilds)} servidores")
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} slash commands sincronizados.")
    except Exception as e:
        print(f"[ERROR sync] {e}")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Espera **{error.retry_after:.1f}s** antes de usar este comando de nuevo.",
            ephemeral=True
        )
    else:
        print(f"[ERROR app_command] {error}")

@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.mention}! How are you?')

async def hola(ctx):
    await ctx.send(f'¡Hola {ctx.author.mention}! ¿Cómo estás?')

@bot.command()
async def info_en(ctx):
    servidor = ctx.guild.name
    usuarios = ctx.guild.member_count
    await ctx.send(f'we are in {servidor}, which has {usuarios} members.')

@bot.command()
async def info_es(ctx):
    servidor = ctx.guild.name
    usuarios = ctx.guild.member_count
    await ctx.send(f'Estamos en {servidor}, que tiene {usuarios} miembros.')

@bot.event
async def on_guild_join(guild):
    """Registra el servidor automáticamente al entrar."""
    try:
        db.registrar_guild(guild.id)
        print(f"[+] Unido a {guild.name} ({guild.id}) - Registrado en DB")
    except Exception as e:
        print(f"[ERROR on_guild_join] {e}")


@bot.event
async def on_guild_remove(guild):
    """Limpia completamente los datos del servidor."""
    try:
        streamers_eliminados = db.contar_streamers_guild(guild.id)
        db.eliminar_guild(guild.id)
        print(f"[-] Expulsado de {guild.name} ({guild.id}) - "
              f"{streamers_eliminados} streamers eliminados.")
    except Exception as e:
        print(f"[ERROR on_guild_remove] {e}")


async def main():
    db.inicializar_db()
    print("Base de datos lista.")

    async with bot:
        await bot.load_extension("cogs.monitor")
        print("Cog cargado: monitor.py")
        try:
            await bot.start(TOKEN)
        finally:
            await cerrar_session()
            print("Sesión HTTP cerrada.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot detenido manualmente.")