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

def extract_meta_tags(soup):
    """Extract meta tags from the page"""
    meta_tags = {}
    meta_tags['title'] = soup.title.text.strip() if soup.title else ''
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_tags['description'] = meta_description['content'].strip() if meta_description else ''
    return meta_tags

def extract_headings(soup):
    """Extract all headings (H1-H6) from the page"""
    headings = []
    for i in range(1, 7):
        heading_tag = f'h{i}'
        for h in soup.find_all(heading_tag):
            headings.append({'level': heading_tag.upper(), 'text': h.text.strip()})
    return headings

def analyze_url(url):
    """Analyze the URL for SEO metrics"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    result = {
        'url': url,
        'status': 'Success',
        'load_time_ms': 0,
        'meta_title': '',
        'meta_description': '',
        'h1_count': 0,
        'h2_count': 0,
        'h3_count': 0,
        'readability_score': 0,
        'keywords': {},
        'headings': []
    }
    try:
        # Load time
        result['load_time_ms'] = get_load_time(url)

        # Fetch page content
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = ' '.join([p.text.strip() for p in soup.find_all(['p', 'div', 'span'])])

        # Meta tags
        meta_tags = extract_meta_tags(soup)
        result['meta_title'] = meta_tags.get('title', '')
        result['meta_description'] = meta_tags.get('description', '')

        # Headings
        headings = extract_headings(soup)
        result['headings'] = headings
        result['h1_count'] = sum(1 for h in headings if h['level'] == 'H1')
        result['h2_count'] = sum(1 for h in headings if h['level'] == 'H2')
        result['h3_count'] = sum(1 for h in headings if h['level'] == 'H3')

        # Readability
        result['readability_score'] = flesch_reading_ease(text_content)

        # Keywords
        result['keywords'] = extract_keywords(text_content)

    except Exception as e:
        result['status'] = f"Error: {str(e)}"

    return result

def main():
    st.set_page_config(page_title="Enhanced SEO Content Analyzer", layout="wide")
    st.title("Enhanced SEO Content Analyzer")

    # Input URLs
    urls_input = st.text_area("Enter URLs (one per line, max 10)", height=200)
    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]

    if st.button("Analyze URLs"):
        if urls:
            if len(urls) > 10:
                st.warning("Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
                urls = urls[:10]

            results = []
            headings_data = []
            progress_bar = st.progress(0)

            # Analyze each URL
            for i, url in enumerate(urls):
                progress_bar.progress((i + 1) / len(urls))
                result = analyze_url(url)
                results.append(result)

                # Collect headings
                for heading in result['headings']:
                    headings_data.append({'url': url, 'level': heading['level'], 'text': heading['text']})

            # Display results
            df = pd.DataFrame(results)
            st.dataframe(df[['url', 'status', 'load_time_ms', 'meta_title', 'meta_description', 'h1_count', 'h2_count', 'h3_count', 'readability_score']])

            # Export results
            st.subheader("Export Results")
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Main Analysis", csv, "seo_analysis.csv", "text/csv")

            # Export headings
            headings_df = pd.DataFrame(headings_data)
            headings_csv = headings_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Headings", headings_csv, "headings_analysis.csv", "text/csv")

if __name__ == "__main__":
    main()
