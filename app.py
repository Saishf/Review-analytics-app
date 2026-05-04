import os
import re
import json
from dataclasses import dataclass
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
USD_TO_INR = 93.0


def to_inr(value: float) -> float:
    return value * USD_TO_INR


def value_to_inr(value: float, currency: str) -> float:
    return value if currency == "INR" else to_inr(value)


def format_inr(value: float, currency: str = "USD") -> str:
    return f"₹{value_to_inr(value, currency):,.0f}"


def format_inr_precise(value: float, currency: str = "USD") -> str:
    return f"₹{value_to_inr(value, currency):,.2f}"


@dataclass
class Product:
    asin: str
    title: str
    brand: str
    price: float
    rating: float
    reviews_count: int
    monthly_sales: int
    image: str
    url: str
    reviews: list[str]
    currency: str = "USD"

    @property
    def monthly_revenue(self) -> float:
        return self.price * self.monthly_sales


DEMO_REVIEW_THEMES = [
    "The product works well and feels durable, but the instructions were confusing at first.",
    "I bought this because the price was better than similar brands. Setup took only five minutes.",
    "Quality is good for daily use. Packaging was neat and delivery was fast.",
    "The main issue is that the size is slightly smaller than expected. Still useful though.",
    "Customer support responded quickly when I had a question. That made me trust the brand.",
    "I like the design and finish. It looks premium for the price.",
    "It stopped working once, but after reconnecting it worked again. Reliability could improve.",
    "Good value if you need something simple. Not the most advanced option.",
    "The product description should be clearer about what is included in the box.",
    "I compared several competitors and picked this one because reviews mentioned durability.",
]


def expanded_demo_reviews(product_name: str, count: int = 120) -> list[str]:
    reviews = []
    for index in range(count):
        theme = DEMO_REVIEW_THEMES[index % len(DEMO_REVIEW_THEMES)]
        reviews.append(f"{theme} Product: {product_name}. Review sample #{index + 1}.")
    return reviews


