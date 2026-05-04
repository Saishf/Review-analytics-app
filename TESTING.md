# Testing Guide

## 1. Demo Mode Test

Use this test first. It does not spend SerpAPI credits.

1. Run the app:

```powershell
python -m streamlit run app.py
```

2. Open the Streamlit URL, usually:

```text
http://localhost:8501
```

3. Keep `Use demo mode` turned on.
4. Click `Run analysis`.
5. Confirm these things appear:

- Listings analyzed: 10
- Total reviews scanned: 1200
- Highest estimated revenue metric
- Overview revenue chart
- Customer Criteria tab has purchase criteria, pain points, likes, dislikes
- Competitor Comparison tab has 10 rows
- Export tab downloads a CSV

## 2. Live API Test

This spends SerpAPI searches, so only run it once or twice.

1. Create a `.env` file in the project folder:

```env
SERPAPI_KEY=your_real_serpapi_key
GROQ_API_KEY=your_real_groq_key
```

2. Stop Streamlit with `Ctrl + C`.
3. Restart:

```powershell
python -m streamlit run app.py
```

4. Paste an Amazon product URL or ASIN.
5. Turn `Use demo mode` off.
6. Click `Run analysis`.
7. Confirm the app shows real product titles and Groq-generated insights.

## 3. Recommended Video Test Flow

For the assignment video:

1. Start in demo mode.
2. Show the dashboard and all tabs.
3. Explain demo mode saves free-tier API credits.
4. Show the `.env.example` file to prove SerpAPI + Groq support.
5. Optionally run one live test if you want to prove the API path.

## 4. Common Fixes

If you see `ModuleNotFoundError`, run:

```powershell
python -m pip install --user -r requirements.txt
```

If the app opens on another port like `8502`, use that URL. Streamlit changes ports when another Streamlit server is already running.
