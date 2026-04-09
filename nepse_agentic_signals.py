import streamlit as st
import pandas as pd
import numpy as np
import ssl
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context

st.set_page_config(page_title="NEPSE Agentic Signals", layout="wide", initial_sidebar_state="collapsed")
st.title("🚨 NEPSE Agentic Signals Engine")
st.markdown("**Real-time • Conservative Signals** | *Not financial advice*")

@st.cache_data(ttl=180)
def fetch_nepse_data():
    try:
        from nepse_scraper import NepseScraper
        with st.spinner("Fetching live NEPSE data..."):
            scraper = NepseScraper(verify_ssl=False)
            data = scraper.get_today_price()
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'symbol': 'SYMBOL',
                'closingPrice': 'LTP',
                'percentChange': 'CHANGE%',
                'volume': 'VOLUME',
                'noOfTransactions': 'TRADES'
            })
            df = df[['SYMBOL', 'LTP', 'CHANGE%', 'VOLUME', 'TRADES']]
            return df
    except Exception as e:
        st.error(f"⚠️ Data issue: {e}\nPlease refresh.")
        return pd.DataFrame()

stocks = fetch_nepse_data()
if stocks.empty:
    st.stop()

def agentic_score(row):
    mom_score = max(0, min(1, (row['CHANGE%'] + 2) / 5))
    vol_score = 1.0 if row['VOLUME'] > 15000 else row['VOLUME'] / 15000
    trade_score = 1.0 if row['TRADES'] > 100 else row['TRADES'] / 100
    total = round(0.5 * mom_score + 0.3 * vol_score + 0.2 * trade_score, 3)
    return max(0.23, min(0.95, total))

stocks['SCORE'] = stocks.apply(agentic_score, axis=1)
stocks['CONFIDENCE'] = np.where(stocks['SCORE'] > 0.55, 'High', np.where(stocks['SCORE'] > 0.40, 'Medium', 'Low'))
stocks['DIRECTION'] = 'LONG'

signals = stocks[stocks['SCORE'] >= 0.23].copy()
signals = signals.sort_values('SCORE', ascending=False).reset_index(drop=True)

def generate_note(row):
    if row['CHANGE%'] > 1.5:
        return f"Strong momentum (+{row['CHANGE%']:.2f}%) 🧠"
    elif row['VOLUME'] > 50000:
        return f"High volume spike detected 🧠"
    else:
        return f"Stable conservative signal 🧠"

signals['AGENT_NOTE'] = signals.apply(generate_note, axis=1)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("Live Signals")
    display_df = signals[['SYMBOL', 'LTP', 'CHANGE%', 'SCORE', 'CONFIDENCE', 'AGENT_NOTE']]
    st.dataframe(display_df.style.background_gradient(cmap='RdYlGn', subset=['SCORE', 'CHANGE%']), use_container_width=True, hide_index=True)

with col2:
    st.metric("Signals", len(signals))
    st.metric("Avg Score", f"{signals['SCORE'].mean():.3f}")
    st.success("✅ Live Data")

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

st.caption("Your own NEPSE Signals App • Mobile friendly")
