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

def analyze_url(url):
    """Basic URL content analysis"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content
        text_content = ' '.join([p.text for p in soup.find_all('p')])
        
        return {
            'url': url,
            'status': 'Success',
            'word_count': len(text_content.split()),
            'title': soup.title.text if soup.title else '',
            'meta_description': soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else ''
        }
    except Exception as e:
        return {
            'url': url,
            'status': f'Error: {str(e)}',
            'word_count': 0,
            'title': '',
            'meta_description': ''
        }

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
    try:
        images = soup.find_all('img')
        return {
            'total_count': len(images),
            'missing_alt': len([img for img in images if not img.get('alt')])
        }
    except:
        return {'total_count': 0, 'missing_alt': 0}

def analyze_links(soup, base_url):
    """Analyze links on the page"""
    try:
        links = soup.find_all('a', href=True)
        domain = urlparse(base_url).netloc
        
        internal_links = []
        external_links = []
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == domain:
                internal_links.append(full_url)
            else:
                external_links.append(full_url)
        
        return {
            'internal_count': len(internal_links),
            'external_count': len(external_links)
        }
    except:
        return {'internal_count': 0, 'external_count': 0}

def analyze_seo(soup, text_content):
    """Analyze SEO elements"""
    try:
        readability_score = textstat.flesch_reading_ease(text_content)
        return {
            'readability_score': readability_score
        }
    except:
        return {'readability_score': 0}

def enhanced_analyze_url(url):
    """Enhanced URL analysis with additional metrics"""
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
            'readability_score': 0
        }
        
        # Measure load time
        load_time = get_load_time(url)
        result['load_time_ms'] = load_time if load_time else 0
        
        # Check SSL
        ssl_valid, ssl_expiry = check_ssl(url)
        result['ssl_valid'] = ssl_valid
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract text content
        text_content = ' '.join([p.text for p in soup.find_all('p')])
        result['word_count'] = len(text_content.split())
        
        # Image analysis
        image_data = analyze_images(soup, url)
        result['image_count'] = image_data['total_count']
        result['images_missing_alt'] = image_data['missing_alt']
        
        # Link analysis
        link_data = analyze_links(soup, url)
        result['internal_links'] = link_data['internal_count']
        result['external_links'] = link_data['external_count']
        
        # SEO analysis
        seo_data = analyze_seo(soup, text_content)
        result['readability_score'] = seo_data['readability_score']
        
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
            'readability_score': 0
        }

def create_visualization(df):
    """Create visualization of analysis results"""
    try:
        plt.figure(figsize=(10, 6))
        
        # Select numeric columns for visualization
        numeric_cols = ['word_count', 'internal_links', 'external_links',
                       'image_count', 'readability_score']
        plot_data = df[numeric_cols].mean()
        
        sns.barplot(x=plot_data.index, y=plot_data.values)
        plt.xticks(rotation=45)
        plt.title('Average Metrics Across All URLs')
        
        return plt
    except Exception as e:
        st.error(f"Error creating visualization: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Enhanced URL Content Analyzer", layout="wide")
    
    st.title("Enhanced URL Content Analyzer")
    
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
            
            # Create DataFrame
            df = pd.DataFrame(results)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("URLs Analyzed", len(results))
            with col2:
                avg_load = df['load_time_ms'].mean()
                st.metric("Avg Load Time (ms)", f"{int(avg_load)}")
            with col3:
                ssl_valid = df['ssl_valid'].sum()
                st.metric("SSL Valid", f"{int(ssl_valid)}/{len(results)}")
            with col4:
                avg_score = df['readability_score'].mean()
                st.metric("Avg Readability", f"{avg_score:.1f}")
            
            # Display visualization
            st.subheader("Analysis Visualization")
            fig = create_visualization(df)
            if fig:
                st.pyplot(fig)
            
            # Display detailed results
            st.subheader("Detailed Analysis")
            st.dataframe(df)
            
            # Export options
            st.subheader("Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    "url_analysis.csv",
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
                    "url_analysis.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()
