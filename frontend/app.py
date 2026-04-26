import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

API_BASE_URL = "http://127.0.0.1:8000"

session = requests.Session()
session.trust_env = False

st.set_page_config(
    page_title="Broker Assistant",
    layout="wide"
)

DEFAULT_SESSION_STATE = {
    "token": None,
    "user": None,
    "auth_mode": "login",
    "active_page": "dialog",
    "last_resolved_instrument": None,
    "chart_search_query": "",
    "chart_resolved_name": None,
    "chart_ticker": "SBER",
    "chart_period": "day",
}

for key, value in DEFAULT_SESSION_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


def inject_styles():
    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            font-size: 19px;
            color: #1f2937;
        }


        /* Заголовки */
        h1 {
            font-size: 34px;
        }

        h2 {
            font-size: 28px;
        }

        h3 {
            font-size: 24px;
        }

        h4 {
            font-size: 20px;
        }

        /* Markdown внутри Streamlit */
        .stMarkdown p {
            font-size: 18px;
            line-height: 1.6;
        }

        /* Чат сообщения */
        div[data-testid="stChatMessage"] p {
            font-size: 18px;
        }

        /* Поле ввода */
        textarea, input {
            font-size: 17px !important;
        }

        /* Caption (мелкий текст) */
        .stCaption {
            font-size: 15px;
            color: #6b7280;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            font-size: 16px;
        }

        /* Кнопки */
        .stButton>button {
            font-size: 16px;
            padding: 8px 14px;
        }


        /* ===== Убираем "жирный/кривой" markdown Streamlit ===== */
        .stMarkdown h3 {
            font-size: 20px;
            font-weight: 600;
        }

        /* ===== Цвета (убираем красный Streamlit) ===== */
        :root {
            --primary-color: #2563eb; /* синий */
        }

        .stButton>button {
            border-radius: 10px;
            border: 1px solid #d1d5db;
            background-color: #f9fafb;
            color: #1f2937;
        }

        .stButton>button:hover {
            background-color: #e5e7eb;
        }

        /* primary кнопки → синие */
        .stButton>button[kind="primary"] {
            background-color: #2563eb;
            color: white;
            border: none;
        }

        /* alerts вместо красных */
        .stAlert {
            border-radius: 10px;
        }

        div[data-baseweb="notification"] {
            border-left: 4px solid #2563eb !important;
        }

        /* ===== Выравнивание контента ===== */
        .content-shell {
            max-width: 900px;
            margin: 0 auto;
            padding-left: 10px;
            padding-right: 10px;
        }

        /* ===== Чат ===== */
        div[data-testid="stChatMessage"] {
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
        }

        /* ===== Поле ввода — ровно по центру ===== */
        div[data-testid="stChatInput"] {
            position: fixed;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: min(900px, calc(100vw - 40px));
            z-index: 100;
            background: white;
            border-top: 1px solid #e5e7eb;
            padding: 12px 16px;
        }

        /* ===== Убираем лишнюю жирность caption ===== */
        .stCaption {
            color: #6b7280;
            font-size: 13px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )


def render_header():
    st.markdown('<div class="page-shell">', unsafe_allow_html=True)
    st.title("Broker Assistant")
    st.caption("Интеллектуальный ассистент для брокерской сферы")
    st.markdown("</div>", unsafe_allow_html=True)


def render_top_navigation():
    st.markdown('<div class="top-nav-wrap">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
                "Диалог",
                use_container_width=True,
                key="top_nav_dialog",
                type="primary" if st.session_state.active_page == "dialog" else "secondary"
        ):
            st.session_state.active_page = "dialog"
            st.rerun()

    with col2:
        if st.button(
                "Аналитический экран",
                use_container_width=True,
                key="top_nav_analytics",
                type="primary" if st.session_state.active_page == "analytics" else "secondary"
        ):
            st.session_state.active_page = "analytics"
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


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


def load_chart_data(ticker: str, period: str = "day"):
    try:
        response = api_get(
            f"/charts/candles/{ticker.upper().strip()}?period={period}&market_type=shares"
        )
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


