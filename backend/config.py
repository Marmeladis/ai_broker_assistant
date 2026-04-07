import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Broker Assistant Backend")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_SUPER_SECRET_KEY_123456789")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    DEFAULT_HISTORY_LIMIT: int = int(os.getenv("DEFAULT_HISTORY_LIMIT", "10"))

    MOEX_ISS_BASE_URL: str = os.getenv("MOEX_ISS_BASE_URL", "https://iss.moex.com/iss")
    MOEX_SHARES_ENGINE: str = os.getenv("MOEX_SHARES_ENGINE", "stock")
    MOEX_SHARES_MARKET: str = os.getenv("MOEX_SHARES_MARKET", "shares")
    MOEX_DEFAULT_BOARD: str = os.getenv("MOEX_DEFAULT_BOARD", "TQBR")
    MARKET_HTTP_TIMEOUT_SECONDS: int = int(os.getenv("MARKET_HTTP_TIMEOUT_SECONDS", "20"))

    NEWS_HTTP_TIMEOUT_SECONDS: int = int(os.getenv("NEWS_HTTP_TIMEOUT_SECONDS", "20"))
    NEWS_MAX_ITEMS_PER_SOURCE: int = int(os.getenv("NEWS_MAX_ITEMS_PER_SOURCE", "10"))
    NEWS_RSS_URLS: list[str] = [
        x.strip()
        for x in os.getenv(
            "NEWS_RSS_URLS",
            "https://rss.interfax.ru/interfax-rss.xml"
        ).split(",")
        if x.strip()
    ]

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gigachat").strip().lower()
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    GIGACHAT_AUTH_KEY: str = os.getenv("GIGACHAT_AUTH_KEY", "")
    GIGACHAT_SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    GIGACHAT_AUTH_URL: str = os.getenv(
        "GIGACHAT_AUTH_URL",
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    ).rstrip("/")
    GIGACHAT_BASE_URL: str = os.getenv(
        "GIGACHAT_BASE_URL",
        "https://gigachat.devices.sberbank.ru/api/v1"
    ).rstrip("/")
    GIGACHAT_MODEL: str = os.getenv("GIGACHAT_MODEL", "GigaChat")
    GIGACHAT_TIMEOUT_SECONDS: int = int(os.getenv("GIGACHAT_TIMEOUT_SECONDS", "60"))
    GIGACHAT_VERIFY_SSL: bool = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() == "true"
settings = Settings()

print("LLM_PROVIDER =", settings.LLM_PROVIDER)
print("GIGACHAT_AUTH_KEY_SET =", bool(settings.GIGACHAT_AUTH_KEY))
print("GIGACHAT_SCOPE =", settings.GIGACHAT_SCOPE)
print("GIGACHAT_AUTH_URL =", settings.GIGACHAT_AUTH_URL)
print("GIGACHAT_BASE_URL =", settings.GIGACHAT_BASE_URL)
print("GIGACHAT_MODEL =", settings.GIGACHAT_MODEL)