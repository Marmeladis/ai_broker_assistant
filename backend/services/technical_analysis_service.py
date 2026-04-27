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
        macd, macd_signal, macd_histogram = self._macd(closes)
        support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
        resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)

        trend = self._detect_trend(last_price, sma_5, sma_10)
        signal = self._detect_signal(last_price, sma_5, sma_10, rsi_14, macd, macd_signal)
        signal_strength = self._detect_signal_strength(trend, signal, rsi_14, macd, macd_signal)

        return {
            "last_price": last_price,
            "sma_5": sma_5,
            "sma_10": sma_10,
            "rsi_14": rsi_14,
            "macd": macd,
            "macd_signal": macd_signal,
            "macd_histogram": macd_histogram,
            "support": support,
            "resistance": resistance,
            "support_distance_percent": self._distance_percent(last_price, support),
            "resistance_distance_percent": self._distance_percent(last_price, resistance),
            "trend": trend,
            "signal": signal,
            "signal_strength": signal_strength,
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

    def _ema_series(self, values: list[float], period: int) -> list[float]:
        if not values:
            return []
        multiplier = 2 / (period + 1)
        ema_values = [values[0]]
        for value in values[1:]:
            ema_values.append((value - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values

    def _macd(self, closes: list[float]) -> tuple[float | None, float | None, float | None]:
        if len(closes) < 35:
            return None, None, None
        ema_12 = self._ema_series(closes, 12)
        ema_26 = self._ema_series(closes, 26)
        macd_line = [fast - slow for fast, slow in zip(ema_12, ema_26)]
        signal_line = self._ema_series(macd_line, 9)
        macd = macd_line[-1]
        macd_signal = signal_line[-1]
        return macd, macd_signal, macd - macd_signal

    def _distance_percent(self, price: float | None, level: float | None) -> float | None:
        if price is None or level is None or price == 0:
            return None
        return ((price - level) / price) * 100

    def _detect_trend(self, last_price, sma_5, sma_10) -> str:
        if sma_5 is None or sma_10 is None:
            return "neutral"
        if last_price > sma_5 > sma_10:
            return "uptrend"
        if last_price < sma_5 < sma_10:
            return "downtrend"
        return "sideways"

    def _detect_signal(self, last_price, sma_5, sma_10, rsi_14, macd=None, macd_signal=None) -> str:
        bullish = 0
        bearish = 0

        if sma_5 is not None and sma_10 is not None:
            if last_price > sma_5 > sma_10:
                bullish += 1
            elif last_price < sma_5 < sma_10:
                bearish += 1

        if rsi_14 is not None:
            if rsi_14 < 30:
                bullish += 1
            elif rsi_14 > 70:
                bearish += 1

        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                bullish += 1
            elif macd < macd_signal:
                bearish += 1

        if bullish > bearish:
            return "bullish"
        if bearish > bullish:
            return "bearish"
        return "neutral"

    def _detect_signal_strength(self, trend, signal, rsi_14, macd, macd_signal) -> str:
        score = 0
        if trend == "uptrend":
            score += 1
        elif trend == "downtrend":
            score -= 1
        if signal == "bullish":
            score += 1
        elif signal == "bearish":
            score -= 1
        if rsi_14 is not None:
            if 45 <= rsi_14 <= 60:
                score += 1
            elif rsi_14 > 70:
                score -= 1
            elif rsi_14 < 30:
                score += 1
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 1
            elif macd < macd_signal:
                score -= 1
        if score >= 3:
            return "strong_bullish"
        if score == 2:
            return "moderate_bullish"
        if score <= -3:
            return "strong_bearish"
        if score == -2:
            return "moderate_bearish"
        return "mixed"
