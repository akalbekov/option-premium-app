import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf
import numpy as np
from scipy.stats import norm

# --- Black-Scholes Formula ---
def black_scholes(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'call':
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

# --- Time to Expiry Formatter ---
def format_time_to_expiry(expiration_datetime):
    now = datetime.now()
    delta = expiration_datetime - now
    total_seconds = int(delta.total_seconds())
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{days}d {hours}h {minutes}m {seconds}s"

# --- Streamlit UI ---
st.set_page_config(page_title="Option Premium Estimator")
st.title("📈 Option Premium Estimator")

col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input("Ticker", value="AAPL")
    stock_price = st.number_input("Custom Stock Price", value=223.0)
    strike_price = st.number_input("Strike Price", value=222.5)
    option_type = st.selectbox("Option Type", ["call", "put"])

with col2:
    year = st.number_input("Expiration Year", min_value=2024, max_value=2100, value=datetime.now().year)
    month = st.number_input("Expiration Month", min_value=1, max_value=12, value=datetime.now().month)
    day = st.number_input("Expiration Day", min_value=1, max_value=31)
    user_iv = st.text_input("Volatility (% - optional)", value="")

if st.button("Estimate Premium"):
    try:
        expiration = datetime(year, month, day, 15, 0, 0)
        T = (expiration - datetime.now()).total_seconds() / (365 * 24 * 60 * 60)

        if T <= 0:
            st.error("Expiration must be in the future.")
        else:
            r = 0.01
            if user_iv.strip():
                iv = float(user_iv.strip()) / 100
                source = "(manual input)"
            else:
                chain = yf.Ticker(ticker).option_chain(f"{year}-{month:02d}-{day:02d}")
                options_df = chain.calls if option_type == 'call' else chain.puts
                option = options_df[options_df['strike'] == strike_price]
                if option.empty:
                    st.error("Option not found.")
                    st.stop()
                iv = option['impliedVolatility'].values[0]
                source = "(from yfinance)"

            premium = black_scholes(stock_price, strike_price, T, r, iv, option_type)
            time_left = format_time_to_expiry(expiration)

            st.success(f"{option_type.title()} Premium: ${premium:.2f}")
            st.write(f"IV: {iv:.2%} {source}")
            st.write(f"⏳ Time to Expiry: {time_left}")
    except Exception as e:
        st.error(f"Error: {e}")
