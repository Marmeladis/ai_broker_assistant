from fastapi import FastAPI

from backend.config import settings
from backend.database import Base, engine, SessionLocal
from backend.routers.auth_router import router as auth_router
from backend.routers.chat_router import router as chat_router
from backend.routers.portfolio_router import router as portfolio_router
from backend.routers.market_router import router as market_router
from backend.routers.request_history_router import router as request_history_router
from backend.routers.news_router import router as news_router
from backend.routers.llm_router import router as llm_router
from backend.routers.analytical_report_router import router as analytical_report_router
from backend.services.seed_service import SeedService
from backend.routers.chart_router import router as chart_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(portfolio_router)
app.include_router(market_router)
app.include_router(request_history_router)
app.include_router(news_router)
app.include_router(llm_router)
app.include_router(analytical_report_router)
app.include_router(chart_router)

@app.on_event("startup")
def startup_seed():
    db = SessionLocal()
    try:
        SeedService().seed_initial_data(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "Broker Assistant API is running"}