from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import AlertEvent, AlertRule, NotificationChannelEnum, Station
from app.services.station_service import StationService


logger = get_logger(__name__)


class AlertService:
    def __init__(self, station_service: StationService) -> None:
        self.station_service = station_service

    async def list_rules(self, session: AsyncSession) -> list[AlertRule]:
        result = await session.execute(select(AlertRule).order_by(AlertRule.created_at.desc()))
        return list(result.scalars().all())

    async def create_rule(self, session: AsyncSession, payload: dict[str, Any]) -> AlertRule:
        rule = AlertRule(
            name=payload["name"],
            fuel_type=payload["fuel_type"],
            max_price=Decimal(str(payload["max_price"])),
            lat=Decimal(str(payload["lat"])),
            lng=Decimal(str(payload["lng"])),
            radius_km=Decimal(str(payload["radius_km"])),
            enabled=payload["enabled"],
            notification_channel=NotificationChannelEnum(payload["notification_channel"]),
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def update_rule(self, session: AsyncSession, rule_id: str, payload: dict[str, Any]) -> AlertRule:
        rule = await session.get(AlertRule, rule_id)
        if not rule:
            raise ValueError("Alert-Regel nicht gefunden.")
        for key, value in payload.items():
            if key in {"max_price", "lat", "lng", "radius_km"}:
                setattr(rule, key, Decimal(str(value)))
            elif key == "notification_channel":
                setattr(rule, key, NotificationChannelEnum(value))
            else:
                setattr(rule, key, value)
        await session.commit()
        await session.refresh(rule)
        return rule

    async def delete_rule(self, session: AsyncSession, rule_id: str) -> None:
        rule = await session.get(AlertRule, rule_id)
        if not rule:
            raise ValueError("Alert-Regel nicht gefunden.")
        await session.delete(rule)
        await session.commit()

    async def list_events(self, session: AsyncSession) -> list[dict[str, Any]]:
        result = await session.execute(
            select(AlertEvent, AlertRule, Station)
            .join(AlertRule, AlertEvent.alert_rule_id == AlertRule.id)
            .join(Station, AlertEvent.station_id == Station.id)
            .order_by(AlertEvent.triggered_at.desc())
        )
        return [
            {
                "id": event.id,
                "alert_rule_id": rule.id,
                "station_id": station.external_station_id,
                "station_name": station.name,
                "fuel_type": event.fuel_type.value,
                "price": float(event.price),
                "triggered_at": event.triggered_at,
                "message": event.message,
                "delivered": event.delivered,
                "delivered_at": event.delivered_at,
            }
            for event, rule, station in result.all()
        ]

    async def check_alerts(self, session: AsyncSession) -> dict[str, Any]:
        rules = await self.list_rules(session)
        events_created = 0
        checked_at = datetime.now(UTC)
        for rule in rules:
            if not rule.enabled:
                continue
            nearby = await self.station_service.search_nearby(
                lat=float(rule.lat),
                lng=float(rule.lng),
                radius_km=float(rule.radius_km),
                fuel_type=rule.fuel_type.value,
                sort="price",
            )
            for item in nearby["items"]:
                price = item.get("price")
                if price is None or float(price) > float(rule.max_price):
                    continue

                station = await self.station_service.upsert_station(session, item)
                if await self._recent_duplicate_exists(session, rule.id, station.id):
                    continue

                message = (
                    f"{item['name']} bietet {rule.fuel_type.value.upper()} aktuell fuer "
                    f"{float(price):.3f} EUR innerhalb von {item.get('distance_km') or 0:.1f} km an."
                )
                session.add(
                    AlertEvent(
                        alert_rule_id=rule.id,
                        station_id=station.id,
                        fuel_type=rule.fuel_type,
                        price=Decimal(str(price)),
                        triggered_at=checked_at,
                        message=message,
                        delivered=rule.notification_channel == NotificationChannelEnum.none,
                        delivered_at=checked_at if rule.notification_channel == NotificationChannelEnum.none else None,
                    )
                )
                logger.info("Preisalarm ausgeloest", extra={"event": "alert_triggered"})
                events_created += 1
        await session.commit()
        return {
            "checked_rules": len(rules),
            "events_created": events_created,
            "checked_at": checked_at,
        }

    async def _recent_duplicate_exists(self, session: AsyncSession, rule_id, station_id) -> bool:
        threshold = datetime.now(UTC) - timedelta(minutes=30)
        result = await session.execute(
            select(AlertEvent).where(
                AlertEvent.alert_rule_id == rule_id,
                AlertEvent.station_id == station_id,
                AlertEvent.triggered_at >= threshold,
            )
        )
        return result.scalars().first() is not None

