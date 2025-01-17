import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import io
import re
import time
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from textstat import flesch_reading_ease

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

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
    # Tokenize the text and remove stopwords and punctuation
    stop_words = set(stopwords.words('english')) | set(punctuation)
    words = [word.lower() for word in word_tokenize(text) if word.lower() not in stop_words and word.isalnum()]

    # Count word frequencies
    word_counts = Counter(words)

    # Return the most common keywords
    return dict(word_counts.most_common(num_keywords))

def extract_anchors(soup, base_url):
    """Extract anchor texts for internal links"""
    anchors = []
    domain = urlparse(base_url).netloc

    for a in soup.find_all('a', href=True):
        href = urljoin(base_url, a['href'])  # Resolve relative URLs
        if urlparse(href).netloc == domain:  # Check if it's an internal link
            anchor_text = a.text.strip()
            if anchor_text:  # Exclude empty anchor texts
                anchors.append(anchor_text)

    return anchors

def extract_meta_tags(soup):
    """Extract meta tags from the page"""
    meta_tags = {}

    # Extract title
    meta_tags['title'] = soup.title.text.strip() if soup.title else ''

    # Extract meta description
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_tags['description'] = meta_description['content'].strip() if meta_description and meta_description.get('content') else ''

    return meta_tags

def extract_headings(soup):
    """Extract all headings (H1-H6) from the page"""
    headings = {}
    for i in range(1, 7):
        heading_tag = f'h{i}'
        headings_list = [h.text.strip() for h in soup.find_all(heading_tag)]
        headings[heading_tag] = headings_list
        headings[f'{heading_tag}_count'] = len(headings_list)
    return headings

def enhanced_analyze_url(url):
    """Enhanced URL analysis with additional SEO metrics"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        # Initialize default values
        result = {
            'url': url,
            'status': 'Success',
            'load_time_ms': 0,
            'word_count': 0,
            'meta_title': '',
            'meta_description': '',
            'h1_count': 0,
            'h2_count': 0,
            'h3_count': 0,
            'h4_count': 0,
            'h5_count': 0,
            'h6_count': 0,
            'keywords': {},
            'anchors': []
        }

        # Measure load time
        load_time = get_load_time(url)
        result['load_time_ms'] = load_time if load_time else 0

        # Fetch and parse page content
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = ' '.join([p.text.strip() for p in soup.find_all(['p', 'div', 'span'])])

        # Basic metrics
        result['word_count'] = len(text_content.split())

        # Extract SEO elements
        meta_tags = extract_meta_tags(soup)
        result['meta_title'] = meta_tags.get('title', '')
        result['meta_description'] = meta_tags.get('description', '')

        headings = extract_headings(soup)
        result['h1_count'] = headings.get('h1_count', 0)
        result['h2_count'] = headings.get('h2_count', 0)
        result['h3_count'] = headings.get('h3_count', 0)
        result['h4_count'] = headings.get('h4_count', 0)
        result['h5_count'] = headings.get('h5_count', 0)
        result['h6_count'] = headings.get('h6_count', 0)

        result['keywords'] = extract_keywords(text_content)
        result['anchors'] = extract_anchors(soup, url)

        return result

    except Exception as e:
        return {
            'url': url,
            'status': f'Error: {str(e)}',
            'load_time_ms': 0,
            'word_count': 0,
            'meta_title': '',
            'meta_description': '',
            'h1_count': 0,
            'h2_count': 0,
            'h3_count': 0,
            'h4_count': 0,
            'h5_count': 0,
            'h6_count': 0,
            'keywords': {},
            'anchors': []
        }

def main():
    st.set_page_config(page_title="Enhanced SEO Content Analyzer", layout="wide")

    st.title("Enhanced SEO Content Analyzer")

    # URL input
    urls_input = st.text_area("Enter URLs (one per line, max 10)", height=200)
    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]

    if st.button("Analyze URLs"):
        if urls:
            if len(urls) > 10:
                st.warning("Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
                urls = urls[:10]

            progress_bar = st.progress(0)
            results = []

            # Analyze URLs with progress tracking
            for i, url in enumerate(urls):
                progress_bar.progress((i + 1) / len(urls))
                result = enhanced_analyze_url(url)
                results.append(result)

            # Create DataFrame for main display
            df = pd.DataFrame(results)

            # Customize column display
            display_df = df[['url', 'status', 'load_time_ms', 'word_count', 'meta_title', 'meta_description',
                             'h1_count', 'h2_count', 'h3_count', 'h4_count', 'h5_count', 'h6_count']]

            # Apply visual enhancements to the table
            st.subheader("Detailed Analysis")
            st.dataframe(display_df.style.set_properties(**{
                'background-color': '#f5f5f5',
                'color': '#333',
                'border-color': 'black',
                'font-family': 'Arial',
                'text-align': 'center'
            }))

            # Export main table
            st.subheader("Export Main Results")
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "seo_analysis.csv", "text/csv")

            # Separate export for keywords and anchors
            keywords_data = pd.DataFrame([
                {
                    'url': result['url'],
                    'keywords': ', '.join([f"{k} ({v})" for k, v in result['keywords'].items()])
                } for result in results
            ])

            anchors_data = pd.DataFrame([
                {
                    'url': result['url'],
                    'anchors': ', '.join(result['anchors'])
                } for result in results
            ])

            st.subheader("Export Keywords and Anchors")
            st.write("**Keywords:**")
            st.dataframe(keywords_data)
            keywords_csv = keywords_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download Keywords CSV", keywords_csv, "keywords_analysis.csv", "text/csv")

            st.write("**Anchors:**")
            st.dataframe(anchors_data)
            anchors_csv = anchors_data.to_csv(index=False).encode('utf-8')
            st.download_button("Download Anchors CSV", anchors_csv, "anchors_analysis.csv", "text/csv")

if __name__ == "__main__":
    main()
