import json
import re
import string
from pathlib import Path

import pytest

from src.domain.exceptions.domain_exceptions import (
    StreamerLimitReachedError, StreamerNotOnTwitchError, StreamerAlreadyExistsError,
    ChannelNotConfiguredError, ChannelNotFoundError, StreamerNotFoundError,
    YouTubeChannelNotFoundError, ChannelLimitReachedError, DomainError,
)
from src.presentation.discord_bot.error_messages import domain_error_message


class _FakeI18n:
    """Resolver falso: devuelve key + kwargs para verificar el contrato."""
    async def t(self, key: str, guild_id, **kwargs):
        return f"{key}|{sorted(kwargs.items())}"


_locales_dir = Path(__file__).resolve().parent.parent.parent / "src" / "resources" / "locales"


# =========================================================================
# Tests de contrato: cada excepción lleva los params correctos
# =========================================================================

@pytest.mark.asyncio
async def test_limit_carries_param():
    msg = await domain_error_message(StreamerLimitReachedError(limit=15), 1, _FakeI18n())
    assert msg == "error.streamer_limit_reached|[('limit', 15)]"


@pytest.mark.asyncio
async def test_not_on_twitch_carries_username():
    msg = await domain_error_message(StreamerNotOnTwitchError(username="foo"), 1, _FakeI18n())
    assert msg == "error.streamer_not_on_twitch|[('username', 'foo')]"


@pytest.mark.asyncio
async def test_already_exists_carries_username():
    msg = await domain_error_message(StreamerAlreadyExistsError(username="bar"), 1, _FakeI18n())
    assert msg == "error.streamer_already_exists|[('username', 'bar')]"


@pytest.mark.asyncio
async def test_no_params_error():
    msg = await domain_error_message(ChannelNotConfiguredError(), 1, _FakeI18n())
    assert msg == "error.channel_not_configured|[]"


@pytest.mark.asyncio
async def test_channel_not_found_carries_channel():
    msg = await domain_error_message(ChannelNotFoundError(channel="UCxxx"), 1, _FakeI18n())
    assert msg == "error.channel_not_found|[('channel', 'UCxxx')]"


@pytest.mark.asyncio
async def test_streamer_not_found_carries_username():
    msg = await domain_error_message(StreamerNotFoundError(username="test"), 1, _FakeI18n())
    assert msg == "error.streamer_not_found|[('username', 'test')]"


@pytest.mark.asyncio
async def test_youtube_channel_not_found_carries_channel():
    msg = await domain_error_message(YouTubeChannelNotFoundError(channel="@foo"), 1, _FakeI18n())
    assert msg == "error.youtube_channel_not_found|[('channel', '@foo')]"


@pytest.mark.asyncio
async def test_channel_limit_carries_param():
    msg = await domain_error_message(ChannelLimitReachedError(limit=5), 1, _FakeI18n())
    assert msg == "error.channel_limit_reached|[('limit', 5)]"


@pytest.mark.asyncio
async def test_unknown_domain_error_falls_back_to_generic():
    class _CustomDomainError(DomainError):
        pass
    msg = await domain_error_message(_CustomDomainError("nope"), 1, _FakeI18n())
    assert msg.startswith("error.domain_generic")


@pytest.mark.asyncio
async def test_non_domain_error_falls_back_to_unexpected():
    msg = await domain_error_message(ValueError("boom"), 1, _FakeI18n())
    assert msg.startswith("error.unexpected")


# =========================================================================
# Test de contrato placeholder ↔ param (evita ver "{username}" literal)
# =========================================================================

def _extract_placeholders(template: str) -> set[str]:
    """Extrae los nombres de {placeholders} de un template."""
    return {fn for _, fn, _, _ in string.Formatter().parse(template) if fn is not None}


# Mapa: nombre de key -> (clase excepción, kwargs esperados)
_ERROR_CONTRACT: dict[str, tuple[type[DomainError], dict]] = {
    "error.streamer_already_exists":   (StreamerAlreadyExistsError,   {"username": "x"}),
    "error.streamer_limit_reached":    (StreamerLimitReachedError,    {"limit": 1}),
    "error.streamer_not_on_twitch":    (StreamerNotOnTwitchError,     {"username": "x"}),
    "error.channel_not_configured":    (ChannelNotConfiguredError,    {}),
    "error.streamer_not_found":        (StreamerNotFoundError,        {"username": "x"}),
    "error.youtube_channel_not_found": (YouTubeChannelNotFoundError,  {"channel": "x"}),
    "error.channel_not_found":         (ChannelNotFoundError,         {"channel": "x"}),
    "error.channel_limit_reached":     (ChannelLimitReachedError,     {"limit": 1}),
}


def test_placeholders_match_params_across_all_locales():
    """Para cada locale JSON, verifica que los placeholders del template
    coinciden con las claves de `params` que produce la excepción."""
    for lang_file in _locales_dir.glob("*.json"):
        with open(lang_file, encoding="utf-8") as f:
            translations = json.load(f)

        for key, (exc_cls, expected_params) in _ERROR_CONTRACT.items():
            template = translations.get(key)
            assert template is not None, f"{lang_file.name}: falta key '{key}'"

            placeholders = _extract_placeholders(template)
            expected_placeholders = set(expected_params.keys())

            assert placeholders == expected_placeholders, (
                f"{lang_file.name}[{key}]: "
                f"placeholders {placeholders} != expected {expected_placeholders}"
            )


def test_error_keys_exist_in_all_locales():
    """Todas las keys de error.* existen en los 4 archivos locale."""
    error_keys = set(_ERROR_CONTRACT.keys()) | {"error.domain_generic", "error.unexpected"}
    for lang_file in _locales_dir.glob("*.json"):
        with open(lang_file, encoding="utf-8") as f:
            translations = json.load(f)
        for key in error_keys:
            assert key in translations, f"{lang_file.name}: falta '{key}'"


def test_no_extra_error_keys():
    """No hay keys error.* extrañas en los JSON que no estén en el contrato."""
    known = set(_ERROR_CONTRACT.keys()) | {"error.domain_generic", "error.unexpected"}
    for lang_file in _locales_dir.glob("*.json"):
        with open(lang_file, encoding="utf-8") as f:
            translations = json.load(f)
        file_error_keys = {k for k in translations if k.startswith("error.")}
        unexpected = file_error_keys - known
        assert not unexpected, f"{lang_file.name}: keys extrañas: {unexpected}"
