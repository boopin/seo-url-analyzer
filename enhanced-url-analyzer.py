"""
Enhanced URL Content Analyzer
Version: 2.0
Created: January 2024
Description: Advanced URL analysis tool with enhanced content analysis, SEO metrics, 
            and improved UI/UX features.
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

__version__ = "2.0"
__app_name__ = "Enhanced URL Content Analyzer"

def check_ssl(url):
    """Check SSL certificate status"""
    try:
        hostname = urlparse(url).hostname
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                return True, cert['notAfter']
    except:
        return False, None

def get_load_time(url):
    """Measure page load time"""
    try:
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        return round((end_time - start_time) * 1000)  # Convert to milliseconds
    except:
        return None

def analyze_images(soup, base_url):
    """Analyze images on the page"""
    images = soup.find_all('img')
    image_data = {
        'total_count': len(images),
        'missing_alt': len([img for img in images if not img.get('alt')]),
        'images': []
    }
    
    for img in images:
        src = img.get('src', '')
        if src:
            full_url = urljoin(base_url, src)
            image_data['images'].append({
                'src': full_url,
                'alt': img.get('alt', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
    
    return image_data

def analyze_links(soup, base_url):
    """Analyze links on the page"""
    links = soup.find_all('a', href=True)
    domain = urlparse(base_url).netloc
    
    internal_links = []
    external_links = []
    broken_links = []
    
    for link in links:
        href = link['href']
        full_url = urljoin(base_url, href)
        
        if urlparse(full_url).netloc == domain:
            internal_links.append(full_url)
        else:
            external_links.append(full_url)
            
        try:
            response = requests.head(full_url, allow_redirects=True)
            if response.status_code >= 400:
                broken_links.append(full_url)
        except:
            broken_links.append(full_url)
    
    return {
        'internal_count': len(internal_links),
        'external_count': len(external_links),
        'broken_count': len(broken_links),
        'broken_links': broken_links
    }

def analyze_seo(soup, url):
    """Analyze SEO elements"""
    # Title analysis
    title = soup.find('title')
    title_text = title.text.strip() if title else ''
    title_length = len(title_text)
    title_score = 1 if 30 <= title_length <= 60 else 0
    
    # Meta description analysis
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    meta_desc_text = meta_desc['content'].strip() if meta_desc else ''
    meta_desc_length = len(meta_desc_text)
    meta_desc_score = 1 if 120 <= meta_desc_length <= 160 else 0
    
    # Keywords analysis
    text_content = ' '.join([p.text for p in soup.find_all('p')])
    words = text_content.lower().split()
    word_freq = pd.Series(words).value_counts()
    top_keywords = word_freq.head(10).to_dict()
    
    # Readability
    readability_score = textstat.flesch_reading_ease(text_content)
    
    return {
        'title_length': title_length,
        'title_score': title_score,
        'meta_desc_length': meta_desc_length,
        'meta_desc_score': meta_desc_score,
        'top_keywords': top_keywords,
        'readability_score': readability_score
    }

def enhanced_analyze_url(url):
    """Enhanced URL analysis with additional metrics"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Measure load time
        load_time = get_load_time(url)
        
        # Check SSL
        ssl_valid, ssl_expiry = check_ssl(url)
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Basic content analysis
        basic_content = analyze_url(url)
        
        # Enhanced analysis
        image_analysis = analyze_images(soup, url)
        link_analysis = analyze_links(soup, url)
        seo_analysis = analyze_seo(soup, url)
        
        return {
            **basic_content,
            'load_time_ms': load_time,
            'ssl_valid': ssl_valid,
            'ssl_expiry': ssl_expiry,
            'image_count': image_analysis['total_count'],
            'images_missing_alt': image_analysis['missing_alt'],
            'internal_links': link_analysis['internal_count'],
            'external_links': link_analysis['external_count'],
            'broken_links': link_analysis['broken_count'],
            'readability_score': seo_analysis['readability_score'],
            'title_score': seo_analysis['title_score'],
            'meta_desc_score': seo_analysis['meta_desc_score'],
            'top_keywords': json.dumps(seo_analysis['top_keywords'])
        }
        
    except Exception as e:
        return {
            'url': url,
            'status': f'Error: {str(e)}',
            'ssl_valid': False,
            'load_time_ms': None
        }

def create_visualization(df):
    """Create visualization of analysis results"""
    plt.figure(figsize=(10, 6))
    
    # Average scores by URL
    scores_df = df[[
        'word_count', 'internal_links', 'external_links',
        'image_count', 'readability_score'
    ]].mean()
    
    sns.barplot(x=scores_df.index, y=scores_df.values)
    plt.xticks(rotation=45)
    plt.title('Average Metrics Across All URLs')
    
    return plt

def main():
    st.set_page_config(page_title=f"{__app_name__} v{__version__}", layout="wide")
    
    # Sidebar for file upload and options
    with st.sidebar:
        st.header("Input Options")
        input_method = st.radio(
            "Choose input method:",
            ["Manual Entry", "File Upload"]
        )
        
        if input_method == "File Upload":
            uploaded_file = st.file_uploader("Upload URLs (CSV/Excel)", type=['csv', 'xlsx'])
        
        st.header("Analysis Options")
        check_ssl = st.checkbox("Check SSL Certificate", value=True)
        check_load_time = st.checkbox("Measure Load Time", value=True)
        check_broken_links = st.checkbox("Check Broken Links", value=True)
    
    st.title(f"{__app_name__} v{__version__}")
    
    # Main content area
    if input_method == "Manual Entry":
        urls_input = st.text_area("Enter URLs (one per line, max 10)", height=200)
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
    else:
        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                df_urls = pd.read_csv(uploaded_file)
            else:
                df_urls = pd.read_excel(uploaded_file)
            urls = df_urls['url'].tolist()
    
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
            
            # Create DataFrame
            df = pd.DataFrame(results)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("URLs Analyzed", len(results))
            with col2:
                avg_load = df['load_time_ms'].mean()
                st.metric("Avg Load Time (ms)", f"{avg_load:.0f}")
            with col3:
                ssl_valid = df['ssl_valid'].sum()
                st.metric("SSL Valid", f"{ssl_valid}/{len(results)}")
            with col4:
                avg_score = df['readability_score'].mean()
                st.metric("Avg Readability", f"{avg_score:.1f}")
            
            # Display visualization
            st.subheader("Analysis Visualization")
            fig = create_visualization(df)
            st.pyplot(fig)
            
            # Display detailed results
            st.subheader("Detailed Analysis")
            st.dataframe(df, use_container_width=True)
            
            # Export options
            st.subheader("Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    f"enhanced_url_analysis_v{__version__}.csv",
                    "text/csv"
                )
            
            with col2:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='URL Analysis', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    "Download Excel",
                    excel_data,
                    f"enhanced_url_analysis_v{__version__}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
