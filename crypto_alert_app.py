# Import Required Libraries
import streamlit as st   # Create the Web Interface
import requests          # To get data from CoinGecko API
import pandas as pd      # For handling data (prices and chart)

# Configure the Streamlit Page
st.set_page_config(page_title="Crypto Price Checker + Alerts", layout="centered")

st.title("💹 Crypto Price Checker + Alerts")

# Get all available crypto currencies
@st.cache_data(ttl=3600)
def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    data = response.json()
    return sorted(data, key=lambda x: x["name"])  # Sorted by name for usability

# Get Current Prices
@st.cache_data(ttl=60)
def get_current_prices(coin_id, currencies):
    currency_str = ",".join(currencies)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies={currency_str}"
    data = requests.get(url).json()
    return data.get(coin_id, {})

# Get 7-day Price History 
@st.cache_data(ttl=60)
def get_price_history(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    data = requests.get(url).json()
    prices = data.get("prices", [])
    df = pd.DataFrame(prices, columns=["timestamp", "price"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df

# Dropdown for coin selection
coins = get_all_coins()
coin_options = [f"{coin['name']} ({coin['symbol'].upper()})" for coin in coins]
coin_lookup = {f"{coin['name']} ({coin['symbol'].upper()})": coin["id"] for coin in coins}

selected_coin_display = st.selectbox("Select a cryptocurrency", coin_options)
selected_coin_id = coin_lookup[selected_coin_display]

# Let User choose Currencies and option
currencies = st.multiselect("Select currencies to view", ["usd", "ngn", "eur"], default=["usd"])
show_chart = st.checkbox("📈 Show 7-day price chart")
auto_refresh = st.checkbox("🔄 Auto-refresh every 60 seconds")

# Set Price Alert
st.subheader("🚨 Set Alert Thresholds (USD only)")
min_price = st.number_input("Minimum price (alert if price goes below)", min_value=0.0, value=0.0, step=0.01)
max_price = st.number_input("Maximum price (alert if price goes above)", min_value=0.0, value=0.0, step=0

# Fetch and Display Current Prices
st.subheader(f"🔍 Current Price for {selected_coin_display}")
with st.spinner("Fetching current prices..."):
    prices = get_current_prices(selected_coin_id, currencies)

    if not prices:
        st.error("❌ Could not fetch price data. Please try again later.")
    else:
        for cur in currencies:
            price = prices.get(cur)
            if price is not None:
                st.write(f"**{cur.upper()}**: {'$' if cur == 'usd' else ''}{price:,.2f}")

        # Alert check (only for USD)
        if "usd" in prices:
            usd_price = prices["usd"]
            if min_price and usd_price < min_price:
                st.warning(f"⚠️ Alert: Price dropped below ${min_price:,.2f} (Current: ${usd_price:,.2f})")
            if max_price and usd_price > max_price:
                st.warning(f"⚠️ Alert: Price rose above ${max_price:,.2f} (Current: ${usd_price:,.2f})")

# --- Price Chart ---
if show_chart:
    st.subheader("📉 7-Day Price Chart (USD)")
    df = get_price_history(selected_coin_id)
    st.line_chart(df["price"])
