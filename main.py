# main.py
import asyncio
import sys
from src.infrastructure.config.settings import Settings
from src.composition_root.container import Container
from src.presentation.discord_bot.bot import NamiBot


async def main() -> None:
    settings = Settings()
    container = Container(settings)

    try:
        await container.startup()
    except Exception as e:
        print(f"Error durante el startup: {e}")
        sys.exit(1)

    bot = NamiBot(container=container, settings=settings)

    try:
        await bot.start(settings.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n⏹ Apagando bot...")
    finally:
        await bot.close()
        await container.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot apagado correctamente.")