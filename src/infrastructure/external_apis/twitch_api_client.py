import aiohttp
from typing import Dict, List, Optional

from aiohttp_retry import ExponentialRetry, RetryClient, retry_options
from src.application.interfaces.twitch_service import ITwitchService
from src.application.interfaces.logger import ILogger


class TwitchAPIClient(ITwitchService):
    """
    Cliente Twitch con gestión de token OAuth y sesión reutilizable.
    """

    BASE_URL = "https://api.twitch.tv/helix"
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        logger: ILogger,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self._logger = logger
        self._access_token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._session: Optional[RetryClient] = None

    async def initialize(self) -> None:
        """Crea la sesión HTTP y obtiene el primer token."""
        retry_options = ExponentialRetry(attempts=3, start_timeout=1.0, max_timeout=5.0)
        client_session = aiohttp.ClientSession()
        self._session = RetryClient(client_session=client_session, retry_options=retry_options)
        await self._refresh_token()
        self._logger.info("twitch_client_initialized")

    async def close(self) -> None:
        """Cierra la sesión HTTP al apagar el bot."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self._logger.info("twitch_client_closed")

    async def _refresh_token(self) -> None:
        """Solicita un nuevo access_token a Twitch."""
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }
        async with self._session.post(self.TOKEN_URL, params=params) as resp:
            data = await resp.json()
            self._access_token = data.get("access_token")
            if not self._access_token:
                self._logger.error("twitch_token_error", response=data)
                raise RuntimeError("No se pudo obtener token de Twitch")
            self._logger.info("twitch_token_refreshed")

    def _headers(self) -> dict:
        return {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {self._access_token}",
        }

    async def user_exists(self, username: str) -> bool:
        """Verifica si un usuario de Twitch existe."""
        if not self._access_token:
            await self._refresh_token()

        url = f"{self.BASE_URL}/users"
        params = {"login": username.lower()}

        async with self._session.get(url, headers=self._headers(), params=params) as resp:
            if resp.status == 401:
                await self._refresh_token()
                return await self.user_exists(username)

            if resp.status != 200:
                self._logger.warning("twitch_user_check_failed", status=resp.status)
                return False

            data = await resp.json()
            return len(data.get("data", [])) > 0

    async def get_live_streams_details(
        self, usernames: List[str]
    ) -> Dict[str, dict]:
        """
        Consulta streams en vivo y devuelve un dict {username: stream_data}.
        Twitch permite hasta 100 usuarios por petición.
        """
        if not usernames:
            return {}

        if not self._access_token:
            await self._refresh_token()

        # Dividir en chunks de 100
        result: Dict[str, dict] = {}
        for i in range(0, len(usernames), 100):
            chunk = usernames[i:i + 100]
            params = [("user_login", name.lower()) for name in chunk]

            url = f"{self.BASE_URL}/streams"
            async with self._session.get(url, headers=self._headers(), params=params) as resp:
                if resp.status == 401:
                    await self._refresh_token()
                    return await self.get_live_streams_details(usernames)

                if resp.status != 200:
                    self._logger.error("twitch_streams_error", status=resp.status)
                    continue

                data = await resp.json()
                for stream in data.get("data", []):
                    result[stream["user_login"].lower()] = stream

        return result