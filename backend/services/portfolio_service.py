from sqlalchemy.orm import Session

from backend.models import PortfolioPosition, User, FinancialInstrument
from backend.services.market_service import MarketService


class PortfolioService:
    def __init__(self):
        self.market_service = MarketService()

    def get_user_positions(self, db: Session, user: User) -> list[PortfolioPosition]:
        return (
            db.query(PortfolioPosition)
            .filter(PortfolioPosition.user_id == user.id)
            .all()
        )

    def add_position(
        self,
        db: Session,
        user: User,
        ticker: str,
        quantity,
        avg_price
    ) -> PortfolioPosition:
        ticker = ticker.upper()

        instrument = db.query(FinancialInstrument).filter(
            FinancialInstrument.ticker == ticker
        ).first()

        if not instrument:
            instrument = FinancialInstrument(
                ticker=ticker,
                name=ticker,
                type="stock",
                currency="RUB"
            )
            db.add(instrument)
            db.commit()
            db.refresh(instrument)

        position = PortfolioPosition(
            user_id=user.id,
            ticker=ticker,
            quantity=quantity,
            avg_price=avg_price
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        return position

    def build_portfolio_summary(self, db: Session, user: User) -> list[dict]:
        positions = self.get_user_positions(db, user)
        result = []

        for p in positions:
            result.append({
                "ticker": p.ticker,
                "quantity": float(p.quantity),
                "avg_price": float(p.avg_price)
            })

        return result

    def get_position_by_ticker(self, db: Session, user: User, ticker: str) -> PortfolioPosition | None:
        return (
            db.query(PortfolioPosition)
            .filter(
                PortfolioPosition.user_id == user.id,
                PortfolioPosition.ticker == ticker.upper()
            )
            .first()
        )

    def build_position_context(self, db: Session, user: User, ticker: str) -> dict | None:
        position = self.get_position_by_ticker(db, user, ticker)
        if not position:
            return None

        return {
            "ticker": position.ticker,
            "quantity": float(position.quantity),
            "avg_price": float(position.avg_price)
        }

    def refresh_portfolio_market_data(self, db: Session, user: User) -> dict:
        positions = self.get_user_positions(db, user)

        refreshed = []
        failed = []

        for position in positions:
            ticker = position.ticker.upper()
            try:
                market_entry = self.market_service.refresh_latest_price_from_provider(db, ticker)
                if market_entry:
                    refreshed.append({
                        "ticker": ticker,
                        "price": float(market_entry.price),
                        "recorded_at": market_entry.recorded_at.isoformat(),
                        "source_name": market_entry.source_name
                    })
                else:
                    failed.append({
                        "ticker": ticker,
                        "reason": "Цена не получена от провайдера"
                    })
            except Exception as e:
                failed.append({
                    "ticker": ticker,
                    "reason": str(e)
                })

        return {
            "refreshed_count": len(refreshed),
            "failed_count": len(failed),
            "refreshed": refreshed,
            "failed": failed
        }

    def build_portfolio_metrics(self, db: Session, user: User) -> dict:
        positions = self.get_user_positions(db, user)

        total_invested_value = 0.0
        total_market_value = 0.0
        total_absolute_pnl = 0.0

        items = []

        for position in positions:
            quantity = float(position.quantity)
            avg_price = float(position.avg_price)
            invested_value = quantity * avg_price

            total_invested_value += invested_value

            latest_market = self.market_service.get_latest_price_prefer_provider(db, position.ticker)

            current_price = None
            market_value = None
            absolute_pnl = None
            pnl_percent = None
            has_market_price = False

            if latest_market:
                has_market_price = True
                current_price = float(latest_market.price)
                market_value = current_price * quantity
                absolute_pnl = market_value - invested_value
                total_market_value += market_value
                total_absolute_pnl += absolute_pnl

                if invested_value != 0:
                    pnl_percent = (absolute_pnl / invested_value) * 100

            item = {
                "ticker": position.ticker,
                "quantity": quantity,
                "avg_price": avg_price,
                "invested_value": round(invested_value, 4),
                "has_market_price": has_market_price,
                "current_price": round(current_price, 4) if current_price is not None else None,
                "market_value": round(market_value, 4) if market_value is not None else None,
                "absolute_pnl": round(absolute_pnl, 4) if absolute_pnl is not None else None,
                "pnl_percent": round(pnl_percent, 4) if pnl_percent is not None else None,
            }
            items.append(item)

        total_pnl_percent = None
        if total_invested_value != 0 and total_market_value != 0:
            total_pnl_percent = (total_absolute_pnl / total_invested_value) * 100

        profitable_positions = sum(
            1 for item in items
            if item["absolute_pnl"] is not None and item["absolute_pnl"] > 0
        )
        losing_positions = sum(
            1 for item in items
            if item["absolute_pnl"] is not None and item["absolute_pnl"] < 0
        )
        unknown_positions = sum(
            1 for item in items
            if item["has_market_price"] is False
        )

        return {
            "positions_count": len(items),
            "total_invested_value": round(total_invested_value, 4),
            "total_market_value": round(total_market_value, 4) if total_market_value != 0 else None,
            "total_absolute_pnl": round(total_absolute_pnl, 4) if total_market_value != 0 else None,
            "total_pnl_percent": round(total_pnl_percent, 4) if total_pnl_percent is not None else None,
            "profitable_positions": profitable_positions,
            "losing_positions": losing_positions,
            "unknown_positions": unknown_positions,
            "items": items
        }

    def build_portfolio_text_summary(self, portfolio_metrics: dict) -> str:
        positions_count = portfolio_metrics.get("positions_count", 0)

        if positions_count == 0:
            return "Портфель пользователя пуст."

        profitable = portfolio_metrics.get("profitable_positions", 0)
        losing = portfolio_metrics.get("losing_positions", 0)
        unknown = portfolio_metrics.get("unknown_positions", 0)
        invested = portfolio_metrics.get("total_invested_value")
        market_value = portfolio_metrics.get("total_market_value")
        total_pnl = portfolio_metrics.get("total_absolute_pnl")
        total_pnl_percent = portfolio_metrics.get("total_pnl_percent")

        parts = [f"В портфеле {positions_count} позиций."]

        if invested is not None:
            parts.append(f"Суммарно вложено: {invested}.")

        if market_value is not None:
            parts.append(f"Текущая рыночная стоимость: {market_value}.")

        if total_pnl is not None:
            pnl_text = f"{total_pnl}"
            if total_pnl_percent is not None:
                pnl_text += f" ({total_pnl_percent}%)"
            parts.append(f"Совокупный P&L: {pnl_text}.")

        parts.append(
            f"Позиции в плюсе: {profitable}, в минусе: {losing}, без актуальной цены: {unknown}."
        )

        return " ".join(parts)