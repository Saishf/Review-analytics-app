# Free Deployment Guide

The easiest free deployment is Streamlit Community Cloud.

## 1. Push Code To GitHub

From this project folder:

```powershell
git init
git add .
git commit -m "Build Amazon review analytics app"
git branch -M main
git remote add origin YOUR_PUBLIC_GITHUB_REPO_URL
git push -u origin main
```

## 2. Deploy On Streamlit Cloud

1. Go to:

```text
https://share.streamlit.io/
```

2. Sign in with GitHub.
3. Click `New app`.
4. Select your public GitHub repo.
5. Set:

```text
Branch: main
Main file path: app.py
```

6. Click `Deploy`.

## 3. Add API Keys

In Streamlit Cloud:

1. Open your deployed app settings.
2. Go to `Secrets`.
3. Add:

```toml
SERPAPI_KEY = "your_serpapi_key_here"
GROQ_API_KEY = "your_groq_api_key_here"
```

4. Save and reboot the app.

## 4. Submission Links

Submit:

- 3-minute video
- public GitHub repo link
- deployed Streamlit app link

## Important

Do not push a `.env` file to GitHub. The `.gitignore` already blocks it.

Use demo mode during recording if you want to avoid spending SerpAPI credits.
