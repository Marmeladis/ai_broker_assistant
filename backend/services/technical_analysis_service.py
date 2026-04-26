from __future__ import annotations

from typing import Any


class TechnicalAnalysisService:

    def analyze(self, candles: list[dict[str, Any]]) -> dict[str, Any]:
        if not candles or len(candles) < 5:
            return {}

        closes = [c["close"] for c in candles if c.get("close") is not None]
        highs = [c["high"] for c in candles if c.get("high") is not None]
        lows = [c["low"] for c in candles if c.get("low") is not None]

        if len(closes) < 5:
            return {}

        last_price = closes[-1]
        sma_5 = self._sma(closes, 5)
        sma_10 = self._sma(closes, 10)
        rsi_14 = self._rsi(closes, 14)
        support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)

        trend = self._detect_trend(last_price, sma_5, sma_10)
        signal = self._detect_signal(last_price, sma_5, sma_10, rsi_14)

        return {
            "last_price": last_price,
            "sma_5": sma_5,
            "sma_10": sma_10,
            "rsi_14": rsi_14,
            "support": support,
            "resistance": resistance,
            "trend": trend,
            "signal": signal,
            "candles_count": len(candles),
            "last_candle_time": candles[-1].get("begin"),
        }

    def _sma(self, values: list[float], period: int) -> float | None:
        if len(values) < period:
            return None
        chunk = values[-period:]
        return sum(chunk) / len(chunk)

    def _rsi(self, closes: list[float], period: int = 14) -> float | None:
        if len(closes) <= period:
            return None

        gains = []
        losses = []

        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))

        if len(gains) < period:
            return None

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _detect_trend(self, last_price, sma_5, sma_10) -> str:
        if sma_5 is None or sma_10 is None:
            return "neutral"

        if last_price > sma_5 > sma_10:
            return "uptrend"
        if last_price < sma_5 < sma_10:
            return "downtrend"
        return "sideways"

    def _detect_signal(self, last_price, sma_5, sma_10, rsi_14) -> str:
        if sma_5 is None or sma_10 is None:
            return "neutral"

        if rsi_14 is not None and rsi_14 < 30:
            return "bullish"
        if rsi_14 is not None and rsi_14 > 70:
            return "bearish"

        if last_price > sma_5 and sma_5 > sma_10:
            return "bullish"
        if last_price < sma_5 and sma_5 < sma_10:
            return "bearish"

        return "neutral"