def parse_asin(raw: str) -> str:
    raw = raw.strip()
    if re.fullmatch(r"[A-Z0-9]{10}", raw, flags=re.IGNORECASE):
        return raw.upper()

    patterns = [
        r"/dp/([A-Z0-9]{10})",
        r"/gp/product/([A-Z0-9]{10})",
        r"/product/([A-Z0-9]{10})",
        r"asin=([A-Z0-9]{10})",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return raw[:10].upper() or "B0DEMO0001"


def title_hint_from_url(raw: str) -> str | None:
    match = re.search(r"amazon\.[^/]+/([^/?#]+)/dp/[A-Z0-9]{10}", raw, flags=re.IGNORECASE)
    if not match:
        return None
    slug = requests.utils.unquote(match.group(1))
    title = re.sub(r"[-_]+", " ", slug).strip()
    return title if len(title) > 4 else None


def amazon_domain_from_input(raw: str) -> str:
    match = re.search(r"amazon\.([a-z.]+)", raw, flags=re.IGNORECASE)
    if not match:
        return "amazon.com"
    suffix = match.group(1).lower()
    supported = {"com", "in", "co.uk", "ca", "de", "fr", "it", "es", "com.au", "co.jp"}
    return f"amazon.{suffix}" if suffix in supported else "amazon.com"


def currency_for_domain(domain: str) -> str:
    return "INR" if domain == "amazon.in" else "USD"


def serpapi_get(params: dict[str, Any]) -> dict[str, Any]:
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_KEY is not configured.")
    last_error: Exception | None = None
    for _ in range(2):
        try:
            response = requests.get(
                "https://serpapi.com/search.json",
                params={**params, "api_key": SERPAPI_KEY},
                timeout=90,
            )
            break
        except requests.Timeout as error:
            last_error = error
    else:
        raise RuntimeError(f"SerpAPI timed out after retrying: {last_error}")
    if response.status_code >= 400:
        try:
            detail = response.json().get("error") or response.text[:300]
        except Exception:
            detail = response.text[:300]
        raise RuntimeError(f"SerpAPI returned HTTP {response.status_code}: {detail}")
    data = response.json()
    if data.get("error"):
        raise RuntimeError(str(data["error"]))
    return data


def safe_price(raw: Any, fallback: float) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    if not raw:
        return fallback
    match = re.search(r"[\d,.]+", str(raw))
    return float(match.group(0).replace(",", "")) if match else fallback


def safe_int(raw: Any, fallback: int) -> int:
    if isinstance(raw, int):
        return raw
    if not raw:
        return fallback
    match = re.search(r"[\d,]+", str(raw))
    return int(match.group(0).replace(",", "")) if match else fallback


def estimate_monthly_sales(rating_count: int, rating: float, rank_hint: int | None = None) -> int:
    base = max(30, int(rating_count * 0.08))
    rating_boost = 1 + max(0, rating - 3.5) * 0.18
    rank_boost = 1
    if rank_hint:
        rank_boost = max(0.35, min(2.5, 75000 / max(rank_hint, 1000)))
    return int(base * rating_boost * rank_boost)


def bought_last_month_to_sales(raw: Any) -> int | None:
    if not raw:
        return None
    text = str(raw).lower().replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*k?\+", text)
    if not match:
        return None
    value = float(match.group(1))
    if "k" in text:
        value *= 1000
    return int(value)


def reviews_from_product_data(data: dict[str, Any], asin: str, max_reviews: int = 120) -> list[str]:
    reviews_info = data.get("reviews_information", {}) or {}
    reviews: list[str] = []

    summary = reviews_info.get("summary", {})
    if isinstance(summary, dict) and summary.get("text"):
        reviews.append(str(summary["text"]))

    for insight in summary.get("insights", []) if isinstance(summary, dict) else []:
        if isinstance(insight, dict):
            text = insight.get("text") or insight.get("title")
            if text:
                reviews.append(str(text))
        elif insight:
            reviews.append(str(insight))

    for review in reviews_info.get("authors_reviews", []) or []:
        if isinstance(review, dict):
            body = review.get("text") or review.get("review") or review.get("title")
            if body:
                reviews.append(str(body))

    product = data.get("product_results", {}) or {}
    for item in product.get("about_item", []) or []:
        reviews.append(f"Product claim: {item}")

    return reviews[:max_reviews] or expanded_demo_reviews(f"Product {asin}", max_reviews)


def fetch_product_serpapi(asin: str, amazon_domain: str = "amazon.com") -> Product:
    data = serpapi_get(
        {
            "engine": "amazon_product",
            "amazon_domain": amazon_domain,
            "asin": asin,
        }
    )
    product = data.get("product_results", {})
    reviews_info = data.get("reviews_information", {})
    title = product.get("title") or f"Amazon Product {asin}"
    price = safe_price(
        product.get("extracted_price")
        or product.get("price")
        or product.get("buybox_winner", {}).get("extracted_price")
        or product.get("buybox_winner", {}).get("price"),
        39.99,
    )
    rating = float(product.get("rating") or reviews_info.get("rating") or 4.2)
    reviews_count = safe_int(
        product.get("ratings_total")
        or product.get("reviews")
        or reviews_info.get("reviews_count")
        or reviews_info.get("ratings_count"),
        1200,
    )
    monthly_sales = bought_last_month_to_sales(product.get("bought_last_month")) or estimate_monthly_sales(reviews_count, rating)

    return Product(
        asin=asin,
        title=title,
        brand=product.get("brand") or product.get("manufacturer") or "Unknown",
        price=price,
        rating=rating,
        reviews_count=reviews_count,
        monthly_sales=monthly_sales,
        image=product.get("thumbnail") or product.get("images", [{}])[0].get("link", ""),
        url=f"https://www.{amazon_domain}/dp/{asin}",
        reviews=reviews_from_product_data(data, asin),
        currency=currency_for_domain(amazon_domain),
    )


def discover_competitors(query: str, seed_asin: str, amazon_domain: str = "amazon.com", limit: int = 9) -> list[str]:
    asins: list[str] = []
    data = serpapi_get(
        {
            "engine": "amazon",
            "amazon_domain": amazon_domain,
            "k": query[:90],
        }
    )
    for item in data.get("organic_results", []):
        asin = item.get("asin")
        if asin and asin != seed_asin and asin not in asins:
            asins.append(asin)
    return asins[:limit]


def demo_products(
    seed_asin: str,
    target_title: str | None = None,
    currency: str = "USD",
    amazon_domain: str = "amazon.com",
) -> list[Product]:
    names = [
        target_title or "PrimePick Pro Organizer",
        "NexaHome Compact Kit",
        "UrbanEase Daily Essential",
        "BrightNest Premium Set",
        "ValueMax Everyday Pack",
        "CoreCraft Durable Model",
        "SwiftUse Smart Edition",
        "AlphaBay Best Seller",
        "HomeAxis Starter Bundle",
        "ClearChoice Plus",
    ]
    brands = ["PrimePick", "NexaHome", "UrbanEase", "BrightNest", "ValueMax", "CoreCraft", "SwiftUse", "AlphaBay", "HomeAxis", "ClearChoice"]
    products: list[Product] = []
    for i, name in enumerate(names):
        price = [29.99, 34.99, 24.49, 39.99, 19.99, 44.5, 31.25, 27.99, 36.75, 41.99][i]
        rating = [4.5, 4.2, 4.0, 4.7, 3.9, 4.4, 4.1, 4.6, 4.3, 4.2][i]
        reviews = [4200, 2800, 1900, 5100, 1250, 3600, 2300, 6100, 3100, 2700][i]
        monthly_sales = estimate_monthly_sales(reviews, rating) + (i * 37)
        demo_asin = seed_asin if i == 0 else f"B0DEMO{i:04d}"
        demo_url = (
            f"https://www.{amazon_domain}/dp/{seed_asin}"
            if i == 0 and not seed_asin.startswith("B0DEMO")
            else f"https://www.{amazon_domain}/s?k={requests.utils.quote(name)}"
        )
        products.append(
            Product(
                asin=demo_asin,
                title=name,
                brand=brands[i],
                price=price,
                rating=rating,
                reviews_count=reviews,
                monthly_sales=monthly_sales,
                image="",
                url=demo_url,
                reviews=expanded_demo_reviews(name, 120),
                currency=currency,
            )
        )
    return products


def heuristic_analysis(products: list[Product]) -> dict[str, Any]:
    all_reviews = " ".join(review.lower() for product in products for review in product.reviews)
    criteria = [
        ("Price / value for money", ["price", "value", "deal", "expensive", "cheap"]),
        ("Durability and reliability", ["durable", "stopped", "reliable", "quality", "working"]),
        ("Ease of setup and use", ["setup", "easy", "simple", "instructions", "confusing"]),
        ("Accurate sizing and description", ["size", "smaller", "description", "included", "box"]),
        ("Brand trust and support", ["support", "trust", "responded", "brand", "service"]),
    ]
    scored = []
    for label, terms in criteria:
        score = sum(all_reviews.count(term) for term in terms)
        scored.append(
            {
                "criterion": label,
                "importance_score": min(100, 45 + score * 7),
                "evidence": f"Mentions detected for: {', '.join(terms)}",
            }
        )
    scored = sorted(scored, key=lambda item: item["importance_score"], reverse=True)
    return {
        "purchase_criteria": scored,
        "pain_points": [
            "Confusing or incomplete product instructions",
            "Mismatch between expected and actual size or contents",
            "Reliability concerns after repeated use",
        ],
        "likes": [
            "Good value compared with competitors",
            "Premium look and useful design",
            "Fast setup and delivery experience",
        ],
        "dislikes": [
            "Product description does not answer all pre-purchase questions",
            "Some buyers worry about long-term reliability",
            "Certain customers expect larger size or more accessories",
        ],
        "positioning_advice": [
            "Highlight durability proof and warranty near the top of the listing.",
            "Add clearer size photos, box contents, and setup instructions.",
            "Compete on value by showing side-by-side feature comparison.",
        ],
    }


def groq_analysis(products: list[Product]) -> dict[str, Any]:
    fallback = heuristic_analysis(products)
    if not GROQ_API_KEY:
        return fallback

    review_payload = "\n".join(
        f"[{product.title}] {review}"
        for product in products
        for review in product.reviews[:35]
    )
    prompt = f"""
Analyze these Amazon review snippets for an ecommerce seller.

Return valid JSON only, with exactly these keys:
purchase_criteria: array of objects with criterion, importance_score, evidence
pain_points: array of strings
likes: array of strings
dislikes: array of strings
positioning_advice: array of strings

Focus on customer buying criteria, objections, quality issues, value perception,
competitor positioning, and listing improvements.

Reviews:
{review_payload[:18000]}
"""
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a precise ecommerce review analyst. Return JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 1400,
            },
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"] or "{}"
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        return json.loads(match.group(0) if match else content)
    except Exception:
        return fallback


