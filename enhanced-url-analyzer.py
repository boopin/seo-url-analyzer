import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import re
import time
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from textstat import flesch_reading_ease

# Pre-download NLTK data and set the path
nltk_data_path = "./nltk_data"
nltk.data.path.append(nltk_data_path)

# Check and download NLTK data only if not already present
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", download_dir=nltk_data_path)

try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords", download_dir=nltk_data_path)

def get_load_time(url):
    """Measure page load time"""
    try:
        start_time = time.time()
        requests.get(url, timeout=10)
        end_time = time.time()
        return round((end_time - start_time) * 1000)  # Convert to milliseconds
    except Exception:
        return None

def extract_keywords(text, num_keywords=20):
    """Extract most common keywords from text"""
    stop_words = set(stopwords.words("english")) | set(punctuation)
    words = [word.lower() for word in word_tokenize(text) if word.lower() not in stop_words and word.isalnum()]
    word_counts = Counter(words)
    return dict(word_counts.most_common(num_keywords))

def main():
    st.set_page_config(page_title="Enhanced SEO Content Analyzer", layout="wide")
    st.title("Enhanced SEO Content Analyzer")

    # Input for URLs
    urls_input = st.text_area("Enter URLs (one per line, max 10)", height=200)
    urls = [url.strip() for url in urls_input.split("\n") if url.strip()]

    if st.button("Analyze URLs"):
        if urls:
            if len(urls) > 10:
                st.warning("Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
                urls = urls[:10]

            results = []
            progress_bar = st.progress(0)

            for i, url in enumerate(urls):
                progress_bar.progress((i + 1) / len(urls))
                try:
                    load_time = get_load_time(url)
                    results.append({"URL": url, "Load Time (ms)": load_time if load_time else "Error"})
                except Exception as e:
                    results.append({"URL": url, "Load Time (ms)": f"Error: {str(e)}"})

            # Display results
            df = pd.DataFrame(results)
            st.write(df)

            # Export results as CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results", csv, "results.csv", "text/csv")

if __name__ == "__main__":
    main()
