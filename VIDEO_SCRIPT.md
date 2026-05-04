# 3-Minute Demo Script

## 0:00 - 0:25 Intro

Hi, my name is [Your Name]. I study at [Your School], my CGPA is [Your CGPA], and my favorite accomplishment is [Your Accomplishment].

For this assignment, I built Amazon Review Analytics, a mini product that helps Amazon sellers understand why customers buy, what they complain about, and how their listing compares with competitors.

## 0:25 - 1:20 User Demo

Here I paste an Amazon product URL or ASIN.

The app analyzes my listing plus up to 9 competitors. It shows estimated monthly revenue, average rating, total reviews scanned, and a revenue chart.

In the Customer Criteria tab, I can see the top purchase criteria, customer pain points, what buyers like, what they dislike, and recommended listing strategy.

In the Competitor Comparison tab, I can compare price, rating, review count, estimated monthly sales, and estimated monthly revenue.

Finally, I can export the report as a CSV.

## 1:20 - 2:05 Why I Designed It This Way

I designed it from the seller's perspective. A seller does not just need raw reviews. They need fast business decisions:

- What matters most to customers?
- Why do customers choose competitors?
- What should I improve in my listing?
- Which competitors look strongest?

That is why the dashboard focuses on insights, comparison, and revenue instead of only showing scraped text.

## 2:05 - 2:35 How It Works

The app extracts the ASIN from the Amazon URL.

It uses SerpAPI to fetch Amazon product pages, review pages, and competitor search results.

Then it sends review snippets to Groq, which runs an LLM and summarizes review themes into purchase criteria, pain points, likes, dislikes, and listing strategy.

If API keys are not available or I want to save free-tier credits, it runs in demo mode with realistic sample data, so the product can still be tested.

## 2:35 - 2:50 APIs / Tools Used

I used SerpAPI for Amazon listing, competitor, and review data.

I used Groq for fast LLM analysis on the free tier.

I also used Streamlit for the app interface and Plotly for the visual charts.

## 2:50 - 3:00 Future Work

With more time, I would add Keepa for more accurate sales estimates, historical tracking, more marketplaces, saved projects, and automatic weekly competitor alerts.
