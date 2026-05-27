# main.py
import asyncio
import sys
import traceback

from src.infrastructure.config.settings import Settings
from src.composition_root.container import Container
from src.presentation.discord_bot.bot import NamiBot


async def main() -> None:
    settings = Settings()
    container = Container(settings)

    try:
        await container.startup()
    except Exception as e:
        print(f"Error durante el startup del container: {e}")
        traceback.print_exc()
        # Si el startup falló a medias, igual intentamos limpiar lo que
        # sí se llegó a crear (p.ej. el pool de DB) sin enmascarar la
        # excepción original.
        try:
            await container.shutdown()
        except Exception as shutdown_err:
            print(f"(Error adicional durante shutdown tras fallo de startup: {shutdown_err})")
        sys.exit(1)

    bot = NamiBot(container=container, settings=settings)

    try:
        await bot.start(settings.DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\nApagando bot...")
    except Exception as e:
        # Imprime el error real que rompió el bot (p.ej. el del setup_hook)
        # ANTES de intentar el shutdown, para que el shutdown nunca
        # enmascare la causa raíz aunque también falle.
        print(f"Error fatal durante la ejecución del bot: {e}")
        traceback.print_exc()
    finally:
        # Cada paso del cleanup va en su propio try para que un fallo
        # en uno no impida ejecutar los siguientes.
        try:
            if not bot.is_closed():
                await bot.close()
        except Exception as e:
            print(f"Error cerrando el bot: {e}")
            traceback.print_exc()

        try:
            await container.shutdown()
        except Exception as e:
            print(f"Error en container.shutdown(): {e}")
            traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot apagado correctamente.")
