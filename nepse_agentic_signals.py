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
            
            rename_map = {
                'symbol': 'SYMBOL',
                'lastTradedPrice': 'LTP',
                'closingPrice': 'LTP',
                'change': 'CHANGE%',
                'percentChange': 'CHANGE%',
                'volume': 'VOLUME',
                'totalTrades': 'TRADES',
                'noOfTransactions': 'TRADES'
            }
            df = df.rename(columns=rename_map)
            
            if 'SYMBOL' not in df.columns: df['SYMBOL'] = 'Unknown'
            if 'LTP' not in df.columns: df['LTP'] = 0.0
            if 'CHANGE%' not in df.columns: df['CHANGE%'] = 0.0
            if 'VOLUME' not in df.columns: df['VOLUME'] = 0
            if 'TRADES' not in df.columns: df['TRADES'] = 0
            
            for col in ['LTP', 'CHANGE%', 'VOLUME', 'TRADES']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df[['SYMBOL', 'LTP', 'CHANGE%', 'VOLUME', 'TRADES']]
    except Exception as e:
        st.error(f"⚠️ Cannot fetch data right now.\nError: {str(e)[:100]}")
        return pd.DataFrame(columns=['SYMBOL', 'LTP', 'CHANGE%', 'VOLUME', 'TRADES'])

stocks = fetch_nepse_data()

if len(stocks) == 0:
    st.stop()

def agentic_score(row):
    mom = max(0, min(1, (row['CHANGE%'] + 2) / 5))
    vol = 1.0 if row['VOLUME'] > 15000 else row['VOLUME'] / 15000
    trade = 1.0 if row['TRADES'] > 100 else row['TRADES'] / 100
    total = round(0.5 * mom + 0.3 * vol + 0.2 * trade, 3)
    return max(0.23, min(0.95, total))

stocks['SCORE'] = stocks.apply(agentic_score, axis=1)
stocks['CONFIDENCE'] = np.where(stocks['SCORE'] > 0.55, 'High', 
                               np.where(stocks['SCORE'] > 0.40, 'Medium', 'Low'))
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
    st.subheader("📊 Live Agentic Signals")
    display_cols = ['SYMBOL', 'LTP', 'CHANGE%', 'SCORE', 'CONFIDENCE', 'AGENT_NOTE']
    st.dataframe(signals[display_cols], use_container_width=True, hide_index=True)

with col2:
    st.metric("Active Signals", len(signals))
    st.metric("Avg Score", f"{signals['SCORE'].mean():.3f}")
    st.success("✅ Connected to NEPSE")

if st.button("🔄 Refresh Live Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.caption("Your personal NEPSE Agentic Signals Platform • Educational purpose only")
