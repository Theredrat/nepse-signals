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
            
            # Robust column mapping for real nepse-scraper
            rename_map = {
                'symbol': 'SYMBOL',
                'lastTradedPrice': 'LTP',
                'change': 'CHANGE%',
                'volume': 'VOLUME',
                'totalTrades': 'TRADES',
                'closingPrice': 'LTP',
                'percentChange': 'CHANGE%',
                'noOfTransactions': 'TRADES'
            }
            df = df.rename(columns=rename_map)
            
            # Keep available columns
            needed = ['SYMBOL', 'LTP', 'CHANGE%', 'VOLUME', 'TRADES']
            available = [col for col in needed if col in df.columns]
            df = df[available]
            
            # Convert to numbers
            for col in ['CHANGE%', 'VOLUME', 'TRADES']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            return df
    except Exception as e:
        st.error(f"⚠️ Data issue: {str(e)[:200]}\nPlease refresh.")
        return pd.DataFrame()

stocks = fetch_nepse_data()

if stocks.empty or len(stocks) == 0:
    st.stop()

def agentic_score(row):
    mom_score = max(0, min(1, (row.get('CHANGE%', 0) + 2) / 5))
    vol_score = 1.0 if row.get('VOLUME', 0) > 15000 else row.get('VOLUME', 0) / 15000
    trade_score = 1.0 if row.get('TRADES', 0) > 100 else row.get('TRADES', 0) / 100
    total = round(0.5 * mom_score + 0.3 * vol_score + 0.2 * trade_score, 3)
    return max(0.23, min(0.95, total))

stocks['SCORE'] = stocks.apply(agentic_score, axis=1)
stocks['CONFIDENCE'] = np.where(stocks['SCORE'] > 0.55, 'High', 
                               np.where(stocks['SCORE'] > 0.40, 'Medium', 'Low'))
stocks['DIRECTION'] = 'LONG'

signals = stocks[stocks['SCORE'] >= 0.23].copy()
signals = signals.sort_values('SCORE', ascending=False).reset_index(drop=True)

def generate_note(row):
    if row.get('CHANGE%', 0) > 1.5:
        return f"Strong momentum (+{row.get('CHANGE%', 0):.2f}%) 🧠"
    elif row.get('VOLUME', 0) > 50000:
        return f"High volume spike detected 🧠"
    else:
        return f"Stable conservative signal 🧠"

signals['AGENT_NOTE'] = signals.apply(generate_note, axis=1)

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("📊 Live Agentic Signals")
    display_df = signals[['SYMBOL', 'LTP', 'CHANGE%', 'SCORE', 'CONFIDENCE', 'AGENT_NOTE']]
    styled = display_df.style.background_gradient(cmap='RdYlGn', subset=['SCORE', 'CHANGE%'])
    st.dataframe(styled, use_container_width=True, hide_index=True)

with col2:
    st.metric("Active Signals", len(signals))
    st.metric("Avg Score", f"{signals['SCORE'].mean():.3f}")
    st.success("✅ Live NEPSE Data")

if st.button("🔄 Refresh Live Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

st.caption("Your NEPSE Agentic Signals App • Educational only")
