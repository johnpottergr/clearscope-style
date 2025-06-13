import streamlit as st
import os
import time
import requests
from newspaper import Article
from docx import Document
from io import BytesIO
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Title and intro
st.title("AI-Powered Content Brief Generator")
st.markdown("""
- 🔍 Scrapes top-performing content for your keyword  
- ✍️ Summarizes the main themes using Gemini 1.5  
- 📋 Helps you plan your own content briefs fast  
""")

# User input
keyword = st.text_input("Enter a keyword:")
num_results = 5  # fixed at 5 to avoid rate issues

# DataForSEO login info
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Get URLs from DataForSEO
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

# Scrape content from page
def get_article_text(url):
    article = Article(url)
    try:
        article.download()
        article.parse()
        return article.text
    except:
        return ""

# Generate summary using Gemini
def summarize_with_gemini(text):
    prompt = f"Summarize the key points and topics from the following article:\n\n{text[:3000]}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini error: {e}"

# Create .docx from list of summaries
def generate_docx(summaries):
    doc = Document()
    doc.add_heading("AI-Powered Content Brief", 0)
    for url, content in summaries:
        doc.add_heading(url, level=2)
        doc.add_paragraph(content)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Main run logic
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
                summary = summarize_with_gemini(content)
                st.write("🧠 Gemini returned:", summary)  # Debug log
                if summary.strip():
                    summaries.append((url, summary))
                    with st.expander(f"✅ Done: {url}", expanded=True):
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
        else:
            st.warning("No summaries were generated. Check Gemini responses above.")
