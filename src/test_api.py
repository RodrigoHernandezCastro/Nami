# test_twitch.py
import asyncio
import sys
sys.path.insert(0, "src")

from infrastructure.external_apis.twitch_api_client import TwitchAPIClient
from infrastructure.config.settings import Settings

async def test():
    settings = Settings()
    client = TwitchAPIClient(
        client_id=settings.TWITCH_CLIENT_ID,
        client_secret=settings.TWITCH_CLIENT_SECRET,
        logger=None,
    )
    await client.initialize()
    print("Twitch OK!")
    exists = await client.user_exists("shroud")
    print(f"shroud existe: {exists}")
    await client.close()

asyncio.run(test())