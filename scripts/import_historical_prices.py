from __future__ import annotations

import argparse
import asyncio
import csv
import logging
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.db.models import FuelTypeEnum, PriceSnapshot, Station
from app.db.session import SessionLocal


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("fuelmind.importer")


@dataclass
class HistoricalRow:
    external_station_id: str
    fuel_type: FuelTypeEnum
    price: Decimal
    observed_at: datetime
    is_open: bool
    source: str


class HistoricalPriceImporter:
    REQUIRED_VARIANTS = [
        {"station_id", "fuel_type", "price", "observed_at"},
        {"external_station_id", "fuel_type", "price", "timestamp"},
    ]

    def __init__(self, csv_path: Path, batch_size: int = 500, dry_run: bool = False) -> None:
        self.csv_path = csv_path
        self.batch_size = batch_size
        self.dry_run = dry_run

    def detect_format(self, columns: list[str]) -> str:
        normalized = {column.strip().lower() for column in columns}
        for required in self.REQUIRED_VARIANTS:
            if required.issubset(normalized):
                return "generic_station_prices"
        raise ValueError(
            "CSV-Format unbekannt. Bitte Adapter-Regeln in HistoricalPriceImporter.detect_format() anpassen."
        )

    def validate_columns(self, columns: list[str]) -> None:
        self.detect_format(columns)

    def parse_row(self, row: dict[str, str]) -> HistoricalRow:
        station_id = row.get("station_id") or row.get("external_station_id")
        timestamp = row.get("observed_at") or row.get("timestamp")
        if not station_id or not timestamp:
            raise ValueError("Pflichtfelder station_id/external_station_id oder observed_at/timestamp fehlen.")

        observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).astimezone(UTC)
        fuel_type = FuelTypeEnum(row["fuel_type"].lower())
        price = Decimal(row["price"].replace(",", "."))
        is_open = str(row.get("is_open", "true")).lower() not in {"false", "0", "closed"}
        source = row.get("source", "historical_csv")
        return HistoricalRow(
            external_station_id=station_id,
            fuel_type=fuel_type,
            price=price,
            observed_at=observed_at,
            is_open=is_open,
            source=source,
        )

    async def insert_batch(self, rows: Iterable[HistoricalRow]) -> tuple[int, int]:
        imported = 0
        skipped = 0
        async with SessionLocal() as session:
            for row in rows:
                station_query = await session.execute(
                    select(Station).where(Station.external_station_id == row.external_station_id)
                )
                station = station_query.scalar_one_or_none()
                if station is None:
                    skipped += 1
                    continue

                duplicate_query = await session.execute(
                    select(PriceSnapshot).where(
                        PriceSnapshot.station_id == station.id,
                        PriceSnapshot.fuel_type == row.fuel_type,
                        PriceSnapshot.observed_at == row.observed_at,
                    )
                )
                if duplicate_query.scalar_one_or_none():
                    skipped += 1
                    continue

                session.add(
                    PriceSnapshot(
                        station_id=station.id,
                        fuel_type=row.fuel_type,
                        price=row.price,
                        is_open=row.is_open,
                        observed_at=row.observed_at,
                        source=row.source,
                    )
                )
                imported += 1

            if self.dry_run:
                await session.rollback()
            else:
                await session.commit()
        return imported, skipped

    async def run(self) -> None:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV-Datei nicht gefunden: {self.csv_path}")

        imported_total = 0
        skipped_total = 0
        parsed_batch: list[HistoricalRow] = []

        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV-Datei enthaelt keine Kopfzeile.")
            self.validate_columns(reader.fieldnames)

            for index, row in enumerate(reader, start=1):
                parsed_batch.append(self.parse_row(row))
                if len(parsed_batch) >= self.batch_size:
                    imported, skipped = await self.insert_batch(parsed_batch)
                    imported_total += imported
                    skipped_total += skipped
                    logger.info("Batch verarbeitet: %s importiert, %s uebersprungen", imported, skipped)
                    parsed_batch.clear()
                if index % 1000 == 0:
                    logger.info("Fortschritt: %s Zeilen gelesen", index)

        if parsed_batch:
            imported, skipped = await self.insert_batch(parsed_batch)
            imported_total += imported
            skipped_total += skipped

        logger.info(
            "Import abgeschlossen. Importiert: %s, uebersprungen: %s, Dry-Run: %s",
            imported_total,
            skipped_total,
            self.dry_run,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FuelMind CSV-Importer fuer historische Preisdaten")
    parser.add_argument("csv_path", type=Path, help="Pfad zur CSV-Datei")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch-Groesse fuer Inserts")
    parser.add_argument("--dry-run", action="store_true", help="Import nur pruefen, nicht committen")
    return parser


async def async_main() -> None:
    get_settings()
    args = build_parser().parse_args()
    importer = HistoricalPriceImporter(args.csv_path, batch_size=args.batch_size, dry_run=args.dry_run)
    await importer.run()


if __name__ == "__main__":
    asyncio.run(async_main())
