# -*- coding: utf-8 -*-
"""
Created on Tue Sep  2 19:05:57 2025

@author: archit
"""

import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta

st.set_page_config(page_title="Google News — API Dashboard", layout="wide")
st.title("Google News — Streamlit + FastAPI Demo")
st.caption("Frontend powered by Streamlit, backend powered by FastAPI.")

with st.sidebar:
    st.header("Search")
    query = st.text_input("Query", value="OpenAI OR ChatGPT")
    col_lang, col_region = st.columns(2)
    with col_lang:
        lang = st.selectbox("Language", ["en-US","en-GB","nl-NL","de-DE","fr-FR","hi-IN"], index=0)
    with col_region:
        region = st.selectbox("Region", ["US","GB","NL","DE","FR","IN"], index=0)

    st.header("Dates")
    today = date.today()
    default_start = today - timedelta(days=7)
    start_date, end_date = st.date_input("Date range", (default_start, today), format="YYYY-MM-DD")

    st.header("Options")
    per_day_cap = st.number_input("Max items per day (0 = unlimited)", 0, 200, 50, 10)

    st.header("Backend API")
    api_base = st.text_input("FastAPI base URL", "http://localhost:8000")

    run = st.button("Fetch")

def fetch_from_api(base, query, start, end, lang, region, cap):
    params = {
        "query": query,
        "start": pd.to_datetime(start).date().isoformat(),
        "end": pd.to_datetime(end).date().isoformat(),
        "lang": lang,
        "region": region,
        "per_day_cap": None if cap == 0 else int(cap)
    }
    r = requests.get(f"{base}/gnews", params=params, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())

placeholder = st.empty()
if run:
    with st.spinner("Calling FastAPI backend…"):
        df = fetch_from_api(api_base, query, start_date, end_date, lang, region, per_day_cap)
    if df.empty:
        st.warning("No results.")
    else:
        st.subheader("Results")
        st.data_editor(
            df[["date", "headline", "link"]],
            hide_index=True,
            use_container_width=True,
            column_config={"link": st.column_config.LinkColumn("link", display_text="open")},
            disabled=True
        )
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv, file_name="gnews_results.csv", mime="text/csv")
else:
    placeholder.info("Set your query and dates on the left, then hit **Fetch**.")