def build_products(input_value: str, manual_competitors: str, force_demo: bool) -> tuple[list[Product], bool, str]:
    asin = parse_asin(input_value)
    title_hint = title_hint_from_url(input_value)
    amazon_domain = amazon_domain_from_input(input_value)
    currency = currency_for_domain(amazon_domain)
    if force_demo:
        return demo_products(asin, title_hint, currency, amazon_domain), True, "Demo mode is turned on."
    if not SERPAPI_KEY:
        return demo_products(asin, title_hint, currency, amazon_domain), True, "SERPAPI_KEY was not found. Check your .env file and restart Streamlit."

    try:
        base = fetch_product_serpapi(asin, amazon_domain)
        competitor_asins = [
            parse_asin(line)
            for line in manual_competitors.splitlines()
            if line.strip()
        ]
        if not competitor_asins:
            competitor_asins = discover_competitors(base.title, asin, amazon_domain)
        products = [base]
        for comp_asin in competitor_asins[:4]:
            try:
                products.append(fetch_product_serpapi(comp_asin, amazon_domain))
            except Exception:
                continue
        if len(products) < 10:
            demo_fillers = demo_products(asin, title_hint, currency, amazon_domain)
            for demo_product in demo_fillers:
                if len(products) >= 10:
                    break
                if demo_product.asin not in {product.asin for product in products}:
                    products.append(demo_product)
        if len(products) == 1:
            return products, False, "Live SerpAPI product data loaded. Competitor discovery did not return extra listings."
        return products, False, "Live SerpAPI data loaded. Demo competitors fill any missing slots to save API credits."
    except Exception as error:
        return demo_products(asin, title_hint, currency, amazon_domain), True, f"Live API request failed, so demo data was used. Reason: {error}"


