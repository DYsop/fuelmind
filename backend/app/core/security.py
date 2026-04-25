from __future__ import annotations

import ipaddress

from fastapi import Header, HTTPException, Request, status

from app.core.config import Settings


def is_private_host(host: str | None) -> bool:
    if not host:
        return False
    if host in {"127.0.0.1", "::1", "localhost", "testclient"}:
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback


async def verify_request_origin(request: Request, settings: Settings) -> None:
    if settings.allow_public_api:
        return

    forwarded = request.headers.get("x-forwarded-for", "")
    forwarded_host = forwarded.split(",")[0].strip() if forwarded else None
    client_host = forwarded_host or (request.client.host if request.client else None)
    if not is_private_host(client_host):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FuelMind ist standardmaessig nur fuer lokale/private Netze freigegeben.",
        )


async def verify_internal_token(
    request: Request,
    x_app_token: str | None = Header(default=None, alias="X-App-Token"),
) -> None:
    settings: Settings = request.app.state.settings
    await verify_request_origin(request, settings)
    if settings.app_internal_token and x_app_token != settings.app_internal_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fehlender oder ungueltiger interner Zugriffstoken.",
        )

