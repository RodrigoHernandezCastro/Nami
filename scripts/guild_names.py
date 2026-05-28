import discord
import os
import asyncio
from dotenv import load_dotenv

# Cargar las variables de entorno para obtener el DISCORD_TOKEN
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

class AnalizadorBot(discord.Client):
    def __init__(self):
        # Solo necesitamos los intents por defecto para leer la lista de servidores
        intents = discord.Intents.default()
        super().__init__(intents=intents)

    async def on_ready(self):
        print(f"Logueado exitosamente como {self.user}")
        print("-" * 50)
        print(f"{'GUILD ID':<20} | {'NOMBRE DEL SERVIDOR'}")
        print("-" * 50)
        
        # self.guilds contiene todos los servidores donde está el bot
        total_servidores = len(self.guilds)
        
        for guild in self.guilds:
            print(f"{guild.id:<20} | {guild.name}")
            
        print("-" * 50)
        print(f"Número total de servidores: {total_servidores}")
        
        # Apagamos el script automáticamente una vez que terminamos de leer
        print("\nDesconectando...")
        await self.close()

if __name__ == "__main__":
    if not TOKEN:
        print("Error: No se encontró DISCORD_TOKEN en el archivo .env")
    else:
        print("Iniciando análisis de servidores...")
        cliente = AnalizadorBot()
        cliente.run(TOKEN)