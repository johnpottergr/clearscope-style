import streamlit as st
import os
import openai
import requests
from newspaper import Article

# Load API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

st.title("AI-Powered Content Brief Generator")
st.markdown("""
- 🔍 Scrapes top-performing content for your keyword  
- ✍️ Summarizes the main themes using GPT  
- 📋 Helps you plan your own content briefs fast  
""")

# User input
keyword = st.text_input("Enter a keyword:")
num_results = st.slider("How many results to analyze?", 1, 10, 3)

# Fetch SERP results from DataForSEO
def get_serp_results(keyword, num_results):
    endpoint = "https://api.dataforseo.com/v3/serp/google/organic/live/regular"
    payload = {
        "location_code": 2840,  # US location code
        "language_code": "en",
        "keyword": keyword,
        "limit": num_results
    }

    response = requests.post(endpoint, auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD), json=[payload])
    data = response.json()

    try:
        items = data["tasks"][0]["result"][0]["items"]
        return [item["url"] for item in items if "url" in item]
    except Exception as e:
        st.error(f"Error parsing SERP results: {e}")
        return []

# Scrape article content
def get_article_text(url):
    article = Article(url)
    try:
        article.download()
        article.parse()
        return article.text
    except:
        return ""

# Summarize with GPT
def summarize_with_gpt(text):
    prompt = f"Summarize the key points and topics from the following article:\n\n{text[:4000]}"
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

# Run analysis
if keyword:
    with st.spinner("Generating content brief..."):
        urls = get_serp_results(keyword, num_results)
        full_summary = ""
        for url in urls:
            st.write(f"🔗 Analyzing: {url}")
            content = get_article_text(url)
            if content:
                summary = summarize_with_gpt(content)
                full_summary += f"\n\n### {url}\n{summary}\n"
        st.markdown(full_summary)



