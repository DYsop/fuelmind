from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.routes_alerts import router as alerts_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_favorites import router as favorites_router
from app.api.routes_health import router as health_router
from app.api.routes_locations import router as locations_router
from app.api.routes_prediction import router as prediction_router
from app.api.routes_prices import router as prices_router
from app.api.routes_settings import router as settings_router
from app.api.routes_stations import router as stations_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import init_db
from app.scheduler.scheduler import build_scheduler
from app.services.alert_service import AlertService
from app.services.analytics_service import AnalyticsService
from app.services.geocoding_service import (
    GeocodingService,
    GeocodingUnavailableError,
    GeocodingValidationError,
)
from app.services.prediction_service import PredictionService
from app.services.price_service import PriceService
from app.services.station_service import StationService
from app.services.tankerkoenig_client import (
    TankerkoenigClient,
    TankerkoenigConfigurationError,
    TankerkoenigRateLimitError,
    TankerkoenigUnavailableError,
    TankerkoenigValidationError,
)


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    redis_client: Redis | None = None
    try:
        redis_client = Redis.from_url(settings.resolved_redis_url, encoding="utf-8", decode_responses=True)
        await redis_client.ping()
        logger.info("Redis Verbindung hergestellt", extra={"event": "redis_connected"})
    except Exception:
        redis_client = None
        logger.warning("Redis nicht erreichbar, FuelMind laeuft ohne zentralen Cache.")

    tanker_client = TankerkoenigClient(settings, redis_client)
    geocoding_service = GeocodingService(settings, redis_client)
    station_service = StationService(tanker_client)
    price_service = PriceService(tanker_client, station_service)
    alert_service = AlertService(station_service)
    analytics_service = AnalyticsService(station_service)
    prediction_service = PredictionService(price_service, analytics_service, station_service)

    app.state.redis = redis_client
    app.state.tanker_client = tanker_client
    app.state.geocoding_service = geocoding_service
    app.state.station_service = station_service
    app.state.price_service = price_service
    app.state.alert_service = alert_service
    app.state.analytics_service = analytics_service
    app.state.prediction_service = prediction_service
    app.state.scheduler = None

    logger.info("Initialisiere Datenbank", extra={"event": "db_init"})
    await init_db()

    if settings.enable_scheduler:
        scheduler = build_scheduler(app)
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("Scheduler gestartet", extra={"event": "scheduler_started"})

    logger.info("FuelMind Backend gestartet", extra={"event": "app_started"})
    try:
        yield
    finally:
        if app.state.scheduler:
            app.state.scheduler.shutdown(wait=False)
        await tanker_client.close()
        await geocoding_service.close()
        if redis_client:
            await redis_client.aclose()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.exception_handler(TankerkoenigConfigurationError)
    async def tanker_config_handler(_: Request, exc: TankerkoenigConfigurationError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(TankerkoenigRateLimitError)
    async def tanker_rate_limit_handler(_: Request, exc: TankerkoenigRateLimitError):
        return JSONResponse(status_code=429, content={"detail": str(exc)})

    @app.exception_handler(TankerkoenigValidationError)
    async def tanker_validation_handler(_: Request, exc: TankerkoenigValidationError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(TankerkoenigUnavailableError)
    async def tanker_unavailable_handler(_: Request, exc: TankerkoenigUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(GeocodingValidationError)
    async def geocoding_validation_handler(_: Request, exc: GeocodingValidationError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(GeocodingUnavailableError)
    async def geocoding_unavailable_handler(_: Request, exc: GeocodingUnavailableError):
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception):
        logger.exception("Unerwarteter Fehler im Backend", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Interner Serverfehler."})

    app.include_router(health_router, prefix="/api")
    app.include_router(stations_router, prefix="/api")
    app.include_router(prices_router, prefix="/api")
    app.include_router(favorites_router, prefix="/api")
    app.include_router(alerts_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")
    app.include_router(prediction_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(locations_router, prefix="/api")
    return app


app = create_app()