def apply_resolved_instrument(instrument: dict):
    st.session_state["chart_ticker"] = instrument["ticker"]
    st.session_state["chart_search_query"] = instrument["name"]
    st.session_state["chart_resolved_name"] = instrument["name"]


def sync_chart_with_instrument(instrument: dict):
    if not instrument:
        return
    apply_resolved_instrument(instrument)


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


def build_asset_summary(
        ticker: str,
        display_name: str,
        chart_data: dict | None,
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
    candles_count = analysis.get("candles_count")
    last_candle_time = analysis.get("last_candle_time")

    parts = [f"По инструменту {display_name} ({ticker})"]

    if last_price is not None:
        parts.append(f"последняя цена составляет {round(last_price, 4)}.")

    if trend == "uptrend":
        parts.append("По графику наблюдается восходящее движение.")
    elif trend == "downtrend":
        parts.append("По графику наблюдается нисходящее движение.")
    else:
        parts.append("По графику сейчас скорее боковое движение.")

    if signal == "bullish":
        parts.append("Сигнал выглядит скорее позитивно.")
    elif signal == "bearish":
        parts.append("Сигнал выглядит скорее слабо.")
    else:
        parts.append("Сигнал нейтральный.")

    if rsi is not None:
        if rsi > 70:
            parts.append("RSI указывает на перекупленность.")
        elif rsi < 30:
            parts.append("RSI указывает на перепроданность.")
        else:
            parts.append("RSI находится в нейтральной зоне.")

    if support is not None and resistance is not None:
        parts.append(
            f"Ближайший диапазон выглядит как поддержка {round(support, 4)} и сопротивление {round(resistance, 4)}."
        )

    if candles_count:
        parts.append(f"Для анализа использовано свечей: {candles_count}.")
    if last_candle_time:
        parts.append(f"Последняя свеча начинается в {last_candle_time}.")

    if position_metrics:
        pnl = position_metrics.get("absolute_pnl")
        pnl_percent = position_metrics.get("pnl_percent")
        if pnl is not None:
            pnl_text = f"{round(pnl, 4)}"
            if pnl_percent is not None:
                pnl_text += f" ({round(pnl_percent, 4)}%)"
            parts.append(f"По вашей позиции текущий результат составляет {pnl_text}.")
    else:
        parts.append("Этой бумаги сейчас нет в вашем портфеле или данные позиции не найдены.")

    parts.append("Это информационный комментарий, а не инвестиционная рекомендация.")
    return " ".join(parts)


def render_auth():
    left, center, right = st.columns([2, 3, 2])

    with center:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown("## Вход в систему")

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
                        st.markdown("</div>", unsafe_allow_html=True)
                        return

                    if not password:
                        st.warning("Введите пароль.")
                        st.markdown("</div>", unsafe_allow_html=True)
                        return

                    payload = {"login": login, "password": password}

                    try:
                        response = session.post(
                            build_url("/auth/register"),
                            json=payload,
                            timeout=30
                        )

                        if response.status_code == 200:
                            st.success("Регистрация успешна. Теперь войдите в систему.")
                            st.session_state.auth_mode = "login"
                        else:
                            show_api_error(response)

                    except requests.RequestException as e:
                        st.error(f"Ошибка соединения: {e}")

        else:
            with st.form("login_form"):
                login = st.text_input("Логин", value="", placeholder="Ваш логин")
                password = st.text_input("Пароль", type="password", value="", placeholder="Ваш пароль")
                submitted = st.form_submit_button("Войти", use_container_width=True)

                if submitted:
                    login = login.strip()

                    if not login:
                        st.warning("Введите логин.")
                        st.markdown("</div>", unsafe_allow_html=True)
                        return

                    if not password:
                        st.warning("Введите пароль.")
                        st.markdown("</div>", unsafe_allow_html=True)
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
                            st.success("Вход выполнен.")
                            st.rerun()
                        else:
                            show_api_error(response)

                    except requests.RequestException as e:
                        st.error(f"Ошибка соединения: {e}")

        st.caption("Портфель, рынок и аналитика используются внутри одного диалога с ассистентом.")
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.title("Broker Assistant")

        if st.session_state.user:
            st.markdown(f"**Пользователь:** `{st.session_state.user['login']}`")
            st.markdown(f"**Роль:** `{st.session_state.user['role']}`")

        st.divider()

        st.markdown("### Примеры запросов")
        st.code("Какая сейчас цена Сбербанка")
        st.code("Сделай теханализ Лукойла")
        st.code("Когда дата отсечки по дивидендам по Татнефти в 2026 году")
        st.code("Когда следующий купон по облигации RU000A10DFJ2")
        st.code("Проанализируй мой портфель")

        st.divider()

        if st.button("Выйти", use_container_width=True):
            logout()


def render_right_panel():
    st.markdown('<div class="right-panel-card">', unsafe_allow_html=True)

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


def render_dialog_page():
    st.markdown('<div class="content-shell">', unsafe_allow_html=True)
    st.markdown('<div class="page-title"><h3>Диалог с ассистентом</h3></div>', unsafe_allow_html=True)
    st.caption("Пожалуйста, проверяйте важную информацию, ассистент может ошибаться.")

    if st.session_state.last_resolved_instrument:
        instrument = st.session_state.last_resolved_instrument
        st.info(f"Найдена бумага: {instrument['name']} ({instrument['ticker']})")

    chat_data = load_chat()
    if not chat_data:
        st.error("Не удалось загрузить чат.")
        st.markdown("</div>", unsafe_allow_html=True)
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

    st.markdown('<div class="chat-spacer"></div>', unsafe_allow_html=True)

    prompt = st.chat_input("Напишите вопрос ассистенту")
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

    st.markdown("</div>", unsafe_allow_html=True)


def render_asset_analytics_screen():
    st.markdown('<div class="analytics-controls">', unsafe_allow_html=True)
    st.markdown('<div class="page-title"> Аналитический экран</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-caption">Акции. Периоды: час, день, неделя, месяц, год.</div>',
        unsafe_allow_html=True
    )

    search_col1, search_col2 = st.columns([3, 1])

    with search_col1:
        search_query = st.text_input(
            "Название инструмента или тикер",
            value=st.session_state.get("chart_search_query", ""),
            placeholder="Например: Сбербанк, Газпром, Лукойл",
            key="asset_search_query"
        )

    with search_col2:
        period = st.selectbox(
            "Период",
            options=["hour", "day", "week", "month", "year"],
            index=["hour", "day", "week", "month", "year"].index(st.session_state.get("chart_period", "day")),
            format_func=lambda x: {
                "hour": "Час",
                "day": "День",
                "week": "Неделя",
                "month": "Месяц",
                "year": "Год",
            }[x],
            key="asset_chart_period"
        )

    action_col1, action_col2, action_col3 = st.columns([1, 1, 1])

    with action_col1:
        if st.button("Найти бумагу", use_container_width=True, key="asset_find_btn"):
            if search_query.strip():
                instrument = resolve_instrument(search_query.strip())
                if instrument:
                    apply_resolved_instrument(instrument)
                    st.success(f"Найдена бумага: {instrument['name']} ({instrument['ticker']})")
                    st.rerun()
                else:
                    st.warning("Бумага не найден.")

    with action_col2:
        if st.button("Обновить экран", use_container_width=True, key="asset_refresh_btn"):
            st.rerun()

    with action_col3:
        if st.button("Открыть анализ в чате", use_container_width=True, key="asset_chat_ta_btn"):
            ticker = st.session_state.get("chart_ticker", "SBER")
            prompt = f"Сделай технический анализ {ticker} по текущему графику и объясни сигнал простыми словами"
            response = api_post("/chat/me/messages", json_data={"content": prompt})
            if response.status_code == 200:
                data = response.json()
                resolved_instrument = data.get("resolved_instrument")
                st.session_state.last_resolved_instrument = resolved_instrument
                if resolved_instrument:
                    sync_chart_with_instrument(resolved_instrument)
                st.session_state.active_page = "dialog"
                st.rerun()
            else:
                show_api_error(response)

    st.markdown("</div>", unsafe_allow_html=True)

    ticker = st.session_state.get("chart_ticker", "SBER")
    display_name = st.session_state.get("chart_resolved_name") or ticker
    period = st.session_state.get("asset_chart_period", st.session_state.get("chart_period", "day"))

    chart_data = load_chart_data(
        ticker=ticker,
        period=period
    )
    portfolio = load_portfolio()

    st.markdown('<div class="chart-shell">', unsafe_allow_html=True)
    st.markdown(f"### Бумага: **{display_name} ({ticker})**")

    if not chart_data:
        st.warning("Не удалось загрузить рыночные данные и теханализ.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    candles = chart_data.get("candles", []) or []
    analysis = chart_data.get("analysis", {}) or {}

    if not candles:
        st.warning("Свечи не найдены.")
        st.markdown("</div>", unsafe_allow_html=True)
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
        })

    if not rows:
        st.warning("Недостаточно данных для графика.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df = pd.DataFrame(rows)
    df["begin"] = pd.to_datetime(df["begin"])
    df = df.sort_values("begin")
    df["SMA_5"] = df["close"].rolling(window=5).mean()
    df["SMA_10"] = df["close"].rolling(window=10).mean()

    last_price = analysis.get("last_price")
    current_position = find_position_by_ticker(portfolio, ticker)
    position_metrics = build_position_metrics(current_position, last_price)

    st.markdown('<div class="metrics-shell">', unsafe_allow_html=True)
    top_col1, top_col2, top_col3, top_col4 = st.columns(4)
    with top_col1:
        st.metric("Цена", round(last_price, 4) if last_price is not None else "—")
    with top_col2:
        st.metric("Тренд", analysis.get("trend") or "—")
    with top_col3:
        st.metric("Сигнал", analysis.get("signal") or "—")
    with top_col4:
        st.metric("RSI(14)", round(analysis.get("rsi_14"), 4) if analysis.get("rsi_14") is not None else "—")
    st.markdown("</div>", unsafe_allow_html=True)

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=df["begin"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Свечи"
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
        width=980,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Позиция по бумаге")
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
        st.caption("Этой бумаги сейчас нет в вашем портфеле.")

    st.markdown('<div class="summary-shell">', unsafe_allow_html=True)
    info_col1, info_col2 = st.columns([2, 1])

    with info_col1:
        st.markdown("### Краткий вывод")
        summary = build_asset_summary(
            ticker=ticker,
            display_name=display_name,
            chart_data=chart_data,
            position_metrics=position_metrics
        )
        st.write(summary)

    with info_col2:
        st.markdown("### Технические показатели")
        st.write(f"**Свечей в анализе:** {analysis.get('candles_count') or '—'}")
        st.write(f"**Последняя свеча:** {analysis.get('last_candle_time') or '—'}")
        st.write(f"**Поддержка:** {round(analysis.get('support'), 4) if analysis.get('support') is not None else '—'}")
        st.write(
            f"**Сопротивление:** {round(analysis.get('resistance'), 4) if analysis.get('resistance') is not None else '—'}")
        st.write(f"**SMA 5:** {round(analysis.get('sma_5'), 4) if analysis.get('sma_5') is not None else '—'}")
        st.write(f"**SMA 10:** {round(analysis.get('sma_10'), 4) if analysis.get('sma_10') is not None else '—'}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Аналитический экран носит информационный характер и не является инвестиционной рекомендацией.")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_styles()

    if not st.session_state.token:
        render_header()
        render_auth()
        return

    if not st.session_state.user:
        if not load_current_user():
            render_header()
            render_auth()
            return

    render_sidebar()
    render_header()
    render_top_navigation()

    if st.session_state.active_page == "dialog":
        left_col, right_col = st.columns([3, 1])

        with left_col:
            render_dialog_page()

        with right_col:
            render_right_panel()
    else:
        render_asset_analytics_screen()


if __name__ == "__main__":
    main()