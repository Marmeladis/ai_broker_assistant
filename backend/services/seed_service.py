from sqlalchemy.orm import Session

from backend.models import FinancialInstrument, ExternalSource, InstrumentAlias


class SeedService:
    def seed_initial_data(self, db: Session) -> None:
        instruments = [
            {"ticker": "SBER", "name": "Сбербанк", "type": "stock", "currency": "RUB"},
            {"ticker": "GAZP", "name": "Газпром", "type": "stock", "currency": "RUB"},
            {"ticker": "LKOH", "name": "Лукойл", "type": "stock", "currency": "RUB"},
            {"ticker": "VTBR", "name": "ВТБ", "type": "stock", "currency": "RUB"},
            {"ticker": "YDEX", "name": "Яндекс", "type": "stock", "currency": "RUB"},
            {"ticker": "MOEX", "name": "Московская биржа", "type": "stock", "currency": "RUB"},
        ]

        for item in instruments:
            exists = db.query(FinancialInstrument).filter(
                FinancialInstrument.ticker == item["ticker"]
            ).first()
            if not exists:
                db.add(FinancialInstrument(**item))

        source_exists = db.query(ExternalSource).filter(
            ExternalSource.name == "manual"
        ).first()
        if not source_exists:
            db.add(ExternalSource(
                name="manual",
                endpoint_url=None,
                is_active=True
            ))

        db.commit()

        aliases = [
            ("SBER", "сбер"),
            ("SBER", "сбербанк"),
            ("SBER", "обычка сбера"),
            ("GAZP", "газпром"),
            ("LKOH", "лукойл"),
            ("VTBR", "втб"),
            ("YDEX", "яндекс"),
            ("MOEX", "мосбиржа"),
            ("MOEX", "московская биржа"),
        ]

        for ticker, alias in aliases:
            exists = db.query(InstrumentAlias).filter(
                InstrumentAlias.ticker == ticker,
                InstrumentAlias.alias == alias
            ).first()
            if not exists:
                db.add(InstrumentAlias(
                    ticker=ticker,
                    alias=alias
                ))

        db.commit()