import streamlit as st
import os
import time
from openai import OpenAI, RateLimitError
import requests
from newspaper import Article
from docx import Document
from io import BytesIO

# Load API keys
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
num_results = 5

# Fetch SERP results from DataForSEO
def get_serp_results(keyword, num_results):
    endpoint = "https://api.dataforseo.com/v3/serp/google/organic/live/regular"
    payload = {
        "location_code": 2840,
        "language_code": "en",
        "keyword": keyword,
        "limit": num_results
    }

    response = requests.post(endpoint, auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD), json=[payload])
    data = response.json()

    try:
        items = data["tasks"][0]["result"][0]["items"]
        return [item["url"] for item in items if "url" in item][:num_results]
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

# Summarize with GPT (with retry logic)
def summarize_with_gpt(text):
    prompt = f"Summarize the key points and topics from the following article:\n\n{text[:3000]}"
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            time.sleep(30)  # Option A: wait longer before retrying
    return "⚠️ OpenAI rate limit exceeded after multiple retries."

# Run analysis
def generate_docx(summaries):
    doc = Document()
    doc.add_heading("AI-Powered Content Brief", 0)
    for summary in summaries:
        url, content = summary
        doc.add_heading(url, level=2)
        doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
    
if keyword:
    with st.spinner("Generating content brief..."):
        st.info(f"Analyzing the top {num_results} search results for '{keyword}'...")
        urls = get_serp_results(keyword, num_results)
        summaries = []

        for url in urls:
            if "wikipedia.org" in url:
                st.write(f"⚠️ Skipping Wikipedia link: {url}")
                continue

            st.write(f"🔗 Analyzing: {url}")
            content = get_article_text(url)
            if content:
                summary = summarize_with_gpt(content)
                summaries.append((url, summary))
                with st.expander(f"✅ Done: {url}", expanded=False):
                    st.write(summary)
                time.sleep(2)
        st.success("✅ Finished summarizing!")

        if summaries:
            docx_file = generate_docx(summaries)
            st.download_button(
                label="📥 Download all summaries (.docx)",
                data=docx_file,
                file_name="content_brief.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

