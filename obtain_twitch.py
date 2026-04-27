import aiohttp
import asyncio
import time
import os
from dotenv import load_dotenv
from typing import List, Dict, Set

load_dotenv()

CLIENT_ID     = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_ACCESS_TOKEN")

_token_cache = {"token": None, "expira_en": 0}
_session: aiohttp.ClientSession = None


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session

async def streamer_existe(nombre: str) -> bool:
    """Verifica que el streamer exista en Twitch."""
    try:
        token = await _obtener_token()
    except Exception:
        return True

    session = await _get_session()
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    try:
        async with session.get(
            "https://api.twitch.tv/helix/users",
            headers=headers, params={"login": nombre.lower()}, timeout=10
        ) as r:
            if r.status != 200:
                return True
            datos = await r.json()
            return len(datos.get("data", [])) > 0
    except Exception:
        return True

async def _obtener_token() -> str:
    """Genera/renueva el App Access Token."""
    if _token_cache["token"] and time.time() < _token_cache["expira_en"]:
        return _token_cache["token"]

    session = await _get_session()
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    async with session.post("https://id.twitch.tv/oauth2/token", data=data) as r:
        r.raise_for_status()
        info = await r.json()
        _token_cache["token"] = info["access_token"]
        _token_cache["expira_en"] = time.time() + info["expires_in"] - 300
        print("[Twitch] Token renovado.")
        return _token_cache["token"]

async def _request_con_reintentos(session, url, headers, params, max_intentos=3):
    """Realiza un GET con backoff exponencial ante fallos."""
    for intento in range(max_intentos):
        try:
            async with session.get(url, headers=headers, params=params, timeout=15) as r:
                if r.status == 200:
                    return await r.json()
                if r.status == 401:
                    _token_cache["token"] = None
                    return None
                if r.status == 429:
                    espera = 2 ** intento
                    print(f"[Twitch] Rate limit. Esperando {espera}s...")
                    await asyncio.sleep(espera)
                    continue
                if 500 <= r.status < 600:
                    print(f"[Twitch] Error servidor {r.status}, reintentando...")
                    await asyncio.sleep(2 ** intento)
                    continue
                return None
        except asyncio.TimeoutError:
            print(f"[Twitch] Timeout intento {intento + 1}")
            await asyncio.sleep(2 ** intento)
        except aiohttp.ClientError as e:
            print(f"[Twitch] ClientError: {e}")
            await asyncio.sleep(2 ** intento)
        except Exception as e:
            print(f"[Twitch] Error inesperado: {e}")
            return None
    return None

async def obtener_streams_en_vivo(streamers: List[str]) -> Set[str]:
    """
    Recibe una lista de nombres de streamers y devuelve un set 
    con los que están actualmente en vivo. Usa batching (100 por request).
    """
    if not streamers:
        return set()

    # Normalizar
    streamers = [s.strip().lower() for s in streamers if s.strip()]
    streamers = list(set(streamers))  # eliminar duplicados

    try:
        token = await _obtener_token()
    except Exception as e:
        print(f"[ERROR Twitch] No se pudo obtener token: {e}")
        return set()

    session = await _get_session()
    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    en_vivo = set()

    # Dividir en lotes de 100 (límite de Twitch)
    for i in range(0, len(streamers), 100):
        lote = streamers[i:i+100]
        params = [("user_login", s) for s in lote]

        try:
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers, params=params, timeout=15
            ) as r:
                if r.status == 401:
                    _token_cache["token"] = None
                    print("[Twitch] Token rechazado, se renovará.")
                    continue

                if r.status == 429:
                    print("[Twitch] Rate limit alcanzado. Esperando...")
                    await asyncio.sleep(5)
                    continue

                if r.status != 200:
                    print(f"[Twitch] HTTP {r.status}: {await r.text()}")
                    continue

                datos = await r.json()
                for stream in datos.get("data", []):
                    if stream.get("type") == "live":
                        en_vivo.add(stream["user_login"].lower())

        except asyncio.TimeoutError:
            print("[Twitch] Timeout en batch request.")
        except Exception as e:
            print(f"[Twitch] Error en batch: {e}")

    return en_vivo

async def obtener_detalles_streams(streamers: List[str]) -> Dict[str, dict]:
    """Devuelve un dict {nombre: {title, game, thumbnail, profile_image}}."""
    if not streamers:
        return {}

    try:
        token = await _obtener_token()
    except Exception as e:
        print(f"[ERROR Twitch] {e}")
        return {}

    session = await _get_session()
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
    detalles = {}

    for i in range(0, len(streamers), 100):
        lote = streamers[i:i+100]
        params = [("user_login", s) for s in lote]

        try:
            # 1. Streams en vivo
            async with session.get(
                "https://api.twitch.tv/helix/streams",
                headers=headers, params=params, timeout=15
            ) as r:
                if r.status != 200:
                    continue
                streams_data = (await r.json()).get("data", [])

            # 2. Info de usuarios (para el avatar)
            async with session.get(
                "https://api.twitch.tv/helix/users",
                headers=headers, params=params, timeout=15
            ) as r:
                users_data = (await r.json()).get("data", []) if r.status == 200 else []

            users_map = {u["login"].lower(): u for u in users_data}

            for stream in streams_data:
                if stream.get("type") != "live":
                    continue
                login = stream["user_login"].lower()
                user_info = users_map.get(login, {})
                detalles[login] = {
                    "title": stream.get("title", "Sin título"),
                    "game": stream.get("game_name", "Sin categoría"),
                    "viewers": stream.get("viewer_count", 0),
                    "thumbnail": stream.get("thumbnail_url", "").replace("{width}", "1280").replace("{height}", "720"),
                    "profile_image": user_info.get("profile_image_url", "")
                }
        except Exception as e:
            print(f"[Twitch] Error obteniendo detalles: {e}")

    return detalles

async def cerrar_session():
    """Cierra la sesión HTTP (llamar al shutdown del bot)."""
    global _session
    if _session and not _session.closed:
        await _session.close()