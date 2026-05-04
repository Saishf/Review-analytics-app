# Amazon Review Analytics

A runnable mini product for analyzing an Amazon listing and competitor products.

It accepts an Amazon product URL or ASIN, collects product and review signals, identifies customer purchase criteria, compares competitors, and estimates monthly revenue.

## Features

- Amazon listing input by URL or ASIN
- 9 competitor discovery slots
- Review analytics for pain points, likes, dislikes, and purchase criteria
- Competitor comparison table
- Monthly revenue estimate per listing
- CSV export for reports
- Demo mode with realistic sample data when Amazon blocks live scraping

## APIs / Tools Used

- SerpAPI for Amazon product, competitor, and review data
- Groq API for LLM review summarization and customer criteria extraction
- Streamlit for the interactive app
- Plotly for charts

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run:

```bash
streamlit run app.py
```

Create a `.env` file:

```env
SERPAPI_KEY=your_serpapi_key_here
GROQ_API_KEY=your_groq_api_key_here
```

Both can be used with free-tier keys. Demo mode is included so you can record the project without spending SerpAPI searches.

## Video Guide

Cover these points in your 3-minute video:

1. Introduce yourself: name, school, CGPA, favorite accomplishment.
2. Paste an Amazon URL and run the analysis.
3. Show the dashboard from the user's perspective.
4. Explain that it uses SerpAPI for Amazon data and Groq for LLM analysis.
5. Explain the design: quick business insights for Amazon sellers.
6. Mention future improvements: live Keepa revenue data, more marketplaces, historical tracking, and review topic clustering over time.