def product_frame(products: list[Product]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ASIN": product.asin,
                "Listing": product.title,
                "Brand": product.brand,
                "Price": product.price,
                "Price (INR est.)": value_to_inr(product.price, product.currency),
                "Rating": product.rating,
                "Reviews": product.reviews_count,
                "Estimated Monthly Sales": product.monthly_sales,
                "Estimated Monthly Revenue": product.monthly_revenue,
                "Estimated Monthly Revenue (INR est.)": value_to_inr(product.monthly_revenue, product.currency),
                "URL": product.url,
            }
            for product in products
        ]
    )


st.set_page_config(page_title="Amazon Review Analytics", page_icon=":chart_with_upwards_trend:", layout="wide")

st.title("Amazon Review Analytics")
st.caption("Analyze one Amazon listing against 9 competitors using review mining, AI insights, and revenue estimates.")
st.caption(f"Amazon.in prices are shown as INR. Amazon.com prices are converted using ₹{USD_TO_INR:.0f} per $1.")

with st.sidebar:
    st.header("Analyze")
    input_value = st.text_input("Amazon URL or ASIN", value="B0DEMO0001")
    manual_competitors = st.text_area(
        "Competitor URLs / ASINs, one per line",
        height=150,
        placeholder="Optional. Leave empty to try free Amazon search-page discovery.",
    )
    force_demo = st.toggle("Use demo mode", value=not bool(SERPAPI_KEY))
    run = st.button("Run analysis", type="primary", use_container_width=True)
    st.divider()
    st.write("API status")
    st.write(f"SerpAPI: {'configured' if SERPAPI_KEY else 'demo fallback'}")
    st.write(f"Groq: {'configured' if GROQ_API_KEY else 'heuristic fallback'}")
    st.write("Streamlit + Plotly: dashboard")


if "products" not in st.session_state:
    st.session_state.products = demo_products("B0DEMO0001")
    st.session_state.used_demo = True
    st.session_state.demo_reason = "Initial sample dashboard."
    st.session_state.analysis = heuristic_analysis(st.session_state.products)

if run:
    with st.spinner("Collecting listings, reviews, competitors, and building insights..."):
        products, used_demo, demo_reason = build_products(input_value, manual_competitors, force_demo)
        st.session_state.products = products
        st.session_state.used_demo = used_demo
        st.session_state.demo_reason = demo_reason
        st.session_state.analysis = groq_analysis(products)

