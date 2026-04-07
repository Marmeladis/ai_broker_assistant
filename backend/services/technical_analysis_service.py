class TechnicalAnalysisService:
    def calculate_sma(self, prices: list[float], window: int) -> float | None:
        if len(prices) < window:
            return None
        return sum(prices[-window:]) / window

    def calculate_ema_series(self, prices: list[float], window: int) -> list[float]:
        if not prices:
            return []

        multiplier = 2 / (window + 1)
        ema_values = [prices[0]]

        for price in prices[1:]:
            ema = (price - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)

        return ema_values

    def calculate_rsi(self, prices: list[float], window: int = 14) -> float | None:
        if len(prices) < window + 1:
            return None

        gains = []
        losses = []

        for i in range(1, len(prices)):
            delta = prices[i] - prices[i - 1]
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(delta))

        avg_gain = sum(gains[-window:]) / window
        avg_loss = sum(losses[-window:]) / window

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: list[float]) -> dict | None:
        if len(prices) < 26:
            return None

        ema_12 = self.calculate_ema_series(prices, 12)
        ema_26 = self.calculate_ema_series(prices, 26)

        macd_line = []
        min_len = min(len(ema_12), len(ema_26))
        for i in range(min_len):
            macd_line.append(ema_12[i] - ema_26[i])

        if len(macd_line) < 9:
            return None

        signal_line = self.calculate_ema_series(macd_line, 9)
        histogram = macd_line[-1] - signal_line[-1]

        return {
            "macd": macd_line[-1],
            "signal": signal_line[-1],
            "histogram": histogram
        }

    def detect_trend(self, prices: list[float]) -> str:
        if len(prices) < 5:
            return "unknown"

        if prices[-1] > prices[-5]:
            return "uptrend"
        if prices[-1] < prices[-5]:
            return "downtrend"
        return "sideways"

    def detect_simple_pattern(self, prices: list[float]) -> str | None:
        if len(prices) < 3:
            return None

        if prices[-3] < prices[-2] < prices[-1]:
            return "momentum_up"

        if prices[-3] > prices[-2] > prices[-1]:
            return "momentum_down"

        return None

    def detect_support_resistance(self, candles: list[dict]) -> dict:
        if not candles:
            return {"support": None, "resistance": None}

        lows = [float(c["low"]) for c in candles if c.get("low") is not None]
        highs = [float(c["high"]) for c in candles if c.get("high") is not None]

        if not lows or not highs:
            return {"support": None, "resistance": None}

        recent_lows = lows[-10:] if len(lows) >= 10 else lows
        recent_highs = highs[-10:] if len(highs) >= 10 else highs

        return {
            "support": min(recent_lows),
            "resistance": max(recent_highs)
        }

    def detect_signal(
        self,
        sma_5: float | None,
        sma_10: float | None,
        rsi: float | None,
        macd_data: dict | None
    ) -> str:
        bullish_score = 0
        bearish_score = 0

        if sma_5 is not None and sma_10 is not None:
            if sma_5 > sma_10:
                bullish_score += 1
            elif sma_5 < sma_10:
                bearish_score += 1

        if rsi is not None:
            if rsi < 30:
                bullish_score += 1
            elif rsi > 70:
                bearish_score += 1

        if macd_data:
            macd = macd_data.get("macd")
            signal = macd_data.get("signal")
            if macd is not None and signal is not None:
                if macd > signal:
                    bullish_score += 1
                elif macd < signal:
                    bearish_score += 1

        if bullish_score > bearish_score:
            return "bullish"
        if bearish_score > bullish_score:
            return "bearish"
        return "neutral"

    def analyze(self, candles: list[dict]) -> dict:
        if not candles:
            return {}

        closes = [float(c["close"]) for c in candles if c.get("close") is not None]

        if not closes:
            return {}

        sma_5 = self.calculate_sma(closes, 5)
        sma_10 = self.calculate_sma(closes, 10)
        trend = self.detect_trend(closes)
        pattern = self.detect_simple_pattern(closes)
        rsi_14 = self.calculate_rsi(closes, 14)
        macd_data = self.calculate_macd(closes)
        support_resistance = self.detect_support_resistance(candles)

        signal = self.detect_signal(
            sma_5=sma_5,
            sma_10=sma_10,
            rsi=rsi_14,
            macd_data=macd_data
        )

        return {
            "trend": trend,
            "pattern": pattern,
            "sma_5": sma_5,
            "sma_10": sma_10,
            "rsi_14": rsi_14,
            "macd": macd_data["macd"] if macd_data else None,
            "macd_signal": macd_data["signal"] if macd_data else None,
            "macd_histogram": macd_data["histogram"] if macd_data else None,
            "support": support_resistance.get("support"),
            "resistance": support_resistance.get("resistance"),
            "signal": signal,
            "last_price": closes[-1]
        }