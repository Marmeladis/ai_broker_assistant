from datetime import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base



from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Boolean,
    Integer, Text, Numeric
)
from sqlalchemy.orm import relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="client")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chat = relationship(
        "Chat",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    portfolio_positions = relationship(
        "PortfolioPosition",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    request_history = relationship(
        "RequestHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, default="Личный чат")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chat = relationship("Chat", back_populates="messages")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    access_token = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="sessions")


class FinancialInstrument(Base):
    __tablename__ = "financial_instruments"

    ticker = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    currency = Column(String, nullable=False)

    market_data = relationship("MarketData", back_populates="instrument")
    portfolio_positions = relationship("PortfolioPosition", back_populates="instrument")
    news_items = relationship("NewsItem", back_populates="instrument")


class ExternalSource(Base):
    __tablename__ = "external_sources"

    name = Column(String, primary_key=True)
    endpoint_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    market_data = relationship("MarketData", back_populates="source")
    news_items = relationship("NewsItem", back_populates="source")


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("financial_instruments.ticker"), nullable=False, index=True)
    source_name = Column(String, ForeignKey("external_sources.name"), nullable=False, index=True)

    price = Column(Numeric(18, 4), nullable=False)
    volume = Column(Numeric(18, 4), nullable=True)

    recorded_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    instrument = relationship("FinancialInstrument", back_populates="market_data")
    source = relationship("ExternalSource", back_populates="market_data")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String, ForeignKey("financial_instruments.ticker"), nullable=False, index=True)

    quantity = Column(Numeric(18, 4), nullable=False)
    avg_price = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="portfolio_positions")
    instrument = relationship("FinancialInstrument", back_populates="portfolio_positions")


class RequestHistory(Base):
    __tablename__ = "request_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)

    user_query = Column(Text, nullable=False)
    system_response = Column(Text, nullable=True)
    intent_type = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="request_history")


class NewsItem(Base):
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("financial_instruments.ticker"), nullable=False, index=True)
    source_name = Column(String, ForeignKey("external_sources.name"), nullable=False, index=True)

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    instrument = relationship("FinancialInstrument", back_populates="news_items")
    source = relationship("ExternalSource", back_populates="news_items")

class AnalyticalReport(Base):
    __tablename__ = "analytical_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    intent_type = Column(String, nullable=False)

    report_type = Column(String, nullable=False)
    trend_summary = Column(Text, nullable=True)
    calculated_indicators = Column(Text, nullable=True)  # JSON string
    confidence_score = Column(Numeric(8, 4), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class InstrumentAlias(Base):
    __tablename__ = "instrument_aliases"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("financial_instruments.ticker"), nullable=False, index=True)
    alias = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ChatSessionState(Base):
    __tablename__ = "chat_session_states"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), unique=True, nullable=False, index=True)

    last_ticker = Column(String, nullable=True)
    recent_tickers_json = Column(Text, nullable=True)
    last_intent = Column(String, nullable=True)
    last_resolved_instrument_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    chat = relationship("Chat", backref="session_state")