"""
Jetfuel (``/i/jfapi/...``), X's server-driven UI endpoints - Creator Studio and the like.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from httpx import Response

from ..constants import DOMAIN

if TYPE_CHECKING:
    from .client import Client


class Endpoint:
    BASE = f'https://{DOMAIN}/i/jfapi'
    # Creator Studio home (which programs the account is eligible for).
    CREATORS_STUDIO = f'{BASE}/creators/studio'
    # Requirements of the original content rewards program and the account's progress.
    CREATORS_ORIGINAL_CONTENT_REWARDS = f'{BASE}/creators/original_content_rewards'
    # Requirements of creator subscriptions and the account's progress.
    CREATORS_SUBSCRIPTIONS_ELIGIBILITY = f'{BASE}/creators/subscriptionsv2/eligibility'


def _local_iana_timezone() -> str | None:
    """The local time zone as an IANA name ("Asia/Tokyo"), or None if it cannot be told."""
    try:
        import tzlocal  # optional
        name = tzlocal.get_localzone_name()
        if name:
            return name
    except Exception:
        pass
    tz = os.environ.get('TZ')
    if tz and '/' in tz:
        return tz
    try:
        target = os.path.realpath('/etc/localtime')
        if 'zoneinfo/' in target:
            return target.split('zoneinfo/', 1)[1]
    except Exception:
        pass
    return None


class JetfuelClient:
    """
    Jetfuel endpoint layer. Returns the raw body (``bytes``) and the
    response: the body is a binary document served as ``text/plain`` (not
    JSON and not base64), decoded by :class:`twikit._jetfuel.JetfuelDocument`.

    The web client (2026-10) sends ``x-jf-v: JP-5``, ``x-jf-client-theme``
    and the ``/i/jf/`` page as Referer. Rate limit is 5000 per 15 minutes.
    """

    #: Protocol version the web client sends (``x-jf-v``).
    PROTOCOL_VERSION = 'JP-5'

    def __init__(self, base: Client) -> None:
        self.base = base
        #: ``x-jf-client-theme`` ("light" / "dark"). Only affects colour styles.
        self.theme = 'light'
        #: Sent as the ``timezone`` header when known (IANA name). Set to None to omit it.
        self.timezone = _local_iana_timezone()

    async def get(self, url: str) -> tuple[bytes, Response]:
        """
        Fetches any Jetfuel page.

        Parameters
        ----------
        url : :class:`str`
            An :class:`Endpoint` URL, or a path such as ``creators/studio``.

        Returns
        -------
        tuple[:class:`bytes`, :class:`httpx.Response`]
            The raw binary body and the response.
        """
        if not url.lower().startswith('http'):
            url = Endpoint.BASE + (url if url.startswith('/') else '/' + url)

        headers = self.base._base_headers
        headers['x-jf-v'] = self.PROTOCOL_VERSION
        headers['x-jf-client-theme'] = self.theme
        # The page that embeds the Jetfuel frame lives under /i/jf/, not /i/jfapi/.
        headers['Referer'] = url.replace('/i/jfapi/', '/i/jf/')
        if self.timezone:
            headers['timezone'] = self.timezone
        _, response = await self.base.get(url, headers=headers)
        return response.content, response

    async def creators_studio(self) -> tuple[bytes, Response]:
        return await self.get(Endpoint.CREATORS_STUDIO)

    async def creators_original_content_rewards(self) -> tuple[bytes, Response]:
        return await self.get(Endpoint.CREATORS_ORIGINAL_CONTENT_REWARDS)

    async def creators_subscriptions_eligibility(self) -> tuple[bytes, Response]:
        return await self.get(Endpoint.CREATORS_SUBSCRIPTIONS_ELIGIBILITY)
