"""
Enhanced URL Content Analyzer
Version: 2.1
Created: January 2024
Description: Advanced URL analysis tool with enhanced SEO analysis capabilities
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse, urljoin
import io
import re
import time
import ssl
import socket
import json
from concurrent.futures import ThreadPoolExecutor
from readability import Document
import textstat
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

def extract_meta_tags(soup):
    """Extract meta tags from the page"""
    meta_tags = {}
    
    # Extract title
    meta_tags['title'] = soup.title.text.strip() if soup.title else ''
    
    # Extract meta description
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_tags['description'] = meta_description['content'].strip() if meta_description else ''
    
    # Extract other important meta tags
    for meta in soup.find_all('meta'):
        name = meta.get('name', '').lower()
        property = meta.get('property', '').lower()
        content = meta.get('content', '').strip()
        
        if name and content:
            meta_tags[f'meta_{name}'] = content
        elif property and content:
            meta_tags[f'meta_{property}'] = content
    
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

def extract_keywords(text, num_keywords=20):
    """Extract commonly used keywords from the text"""
    # Tokenize and convert to lowercase
    tokens = word_tokenize(text.lower())
    
    # Remove stopwords and punctuation
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words and word not in punctuation and len(word) > 2]
    
    # Count word frequencies
    word_freq = Counter(tokens)
    
    # Get the most common words
    return dict(word_freq.most_common(num_keywords))

def extract_anchors(soup, base_url):
    """Extract and analyze anchor texts and their targets"""
    anchors = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.text.strip()
        if text and len(text) > 1:  # Ignore empty or single-character anchor texts
            full_url = urljoin(base_url, href)
            anchors.append({
                'text': text,
                'href': full_url,
                'internal': urlparse(full_url).netloc == urlparse(base_url).netloc
            })
    return anchors

def enhanced_analyze_url(url):
    """Enhanced URL analysis with additional SEO metrics"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Initialize default values
        result = {
            'url': url,
            'status': 'Success',
            'ssl_valid': False,
            'load_time_ms': 0,
            'word_count': 0,
            'image_count': 0,
            'images_missing_alt': 0,
            'internal_links': 0,
            'external_links': 0,
            'readability_score': 0,
            'meta_tags': {},
            'headings': {},
            'keywords': {},
            'anchors': []
        }
        
        # Measure load time and check SSL
        result['load_time_ms'] = get_load_time(url) or 0
        result['ssl_valid'], _ = check_ssl(url)
        
        # Fetch and parse page content
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = ' '.join([p.text for p in soup.find_all(['p', 'div', 'span'])])
        
        # Basic metrics
        result['word_count'] = len(text_content.split())
        
        # Extract SEO elements
        result['meta_tags'] = extract_meta_tags(soup)
        result['headings'] = extract_headings(soup)
        result['keywords'] = extract_keywords(text_content)
        result['anchors'] = extract_anchors(soup, url)
        
        # Image and link analysis
        image_data = analyze_images(soup, url)
        result['image_count'] = image_data['total_count']
        result['images_missing_alt'] = image_data['missing_alt']
        
        link_data = analyze_links(soup, url)
        result['internal_links'] = link_data['internal_count']
        result['external_links'] = link_data['external_count']
        
        # Readability analysis
        result['readability_score'] = textstat.flesch_reading_ease(text_content)
        
        return result
        
    except Exception as e:
        return {
            'url': url,
            'status': f'Error: {str(e)}',
            'ssl_valid': False,
            'load_time_ms': 0,
            'word_count': 0,
            'image_count': 0,
            'images_missing_alt': 0,
            'internal_links': 0,
            'external_links': 0,
            'readability_score': 0,
            'meta_tags': {},
            'headings': {},
            'keywords': {},
            'anchors': []
        }

def create_detailed_report(results):
    """Create a detailed report including all SEO elements"""
    report = []
    
    for result in results:
        url_report = {
            'URL': result['url'],
            'Status': result['status'],
            'Load Time (ms)': result['load_time_ms'],
            'SSL Valid': result['ssl_valid'],
            'Word Count': result['word_count'],
            'Readability Score': result['readability_score'],
        }
        
        # Add meta tags
        for key, value in result['meta_tags'].items():
            url_report[f'Meta_{key}'] = value
        
        # Add heading counts
        for key, value in result['headings'].items():
            if key.endswith('_count'):
                url_report[f'Heading_{key}'] = value
        
        # Add top keywords (first 10)
        keywords = list(result['keywords'].items())[:10]
        for i, (keyword, count) in enumerate(keywords, 1):
            url_report[f'Keyword_{i}'] = f'{keyword} ({count})'
        
        # Add link counts
        url_report['Internal Links'] = result['internal_links']
        url_report['External Links'] = result['external_links']
        
        report.append(url_report)
    
    return pd.DataFrame(report)

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
            
            # Create detailed report
            df = create_detailed_report(results)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("URLs Analyzed", len(results))
            with col2:
                avg_load = df['Load Time (ms)'].mean()
                st.metric("Avg Load Time (ms)", f"{int(avg_load)}")
            with col3:
                ssl_valid = df['SSL Valid'].sum()
                st.metric("SSL Valid", f"{int(ssl_valid)}/{len(results)}")
            with col4:
                avg_score = df['Readability Score'].mean()
                st.metric("Avg Readability", f"{avg_score:.1f}")
            
            # Display detailed results
            st.subheader("Detailed Analysis")
            st.dataframe(df)
            
            # Display raw data for each URL
            st.subheader("Raw Data (Expandable)")
            for result in results:
                with st.expander(f"Detailed data for {result['url']}"):
                    # Meta Tags
                    st.write("Meta Tags:")
                    st.json(result['meta_tags'])
                    
                    # Headings
                    st.write("Headings:")
                    st.json({k: v for k, v in result['headings'].items() if not k.endswith('_count')})
                    
                    # Keywords
                    st.write("Top Keywords:")
                    st.json(dict(list(result['keywords'].items())[:20]))
                    
                    # Anchors
                    st.write("Anchor Texts:")
                    st.json(result['anchors'])
            
            # Export options
            st.subheader("Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    "seo_analysis.csv",
                    "text/csv"
                )
            
            with col2:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='SEO Analysis', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    "Download Excel",
                    excel_data,
                    "seo_analysis.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
