"""
Enhanced SEO Content Analyzer
Version: 2.5
Updated: January 2025
Description: Analyze webpages for SEO metrics, including meta tags, headings (H1-H6), links, and readability scores.
"""

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

def preprocess_url(url):
    """Ensure the URL has a valid scheme (http or https)"""
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url

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

def extract_internal_links(soup, base_url):
    """Extract internal links and their anchor texts"""
    internal_links = []
    domain = urlparse(base_url).netloc
    for a in soup.find_all('a', href=True):
        href = urljoin(base_url, a['href'])
        if urlparse(href).netloc == domain:
            anchor_text = a.text.strip()
            internal_links.append({'url': href, 'anchor_text': anchor_text})
    return internal_links

def extract_external_links(soup, base_url):
    """Extract external links and their anchor texts"""
    external_links = []
    domain = urlparse(base_url).netloc
    for a in soup.find_all('a', href=True):
        href = urljoin(base_url, a['href'])
        if urlparse(href).netloc != domain:
            anchor_text = a.text.strip()
            external_links.append({'url': href, 'anchor_text': anchor_text})
    return external_links

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
        'h4_count': 0,
        'h5_count': 0,
        'h6_count': 0,
        'word_count': 0,
        'readability_score': 0,
        'internal_links': [],
        'internal_link_count': 0,
        'external_links': [],
        'external_link_count': 0,
    }
    try:
        # Load time
        result['load_time_ms'] = get_load_time(url)

        # Fetch page content
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = ' '.join([p.text.strip() for p in soup.find_all(['p', 'div', 'span'])])

        # Word count
        result['word_count'] = len(text_content.split())

        # Readability score
        result['readability_score'] = flesch_reading_ease(text_content)

        # Meta tags
        meta_tags = extract_meta_tags(soup)
        result['meta_title'] = meta_tags.get('title', '')
        result['meta_description'] = meta_tags.get('description', '')

        # Headings
        result['headings'] = extract_headings(soup)
        result['h1_count'] = sum(1 for h in result['headings'] if h['level'] == 'H1')
        result['h2_count'] = sum(1 for h in result['headings'] if h['level'] == 'H2')
        result['h3_count'] = sum(1 for h in result['headings'] if h['level'] == 'H3')
        result['h4_count'] = sum(1 for h in result['headings'] if h['level'] == 'H4')
        result['h5_count'] = sum(1 for h in result['headings'] if h['level'] == 'H5')
        result['h6_count'] = sum(1 for h in result['headings'] if h['level'] == 'H6')

        # Internal links
        internal_links = extract_internal_links(soup, url)
        result['internal_links'] = internal_links
        result['internal_link_count'] = len(internal_links)

        # External links
        external_links = extract_external_links(soup, url)
        result['external_links'] = external_links
        result['external_link_count'] = len(external_links)

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
            # Preprocess URLs
            urls = [preprocess_url(url) for url in urls]
            
            if len(urls) > 10:
                st.warning("Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
                urls = urls[:10]

            results = []
            internal_links_data = []
            external_links_data = []
            headings_data = []
            progress_bar = st.progress(0)

            # Analyze each URL
            with st.spinner("Analyzing URLs..."):
                for i, url in enumerate(urls):
                    progress_bar.progress((i + 1) / len(urls))
                    result = analyze_url(url)
                    results.append(result)

                    # Collect internal links for export
                    for link in result.get('internal_links', []):
                        internal_links_data.append({'page_url': url, 'link_url': link['url'], 'anchor_text': link['anchor_text']})

                    # Collect external links for export
                    for link in result.get('external_links', []):
                        external_links_data.append({'page_url': url, 'link_url': link['url'], 'anchor_text': link['anchor_text']})

                    # Collect headings for export
                    for heading in result['headings']:
                        headings_data.append({'page_url': url, 'level': heading['level'], 'text': heading['text']})

            # Create DataFrame for main results
            df = pd.DataFrame(results)

            # Tabs for organized display
            tabs = st.tabs(["Summary", "Main Table", "Internal Links", "External Links", "Headings"])

            # Summary Tab
            with tabs[0]:
                st.subheader("Summary Statistics")
                summary = {
                    "Average Load Time (ms)": [df['load_time_ms'].mean()],
                    "Average Word Count": [df['word_count'].mean()],
                    "Average Internal Links": [df['internal_link_count'].mean()],
                    "Average External Links": [df['external_link_count'].mean()],
                    "Average Readability Score": [df['readability_score'].mean()],
                    "Average H1 Count": [df['h1_count'].mean()],
                    "Average H2 Count": [df['h2_count'].mean()],
                    "Average H3 Count": [df['h3_count'].mean()],
                    "Average H4 Count": [df['h4_count'].mean()],
                    "Average H5 Count": [df['h5_count'].mean()],
                    "Average H6 Count": [df['h6_count'].mean()],
                    "Total URLs": [len(df)],
                }
                summary_df = pd.DataFrame(summary)
                st.dataframe(summary_df)

            # Main Table Tab
            with tabs[1]:
                st.subheader("Main Analysis Table")
                display_columns = [
                    'url', 'status', 'load_time_ms', 'word_count', 'readability_score',
                    'internal_link_count', 'external_link_count', 'meta_title', 'meta_description',
                    'h1_count', 'h2_count', 'h3_count', 'h4_count', 'h5_count', 'h6_count'
                ]
                st.download_button("Download Main Table", df[display_columns].to_csv(index=False).encode('utf-8'), "main_table.csv", "text/csv")
                st.dataframe(df[display_columns])

            # Internal Links Tab
            with tabs[2]:
                st.subheader("Internal Links")
                internal_links_df = pd.DataFrame(internal_links_data)
                st.download_button("Download Internal Links", internal_links_df.to_csv(index=False).encode('utf-8'), "internal_links.csv", "text/csv")
                st.dataframe(internal_links_df)

            # External Links Tab
            with tabs[3]:
                st.subheader("External Links")
                external_links_df = pd.DataFrame(external_links_data)
                st.download_button("Download External Links", external_links_df.to_csv(index=False).encode('utf-8'), "external_links.csv", "text/csv")
                st.dataframe(external_links_df)

            # Headings Tab
            with tabs[4]:
                st.subheader("Headings (H1-H6)")
                headings_df = pd.DataFrame(headings_data)
                st.download_button("Download Headings", headings_df.to_csv(index=False).encode('utf-8'), "headings.csv", "text/csv")
                st.dataframe(headings_df)

if __name__ == "__main__":
    main()
