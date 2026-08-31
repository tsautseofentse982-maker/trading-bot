import streamlit as st
import time
import pandas as pd
from binance.client import Client

# Set up page layout
st.set_page_config(page_title="Crypto Trading Bot Dashboard", page_icon="📈", layout="wide")
st.title("🤖 Binance Automated Trading Dashboard")

# -------------------------------------------------------------------
# Sidebar - User Controls & Inputs
# -------------------------------------------------------------------
st.sidebar.header("Configuration")

# Retrieve API keys securely from Streamlit Secrets or manual input
api_key = st.sidebar.text_input("Binance Testnet API Key", value=st.secrets.get("API_KEY", ""), type="password")
api_secret = st.sidebar.text_input("Binance Testnet Secret Key", value=st.secrets.get("API_SECRET", ""), type="password")

symbol = st.sidebar.selectbox("Select Asset Pair", ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
fast_ema = st.sidebar.number_input("Fast EMA Period", value=9, min_value=1)
slow_ema = st.sidebar.number_input("Slow EMA Period", value=21, min_value=1)

sl_pct = st.sidebar.slider("Stop-Loss %", min_value=0.5, max_value=5.0, value=1.5) / 100
tp_pct = st.sidebar.slider("Take-Profit %", min_value=1.0, max_value=10.0, value=3.0) / 100

start_bot = st.sidebar.button("▶️ Start Trading Bot")
stop_bot = st.sidebar.button("⏹️ Stop Trading Bot")

# -------------------------------------------------------------------
# Main Dashboard UI Setup
# -------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
metric_price = col1.empty()
metric_fast = col2.empty()
metric_slow = col3.empty()

status_box = st.empty()
chart_area = st.empty()

# Persistent state management
if "bot_active" not in st.session_state:
    st.session_state.bot_active = False

if start_bot:
    if not api_key or not api_secret:
        st.error("Please enter both API Key and Secret Key in the sidebar or Advanced Settings.")
    else:
        st.session_state.bot_active = True

if stop_bot:
    st.session_state.bot_active = False
    status_box.warning("Bot status: STOPPED")

# -------------------------------------------------------------------
# Bot Engine Loop
# -------------------------------------------------------------------
if st.session_state.bot_active:
    status_box.success(f"Bot status: RUNNING live on {symbol}")
    client = Client(api_key, api_secret, testnet=True)
    
    # Live execution loop
    while st.session_state.bot_active:
        try:
            # Fetch market data
            klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "100 candles")
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            df['close'] = pd.to_numeric(df['close'])
            df['ema_fast'] = df['close'].ewm(span=fast_ema, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=slow_ema, adjust=False).mean()

            curr_row = df.iloc[-2]
            current_price = curr_row['close']

            # Update real-time metrics on dashboard
            metric_price.metric("Current Price", f"${current_price:,.2f}")
            metric_fast.metric(f"EMA ({fast_ema})", f"${curr_row['ema_fast']:,.2f}")
            metric_slow.metric(f"EMA ({slow_ema})", f"${curr_row['ema_slow']:,.2f}")

            # Update live price line chart
            chart_area.line_chart(df[['close', 'ema_fast', 'ema_slow']].tail(30))

            time.sleep(10)  # Wait 10 seconds before refreshing metrics

        except Exception as e:
            status_box.error(f"Error connecting to Binance: {e}")
            st.session_state.bot_active = False
            break
