import streamlit as st
import os
import time
import requests
from newspaper import Article
from docx import Document
from io import BytesIO
import google.generativeai as genai

# Set Gemini API key and model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

st.title("AI-Powered Content Brief Generator")
st.markdown("""
- 🔍 Scrapes top-performing content for your keyword  
- ✍️ Summarizes the main themes using Gemini 1.5  
- 📋 Helps you plan your own content briefs fast  
""")

# User input
keyword = st.text_input("Enter a keyword:")
num_results = 5

# DataForSEO credentials
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

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

# Summarize with Gemini
def summarize_with_gemini(text):
    prompt = f"Summarize the key points and topics from the following article:\n\n{text[:3000]}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini error: {e}"

# Generate .docx file
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

# Run main logic
summaries = []

if keyword:
    with st.spinner("Generating content brief..."):
        st.info(f"Analyzing the top {num_results} search results for '{keyword}'...")
        urls = get_serp_results(keyword, num_results)

        for url in urls:
            if "wikipedia.org" in url:
                st.write(f"⚠️ Skipping Wikipedia link: {url}")
                continue

            st.write(f"🔗 Analyzing: {url}")
            content = get_article_text(url)
            if content:
                summary = summarize_with_gemini(content)
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

# Fallback test if summaries are empty
if keyword and not summaries:
    st.warning("No summaries were generated. Running test prompt to check Gemini...")

    test_text = "Project management is the practice of initiating, planning, executing, controlling, and closing the work of a team to achieve specific goals."

    test_prompt = f"Summarize the key points from the following:\n\n{test_text}"
    try:
        response = model.generate_content(test_prompt)
        st.markdown("### 🔍 Gemini test summary:")
        st.write(response.text)
    except Exception as e:
        st.error(f"⚠️ Gemini test failed: {repr(e)}")
