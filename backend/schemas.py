from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    login: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    login: str
    password: str


class UserResponse(BaseModel):
    id: int
    login: str
    role: str
    created_at: datetime
    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    id: str
    user_id: int
    is_active: bool
    created_at: datetime
    expires_at: datetime
    model_config = {"from_attributes": True}


class AuthWithSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    session: SessionResponse


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatWithMessagesResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    messages: list[MessageResponse]
    model_config = {"from_attributes": True}


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    intent: str
    analytics: dict | None = None


class PortfolioPositionCreate(BaseModel):
    ticker: str
    quantity: Decimal
    avg_price: Decimal


class PortfolioPositionResponse(BaseModel):
    id: int
    user_id: int
    ticker: str
    quantity: Decimal
    avg_price: Decimal
    created_at: datetime
    model_config = {"from_attributes": True}


class InstrumentCreate(BaseModel):
    ticker: str
    name: str
    type: str
    currency: str


class MarketDataCreate(BaseModel):
    ticker: str
    source_name: str
    price: Decimal
    volume: Decimal | None = None
    recorded_at: datetime


class MarketDataResponse(BaseModel):
    id: int
    ticker: str
    source_name: str
    price: Decimal
    volume: Decimal | None = None
    recorded_at: datetime
    fetched_at: datetime
    model_config = {"from_attributes": True}


class RequestHistoryResponse(BaseModel):
    id: str
    user_id: int
    message_id: int | None = None
    user_query: str
    system_response: str | None = None
    intent_type: str
    timestamp: datetime
    model_config = {"from_attributes": True}


class NewsCreate(BaseModel):
    ticker: str
    source_name: str
    title: str
    content: str
    published_at: datetime


class NewsResponse(BaseModel):
    id: int
    ticker: str
    source_name: str
    title: str
    content: str
    published_at: datetime
    fetched_at: datetime
    model_config = {"from_attributes": True}

class AnalyticalReportResponse(BaseModel):
    id: str
    user_id: int
    message_id: int | None = None
    intent_type: str
    report_type: str
    trend_summary: str | None = None
    calculated_indicators: str | None = None
    confidence_score: Decimal | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class ResolvedInstrumentResponse(BaseModel):
    ticker: str
    name: str
    type: str | None = None
    currency: str | None = None


class ChatMessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


class ChatProcessResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    intent: str
    resolved_instrument: ResolvedInstrumentResponse | None = None
    history_id: str | None = None
    analytical_report_id: str | None = None