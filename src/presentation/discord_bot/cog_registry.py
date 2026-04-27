from typing import Protocol, List, Type
from discord.ext import commands


class ICogFactory(Protocol):
    """Contrato que todo cog-factory debe cumplir."""
    def build(self, bot: commands.Bot, container) -> commands.Cog: ...


class CogRegistry:
    """
    Registro central de cogs. Añadir una feature nueva =
    registrar una factory, SIN modificar el bot principal.
    """
    _factories: List[ICogFactory] = []

    @classmethod
    def register(cls, factory: ICogFactory) -> ICogFactory:
        cls._factories.append(factory)
        return factory

    @classmethod
    async def load_all(cls, bot: commands.Bot, container) -> None:
        for factory in cls._factories:
            cog = factory.build(bot, container)
            await bot.add_cog(cog)