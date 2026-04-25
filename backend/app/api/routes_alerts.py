from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_internal_token
from app.db.session import get_db_session
from app.schemas.alert_schema import AlertRuleCreate, AlertRuleUpdate


router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(verify_internal_token)])


@router.get("")
async def list_alerts(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    rules = await request.app.state.alert_service.list_rules(session)
    events = await request.app.state.alert_service.list_events(session)
    return {
        "rules": [
            {
                "id": rule.id,
                "name": rule.name,
                "fuel_type": rule.fuel_type.value,
                "max_price": float(rule.max_price),
                "lat": float(rule.lat),
                "lng": float(rule.lng),
                "radius_km": float(rule.radius_km),
                "enabled": rule.enabled,
                "notification_channel": rule.notification_channel.value,
                "created_at": rule.created_at,
                "updated_at": rule.updated_at,
            }
            for rule in rules
        ],
        "events": events,
    }


@router.post("")
async def create_alert(
    payload: AlertRuleCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    rule = await request.app.state.alert_service.create_rule(session, payload.model_dump())
    return {
        "id": rule.id,
        "name": rule.name,
        "fuel_type": rule.fuel_type.value,
        "max_price": float(rule.max_price),
        "lat": float(rule.lat),
        "lng": float(rule.lng),
        "radius_km": float(rule.radius_km),
        "enabled": rule.enabled,
        "notification_channel": rule.notification_channel.value,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


@router.put("/{alert_id}")
async def update_alert(
    alert_id: str,
    payload: AlertRuleUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        rule = await request.app.state.alert_service.update_rule(session, alert_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": rule.id,
        "name": rule.name,
        "fuel_type": rule.fuel_type.value,
        "max_price": float(rule.max_price),
        "lat": float(rule.lat),
        "lng": float(rule.lng),
        "radius_km": float(rule.radius_km),
        "enabled": rule.enabled,
        "notification_channel": rule.notification_channel.value,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        await request.app.state.alert_service.delete_rule(session, alert_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True}


@router.post("/check-now")
async def check_alerts_now(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    return await request.app.state.alert_service.check_alerts(session)