products = st.session_state.products
analysis = st.session_state.analysis
df = product_frame(products)

if st.session_state.used_demo:
    st.info(f"Running in demo mode. {st.session_state.demo_reason}")
else:
    st.success(st.session_state.demo_reason)

summary_cols = st.columns(4)
summary_cols[0].metric("Listings analyzed", len(products))
summary_cols[1].metric("Total reviews scanned", sum(len(product.reviews) for product in products))
summary_cols[2].metric("Highest est. revenue", f"₹{df['Estimated Monthly Revenue (INR est.)'].max():,.0f}")
summary_cols[3].metric("Avg rating", f"{df['Rating'].mean():.2f}")

target = products[0]
with st.container(border=True):
    st.subheader("Target Listing")
    target_cols = st.columns([2.0, 1.0, 0.7, 1.2])
    with target_cols[0]:
        st.write(target.title)
        st.caption(f"ASIN: {target.asin} | Brand: {target.brand}")
    with target_cols[1]:
        st.caption("Price")
        st.write(f"**{format_inr_precise(target.price, target.currency)}**")
    with target_cols[2]:
        st.caption("Rating")
        st.write(f"**{target.rating:.1f}**")
    with target_cols[3]:
        st.caption("Est. Revenue")
        st.write(f"**{format_inr(target.monthly_revenue, target.currency)}/mo**")
    st.link_button("Open your pasted listing", target.url)

tab_overview, tab_insights, tab_compare, tab_export = st.tabs(
    ["Overview", "Customer Criteria", "Competitor Comparison", "Export"]
)

with tab_overview:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Estimated Monthly Revenue")
        chart_df = df.sort_values("Estimated Monthly Revenue (INR est.)", ascending=True)
        fig = px.bar(
            chart_df,
            x="Estimated Monthly Revenue (INR est.)",
            y="Listing",
            orientation="h",
            color="Rating",
            color_continuous_scale="Tealrose",
        )
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Winning Listing")
        st.caption("This is the listing with the highest estimated monthly revenue, so it can be a competitor.")
        winner = df.sort_values("Estimated Monthly Revenue (INR est.)", ascending=False).iloc[0]
        st.metric("Revenue", f"₹{winner['Estimated Monthly Revenue (INR est.)']:,.0f}/mo")
        st.write(winner["Listing"])
        st.write(f"Rating: {winner['Rating']} | Reviews: {winner['Reviews']:,} | Price: ₹{winner['Price (INR est.)']:,.2f}")
        st.link_button("Open winning listing", winner["URL"])

with tab_insights:
    st.subheader("Key Purchase Criteria")
    criteria_df = pd.DataFrame(analysis.get("purchase_criteria", []))
    if not criteria_df.empty:
        st.dataframe(criteria_df, hide_index=True, use_container_width=True)
    insight_cols = st.columns(3)
    with insight_cols[0]:
        st.subheader("Pain Points")
        for item in analysis.get("pain_points", []):
            st.write(f"- {item}")
    with insight_cols[1]:
        st.subheader("What Buyers Like")
        for item in analysis.get("likes", []):
            st.write(f"- {item}")
    with insight_cols[2]:
        st.subheader("What Buyers Dislike")
        for item in analysis.get("dislikes", []):
            st.write(f"- {item}")
    st.subheader("Listing Strategy")
    for item in analysis.get("positioning_advice", []):
        st.write(f"- {item}")

with tab_compare:
    st.subheader("Listing Comparison")
    st.dataframe(
        df[
            [
                "ASIN",
                "Listing",
                "Brand",
                "Price (INR est.)",
                "Rating",
                "Reviews",
                "Estimated Monthly Sales",
                "Estimated Monthly Revenue (INR est.)",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
    scatter = px.scatter(
        df,
        x="Price (INR est.)",
        y="Rating",
        size="Estimated Monthly Revenue (INR est.)",
        hover_name="Listing",
        color="Reviews",
        title="Price vs Rating vs Revenue",
    )
    st.plotly_chart(scatter, use_container_width=True)

with tab_export:
    st.subheader("Export Report")
    st.download_button(
        "Download competitor CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="amazon_review_analytics.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.json(analysis)
