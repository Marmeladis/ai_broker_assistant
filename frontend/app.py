import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go


API_BASE_URL = "http://127.0.0.1:8000"

session = requests.Session()
session.trust_env = False


# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Broker Assistant",
    page_icon="📈",
    layout="wide"
)


# =========================
# Session state
# =========================
DEFAULT_SESSION_STATE = {
    "token": None,
    "user": None,
    "auth_mode": "login",
    "last_resolved_instrument": None,
    "chart_search_query": "",
    "chart_resolved_name": None,
    "chart_ticker": "SBER",
    "chart_interval": "24",
    "chart_limit": 60,
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================
# Sticky styles
# =========================
def inject_sticky_styles():
    st.markdown(
        """
        <style>
        :root {
            --sticky-bg: rgba(255, 255, 255, 0.97);
            --sticky-border: rgba(49, 51, 63, 0.12);
            --sticky-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --sticky-bg: rgba(14, 17, 23, 0.96);
                --sticky-border: rgba(250, 250, 250, 0.10);
                --sticky-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
            }
        }

        .sticky-header {
            position: sticky;
            top: 0;
            z-index: 50;
            background: var(--sticky-bg);
            border-bottom: 1px solid var(--sticky-border);
            box-shadow: var(--sticky-shadow);
            padding: 0.4rem 0 0.75rem 0;
            margin-bottom: 1rem;
        }

        .sticky-side {
            position: sticky;
            top: 1rem;
            z-index: 30;
        }

        .side-card {
            background: var(--sticky-bg);
            border: 1px solid var(--sticky-border);
            border-radius: 14px;
            box-shadow: var(--sticky-shadow);
            padding: 1rem;
        }

        div[data-testid="stChatInput"] {
            position: sticky;
            bottom: 0;
            z-index: 60;
            background: var(--sticky-bg);
            border-top: 1px solid var(--sticky-border);
            padding-top: 0.75rem;
            padding-bottom: 0.35rem;
            margin-top: 1rem;
        }

        div[data-baseweb="tab-list"] {
            position: sticky;
            top: 0;
            z-index: 70;
            background: var(--sticky-bg);
            border-bottom: 1px solid var(--sticky-border);
            padding-top: 0.2rem;
            padding-bottom: 0.15rem;
            margin-bottom: 0.75rem;
        }

        .chat-bottom-spacer {
            height: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# =========================
# API helpers
# =========================
def build_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def get_headers() -> dict:
    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_get(path: str):
    return session.get(
        build_url(path),
        headers=get_headers(),
        timeout=30
    )


def api_post(path: str, json_data=None, params=None):
    return session.post(
        build_url(path),
        headers=get_headers(),
        json=json_data,
        params=params,
        timeout=30
    )


def show_api_error(response):
    try:
        data = response.json()
        detail = data.get("detail")
        if detail:
            st.error(str(detail))
        else:
            st.error(f"HTTP {response.status_code}")
            st.json(data)
    except Exception:
        st.error(f"HTTP {response.status_code}")
        if response.text:
            st.text(response.text)


# =========================
# Auth / user helpers
# =========================
def load_current_user() -> bool:
    try:
        response = api_get("/auth/me")
        if response.status_code == 200:
            st.session_state.user = response.json()
            return True

        st.session_state.token = None
        st.session_state.user = None
        return False

    except requests.RequestException as e:
        st.error(f"Ошибка соединения: {e}")
        st.session_state.token = None
        st.session_state.user = None
        return False


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.last_resolved_instrument = None
    st.rerun()


# =========================
# Data loaders
# =========================
def load_chat():
    try:
        response = api_get("/chat/me")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def load_portfolio():
    try:
        response = api_get("/portfolio/me")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []


def load_history():
    try:
        response = api_get("/history/me")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.RequestException:
        return []


def load_llm_status():
    try:
        response = api_get("/llm/health")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def load_chart_data(ticker: str, interval: str = "24", limit: int = 60):
    try:
        response = api_get(
            f"/charts/candles/{ticker.upper().strip()}?interval={interval}&limit={limit}"
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def load_news_data(query: str):
    try:
        response = api_get(f"/news/{query}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


def resolve_instrument(query: str):
    try:
        response = api_get(f"/market/resolve?query={query}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException:
        return None


# =========================
# Instrument helpers
# =========================
def set_chart_ticker(ticker: str):
    st.session_state["chart_ticker"] = ticker


def apply_resolved_instrument(instrument: dict):
    st.session_state["chart_ticker"] = instrument["ticker"]
    st.session_state["chart_search_query"] = instrument["name"]
    st.session_state["chart_resolved_name"] = instrument["name"]


def sync_chart_with_instrument(instrument: dict):
    if not instrument:
        return
    apply_resolved_instrument(instrument)


# =========================
# Portfolio helpers
# =========================
def find_position_by_ticker(portfolio: list[dict], ticker: str) -> dict | None:
    ticker = (ticker or "").upper()
    for item in portfolio:
        if str(item.get("ticker", "")).upper() == ticker:
            return item
    return None


def build_position_metrics(position: dict | None, last_price: float | None) -> dict | None:
    if not position:
        return None

    quantity = float(position.get("quantity", 0))
    avg_price = float(position.get("avg_price", 0))

    invested_value = quantity * avg_price

    if last_price is None:
        return {
            "quantity": quantity,
            "avg_price": avg_price,
            "invested_value": invested_value,
            "market_value": None,
            "absolute_pnl": None,
            "pnl_percent": None,
        }

    market_value = quantity * last_price
    absolute_pnl = market_value - invested_value
    pnl_percent = None
    if invested_value != 0:
        pnl_percent = (absolute_pnl / invested_value) * 100

    return {
        "quantity": quantity,
        "avg_price": avg_price,
        "invested_value": invested_value,
        "market_value": market_value,
        "absolute_pnl": absolute_pnl,
        "pnl_percent": pnl_percent,
    }


# =========================
# Summary helper
# =========================
def build_asset_summary(
    ticker: str,
    display_name: str,
    chart_data: dict | None,
    news_data: dict | None,
    position_metrics: dict | None = None
) -> str:
    if not chart_data:
        return "Недостаточно данных для формирования краткого вывода."

    analysis = chart_data.get("analysis", {}) or {}
    signal = analysis.get("signal")
    trend = analysis.get("trend")
    rsi = analysis.get("rsi_14")
    support = analysis.get("support")
    resistance = analysis.get("resistance")
    last_price = analysis.get("last_price")

    news_items = []
    if news_data:
        news_items = news_data.get("items", []) or []

    parts = [f"По бумаге {display_name} ({ticker})"]

    if last_price is not None:
        parts.append(f"последняя доступная цена составляет {round(last_price, 4)}.")

    if signal == "bullish":
        parts.append("Техническая картина сейчас скорее позитивная.")
    elif signal == "bearish":
        parts.append("Техническая картина сейчас скорее слабая.")
    else:
        parts.append("Техническая картина сейчас нейтральная.")

    if trend == "uptrend":
        parts.append("По графику наблюдается восходящее движение.")
    elif trend == "downtrend":
        parts.append("По графику наблюдается нисходящее движение.")
    elif trend == "sideways":
        parts.append("Цена движется в боковом диапазоне.")

    if rsi is not None:
        if rsi > 70:
            parts.append("RSI указывает на зону перекупленности.")
        elif rsi < 30:
            parts.append("RSI указывает на зону перепроданности.")
        else:
            parts.append("RSI находится в нейтральной зоне.")

    if support is not None and resistance is not None:
        parts.append(
            f"Ближайший диапазон выглядит как поддержка {round(support, 4)} и сопротивление {round(resistance, 4)}."
        )

    if position_metrics:
        pnl = position_metrics.get("absolute_pnl")
        pnl_percent = position_metrics.get("pnl_percent")
        if pnl is not None:
            pnl_text = f"{round(pnl, 4)}"
            if pnl_percent is not None:
                pnl_text += f" ({round(pnl_percent, 4)}%)"
            parts.append(f"По твоей позиции текущий результат составляет {pnl_text}.")
    else:
        parts.append("Этой бумаги сейчас нет в твоём портфеле или данные позиции не найдены.")

    if news_items:
        parts.append(f"По инструменту найдено новостей: {len(news_items)}.")
        first_title = news_items[0].get("title")
        if first_title:
            parts.append(f"Последний новостной заголовок: «{first_title}».")
    else:
        parts.append("Свежих новостей в текущей выборке не найдено.")

    parts.append("Вывод носит информационный характер и не является инвестиционной рекомендацией.")

    return " ".join(parts)


# =========================
# Auth page
# =========================
def render_auth():
    st.title("📈 Broker Assistant")
    st.subheader("Единый диалоговый ассистент для брокерской сферы")

    mode = st.radio(
        "Режим",
        ["login", "register"],
        index=0 if st.session_state.auth_mode == "login" else 1,
        format_func=lambda x: "Вход" if x == "login" else "Регистрация"
    )
    st.session_state.auth_mode = mode

    if mode == "register":
        with st.form("register_form"):
            login = st.text_input("Логин", value="", placeholder="Например: anna")
            password = st.text_input("Пароль", type="password", value="", placeholder="Не менее 6 символов")
            submitted = st.form_submit_button("Зарегистрироваться", use_container_width=True)

            if submitted:
                login = login.strip()

                if not login:
                    st.warning("Введите логин.")
                    return

                if not password:
                    st.warning("Введите пароль.")
                    return

                payload = {"login": login, "password": password}

                try:
                    response = session.post(
                        build_url("/auth/register"),
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        st.success("Регистрация успешна. Теперь войди в систему.")
                        st.session_state.auth_mode = "login"
                    else:
                        show_api_error(response)

                except requests.RequestException as e:
                    st.error(f"Ошибка соединения: {e}")

    else:
        with st.form("login_form"):
            login = st.text_input("Логин", value="", placeholder="Твой логин")
            password = st.text_input("Пароль", type="password", value="", placeholder="Твой пароль")
            submitted = st.form_submit_button("Войти", use_container_width=True)

            if submitted:
                login = login.strip()

                if not login:
                    st.warning("Введите логин.")
                    return

                if not password:
                    st.warning("Введите пароль.")
                    return

                payload = {"login": login, "password": password}

                try:
                    response = session.post(
                        build_url("/auth/login"),
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user = data["user"]
                        st.success("Вход выполнен")
                        st.rerun()
                    else:
                        show_api_error(response)

                except requests.RequestException as e:
                    st.error(f"Ошибка соединения: {e}")

    st.divider()
    st.caption(
        "Все данные пользователя — портфель, рынок, новости и аналитика — "
        "используются внутри одного диалога с ассистентом."
    )


# =========================
# Sidebar
# =========================
def render_sidebar():
    with st.sidebar:
        st.title("Broker Assistant")

        if st.session_state.user:
            st.markdown(f"**Пользователь:** `{st.session_state.user['login']}`")
            st.markdown(f"**Роль:** `{st.session_state.user['role']}`")

        st.divider()

        st.markdown("### Быстрые подсказки")
        st.caption("Попробуй спросить:")
        st.code("Какая сейчас цена Сбербанка?")
        st.code("Сделай теханализ Лукойла")
        st.code("Объясни новости по Газпрому")
        st.code("Проанализируй мой портфель")
        st.code("Сравни Сбер и Газпром")

        st.divider()

        if st.button("Выйти", use_container_width=True):
            logout()


# =========================
# Right panel
# =========================
def render_right_panel():
    st.markdown('<div class="sticky-side">', unsafe_allow_html=True)
    st.markdown('<div class="side-card">', unsafe_allow_html=True)

    st.markdown("### Сводка")

    llm_status = load_llm_status()
    if llm_status:
        configured = llm_status.get("configured", False)
        available = llm_status.get("available", False)

        if configured and available:
            st.success("LLM подключена")
        elif configured and not available:
            st.warning("LLM настроена, но недоступна")
        else:
            st.info("LLM не настроена")

    portfolio = load_portfolio()
    st.markdown("#### Портфель")
    if portfolio:
        st.metric("Позиций", len(portfolio))
        for position in portfolio[:5]:
            st.write(
                f"**{position['ticker']}** — {position['quantity']} шт. "
                f"по {position['avg_price']}"
            )
    else:
        st.caption("Портфель пуст")

    st.markdown("#### Последние запросы")
    history = load_history()
    if history:
        for item in history[:5]:
            with st.expander(f"{item['intent_type']}"):
                st.write(item["user_query"])
    else:
        st.caption("История пока пуста")

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Chat
# =========================
def render_dialog_page():
    st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
    st.title("💬 Диалог с ассистентом")
    st.caption("Единая точка входа: ассистент сам использует портфель, рынок, новости и аналитику.")

    if st.session_state.last_resolved_instrument:
        instrument = st.session_state.last_resolved_instrument
        st.info(f"Найден инструмент: {instrument['name']} ({instrument['ticker']})")
    st.markdown("</div>", unsafe_allow_html=True)

    chat_data = load_chat()
    if not chat_data:
        st.error("Не удалось загрузить чат.")
        return

    messages = chat_data.get("messages", [])

    for msg in messages:
        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        created_at = msg.get("created_at", "")

        ui_role = "user" if role == "user" else "assistant"
        with st.chat_message(ui_role):
            st.write(content)
            if created_at:
                st.caption(created_at)

    st.markdown('<div class="chat-bottom-spacer"></div>', unsafe_allow_html=True)

    prompt = st.chat_input("Напиши вопрос ассистенту")
    if prompt:
        payload = {"content": prompt}

        try:
            response = api_post("/chat/me/messages", json_data=payload)
            if response.status_code == 200:
                data = response.json()
                resolved_instrument = data.get("resolved_instrument")
                st.session_state.last_resolved_instrument = resolved_instrument

                if resolved_instrument:
                    sync_chart_with_instrument(resolved_instrument)

                st.rerun()
            else:
                show_api_error(response)
        except requests.RequestException as e:
            st.error(f"Ошибка соединения: {e}")


# =========================
# Unified analytics screen
# =========================
def render_asset_analytics_screen():
    st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
    st.markdown("## 📊 Аналитический экран по бумаге")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### Выбор инструмента")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

    with quick_col1:
        if st.button("SBER", use_container_width=True, key="asset_quick_sber"):
            st.session_state["chart_ticker"] = "SBER"
            st.session_state["chart_search_query"] = "Сбербанк"
            st.session_state["chart_resolved_name"] = "Сбербанк"
            st.rerun()

    with quick_col2:
        if st.button("GAZP", use_container_width=True, key="asset_quick_gazp"):
            st.session_state["chart_ticker"] = "GAZP"
            st.session_state["chart_search_query"] = "Газпром"
            st.session_state["chart_resolved_name"] = "Газпром"
            st.rerun()

    with quick_col3:
        if st.button("LKOH", use_container_width=True, key="asset_quick_lkoh"):
            st.session_state["chart_ticker"] = "LKOH"
            st.session_state["chart_search_query"] = "Лукойл"
            st.session_state["chart_resolved_name"] = "Лукойл"
            st.rerun()

    with quick_col4:
        if st.button("YDEX", use_container_width=True, key="asset_quick_ydex"):
            st.session_state["chart_ticker"] = "YDEX"
            st.session_state["chart_search_query"] = "Яндекс"
            st.session_state["chart_resolved_name"] = "Яндекс"
            st.rerun()

    search_col1, search_col2, search_col3 = st.columns([3, 1, 1])

    with search_col1:
        search_query = st.text_input(
            "Название бумаги или тикер",
            value=st.session_state.get("chart_search_query", ""),
            placeholder="Например: Сбербанк, Газпром, Лукойл, SBER",
            key="asset_search_query"
        )

    with search_col2:
        interval = st.selectbox(
            "Интервал",
            options=["24", "60"],
            format_func=lambda x: "День" if x == "24" else "Час",
            key="asset_chart_interval"
        )

    with search_col3:
        limit = st.selectbox(
            "Период",
            options=[30, 60, 90, 120],
            format_func=lambda x: f"{x} свечей",
            index=1,
            key="asset_chart_limit"
        )

    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        if st.button("Найти инструмент", use_container_width=True, key="asset_find_btn"):
            if search_query.strip():
                instrument = resolve_instrument(search_query.strip())
                if instrument:
                    apply_resolved_instrument(instrument)
                    st.success(f"Найден инструмент: {instrument['name']} ({instrument['ticker']})")
                    st.rerun()
                else:
                    st.warning("Инструмент не найден.")

    with action_col2:
        if st.button("Обновить экран", use_container_width=True, key="asset_refresh_btn"):
            st.rerun()

    ticker = st.session_state.get("chart_ticker", "SBER")
    display_name = st.session_state.get("chart_resolved_name") or ticker

    chart_data = load_chart_data(
        ticker=ticker,
        interval=interval,
        limit=limit
    )
    news_data = load_news_data(ticker)
    portfolio = load_portfolio()

    st.markdown(f"### Инструмент: **{display_name} ({ticker})**")

    if not chart_data:
        st.warning("Не удалось загрузить рыночные данные и теханализ.")
        return

    candles = chart_data.get("candles", []) or []
    analysis = chart_data.get("analysis", {}) or {}

    if not candles:
        st.warning("Свечи не найдены.")
        return

    rows = []
    for candle in candles:
        begin_value = candle.get("begin")
        open_value = candle.get("open")
        high_value = candle.get("high")
        low_value = candle.get("low")
        close_value = candle.get("close")

        if None in [begin_value, open_value, high_value, low_value, close_value]:
            continue

        rows.append({
            "begin": begin_value,
            "open": float(open_value),
            "high": float(high_value),
            "low": float(low_value),
            "close": float(close_value),
            "volume": float(candle["value"]) if candle.get("value") is not None else None,
        })

    if not rows:
        st.warning("Недостаточно данных для графика.")
        return

    df = pd.DataFrame(rows)
    df["begin"] = pd.to_datetime(df["begin"])
    df = df.sort_values("begin")
    df["SMA_5"] = df["close"].rolling(window=5).mean()
    df["SMA_10"] = df["close"].rolling(window=10).mean()

    last_price = analysis.get("last_price")
    current_position = find_position_by_ticker(portfolio, ticker)
    position_metrics = build_position_metrics(current_position, last_price)

    top_col1, top_col2, top_col3, top_col4 = st.columns(4)
    with top_col1:
        st.metric("Цена", round(last_price, 4) if last_price is not None else "—")
    with top_col2:
        st.metric("Тренд", analysis.get("trend") or "—")
    with top_col3:
        st.metric("Сигнал", analysis.get("signal") or "—")
    with top_col4:
        st.metric("RSI(14)", round(analysis.get("rsi_14"), 4) if analysis.get("rsi_14") is not None else "—")

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["begin"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Candles"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["begin"],
            y=df["SMA_5"],
            mode="lines",
            name="SMA 5"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["begin"],
            y=df["SMA_10"],
            mode="lines",
            name="SMA 10"
        )
    )

    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Цена",
        xaxis_rangeslider_visible=False,
        height=560,
        margin=dict(l=20, r=20, t=30, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💼 Моя позиция по этой бумаге")
    if current_position and position_metrics:
        pos_col1, pos_col2, pos_col3, pos_col4 = st.columns(4)
        with pos_col1:
            st.metric("Количество", round(position_metrics["quantity"], 4))
        with pos_col2:
            st.metric("Средняя цена", round(position_metrics["avg_price"], 4))
        with pos_col3:
            st.metric(
                "Рыночная стоимость",
                round(position_metrics["market_value"], 4) if position_metrics["market_value"] is not None else "—"
            )
        with pos_col4:
            pnl = position_metrics.get("absolute_pnl")
            pnl_percent = position_metrics.get("pnl_percent")
            if pnl is not None:
                pnl_text = f"{round(pnl, 4)}"
                if pnl_percent is not None:
                    pnl_text += f" ({round(pnl_percent, 4)}%)"
                st.metric("P&L", pnl_text)
            else:
                st.metric("P&L", "—")
    else:
        st.caption("Этой бумаги сейчас нет в твоём портфеле.")

    info_col1, info_col2 = st.columns([2, 1])

    with info_col1:
        st.markdown("### 🧠 Краткий AI-вывод")
        ai_summary = build_asset_summary(
            ticker=ticker,
            display_name=display_name,
            chart_data=chart_data,
            news_data=news_data,
            position_metrics=position_metrics
        )
        st.write(ai_summary)

        chat_col1, chat_col2 = st.columns(2)

        with chat_col1:
            if st.button("Разобрать график в чате", use_container_width=True, key="asset_chat_ta_btn"):
                prompt = f"Сделай технический анализ {ticker} по текущему графику и объясни сигнал простыми словами"
                response = api_post("/chat/me/messages", json_data={"content": prompt})
                if response.status_code == 200:
                    data = response.json()
                    resolved_instrument = data.get("resolved_instrument")
                    st.session_state.last_resolved_instrument = resolved_instrument
                    if resolved_instrument:
                        sync_chart_with_instrument(resolved_instrument)
                    st.success("Запрос отправлен в чат.")
                    st.rerun()
                else:
                    show_api_error(response)

        with chat_col2:
            if st.button("Объяснить новости в чате", use_container_width=True, key="asset_chat_news_btn"):
                prompt = f"Объясни новости по {ticker} и их возможное влияние простыми словами"
                response = api_post("/chat/me/messages", json_data={"content": prompt})
                if response.status_code == 200:
                    data = response.json()
                    resolved_instrument = data.get("resolved_instrument")
                    st.session_state.last_resolved_instrument = resolved_instrument
                    if resolved_instrument:
                        sync_chart_with_instrument(resolved_instrument)
                    st.success("Запрос отправлен в чат.")
                    st.rerun()
                else:
                    show_api_error(response)

    with info_col2:
        st.markdown("### 📌 Техпоказатели")
        st.write(f"**Паттерн:** {analysis.get('pattern') or '—'}")
        st.write(f"**MACD:** {round(analysis.get('macd'), 4) if analysis.get('macd') is not None else '—'}")
        st.write(f"**MACD signal:** {round(analysis.get('macd_signal'), 4) if analysis.get('macd_signal') is not None else '—'}")
        st.write(f"**Поддержка:** {round(analysis.get('support'), 4) if analysis.get('support') is not None else '—'}")
        st.write(f"**Сопротивление:** {round(analysis.get('resistance'), 4) if analysis.get('resistance') is not None else '—'}")

    st.markdown("### 📰 Новости")
    if not news_data:
        st.info("Не удалось загрузить новости.")
    else:
        items = news_data.get("items", []) or []
        if not items:
            st.caption("Новости пока не найдены.")
        else:
            for item in items[:5]:
                title = item.get("title", "Без заголовка")
                content = item.get("content", "")
                published_at = item.get("published_at", "")
                source_name = item.get("source_name", "")

                with st.container():
                    st.markdown(f"**{title}**")

                    meta_parts = []
                    if source_name:
                        meta_parts.append(source_name)
                    if published_at:
                        meta_parts.append(published_at)

                    if meta_parts:
                        st.caption(" • ".join(meta_parts))

                    if content:
                        st.write(content)

                    st.divider()

    st.caption("Аналитический экран носит информационный характер и не является инвестиционной рекомендацией.")


# =========================
# Main
# =========================
def main():
    inject_sticky_styles()

    if not st.session_state.token:
        render_auth()
        return

    if not st.session_state.user:
        if not load_current_user():
            render_auth()
            return

    render_sidebar()

    tab1, tab2 = st.tabs(["💬 Диалог", "📊 Аналитический экран"])

    with tab1:
        left_col, right_col = st.columns([3, 1])

        with left_col:
            render_dialog_page()

        with right_col:
            render_right_panel()

    with tab2:
        render_asset_analytics_screen()


if __name__ == "__main__":
    main()