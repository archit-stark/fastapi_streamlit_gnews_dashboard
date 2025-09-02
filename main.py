# -*- coding: utf-8 -*-
"""
Created on Tue Sep  2 19:04:57 2025

@author: archit
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import quote_plus
import pandas as pd
import feedparser

app = FastAPI(title="GNews API", version="1.0.0")

def gnews_url(query: str, lang: str = "en-US", region: str = "US") -> str:
    return (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}&hl={lang}&gl={region}&ceid={region}:{lang.split('-')[0]}"
    )

def _parse_dt(entry) -> str:
    try:
        return pd.to_datetime(entry.published, utc=True).date().isoformat()
    except Exception:
        return pd.Timestamp.utcnow().date().isoformat()

class NewsItem(BaseModel):
    date: str
    headline: str
    link: str
    source: str

@app.get("/gnews", response_model=List[NewsItem])
def gnews(
    query: str = Query(..., description="Search query"),
    start: str = Query(..., description="YYYY-MM-DD inclusive"),
    end: str = Query(..., description="YYYY-MM-DD inclusive"),
    lang: str = "en-US",
    region: str = "US",
    per_day_cap: Optional[int] = 50,
):
    start_ts = pd.to_datetime(start)
    end_ts = pd.to_datetime(end) + pd.Timedelta(days=1)
    rows = []
    for day in pd.date_range(start_ts, end_ts, inclusive="left", freq="D"):
        after = day.strftime("%Y-%m-%d")
        before = (day + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        q = f"{query} after:{after} before:{before}"
        url = gnews_url(q, lang=lang, region=region)
        feed = feedparser.parse(url)
        for i, it in enumerate(feed.entries):
            if per_day_cap is not None and i >= per_day_cap:
                break
            title = (it.get("title") or "").strip()
            link  = (it.get("link")  or "").strip()
            if not title or not link:
                continue
            src = it.get("source", {})
            source = src.get("title") if isinstance(src, dict) else "news.google.com"
            rows.append({"date": _parse_dt(it), "headline": title, "link": link, "source": source})

    df = (pd.DataFrame(rows)
            .drop_duplicates(subset=["link"])
            .drop_duplicates(subset=["date", "headline"])
            .sort_values(["date", "source"]))
    return df.to_dict(orient="records")
