"""
URL Content Analyzer
Version: 1.0
Created: January 2024
Requirements: Python 3.7+, see requirements.txt
Dependencies:
    - streamlit==1.32.0
    - requests==2.31.0
    - beautifulsoup4==4.12.3
    - pandas==2.2.0
    - xlsxwriter==3.1.9
    - python-dotenv==1.0.1
    - chardet==5.2.0
    - openpyxl==3.1.2

Description: A Streamlit web application that analyzes URLs for meta information, 
            headings, and word count with export capabilities.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
import io
import re

__version__ = "1.0"
__app_name__ = "URL Content Analyzer"

def clean_text(text):
    """Clean text by removing extra whitespace and newlines"""
    return ' '.join(text.split())

def get_word_count(soup):
    """Get word count from visible text"""
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    # Get text and count words
    text = soup.get_text()
    words = re.findall(r'\w+', text)
    return len(words)

def analyze_url(url):
    """Analyze a single URL and extract required information"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract meta information
        meta_title = soup.find('title')
        meta_title = clean_text(meta_title.text) if meta_title else ''
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_description = clean_text(meta_description['content']) if meta_description else ''
        
        # Extract headings
        headings = {}
        for i in range(1, 7):
            tag = f'h{i}'
            headings[tag] = [clean_text(h.text) for h in soup.find_all(tag)]
        
        # Get word count
        word_count = get_word_count(soup)
        
        return {
            'url': url,
            'meta_title': meta_title,
            'meta_description': meta_description,
            'h1': ' | '.join(headings['h1']),
            'h2': ' | '.join(headings['h2']),
            'h3': ' | '.join(headings['h3']),
            'h4': ' | '.join(headings['h4']),
            'h5': ' | '.join(headings['h5']),
            'h6': ' | '.join(headings['h6']),
            'word_count': word_count,
            'status': 'Success'
        }
    
    except Exception as e:
        return {
            'url': url,
            'meta_title': '',
            'meta_description': '',
            'h1': '',
            'h2': '',
            'h3': '',
            'h4': '',
            'h5': '',
            'h6': '',
            'word_count': 0,
            'status': f'Error: {str(e)}'
        }

def main():
    st.set_page_config(page_title=f"{__app_name__} v{__version__}", layout="wide")
    
    # App header with version
    st.title(f"{__app_name__} v{__version__}")
    st.write("Analyze meta information, headings, and word count for up to 10 URLs")
    
    # URL input
    st.subheader("Enter URLs (one per line, max 10)")
    url_text = st.text_area("", height=200)
    
    if st.button("Analyze URLs"):
        if url_text:
            urls = [url.strip() for url in url_text.split('\n') if url.strip()]
            
            if len(urls) > 10:
                st.warning("Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
                urls = urls[:10]
            
            if urls:
                # Initialize progress bar
                progress_bar = st.progress(0)
                st.write("Analyzing URLs...")
                
                # Analyze URLs
                results = []
                for i, url in enumerate(urls):
                    progress_bar.progress((i + 1) / len(urls))
                    result = analyze_url(url)
                    results.append(result)
                
                # Create DataFrame
                df = pd.DataFrame(results)
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("URLs Analyzed", len(results))
                with col2:
                    successful = len([r for r in results if r['status'] == 'Success'])
                    st.metric("Successful", successful)
                with col3:
                    avg_words = int(sum(r['word_count'] for r in results) / len(results))
                    st.metric("Average Word Count", avg_words)
                
                # Display results table
                st.subheader("Analysis Results")
                
                # Style the DataFrame
                def highlight_errors(val):
                    if isinstance(val, str) and val.startswith('Error'):
                        return 'color: red'
                    return ''
                
                styled_df = df.style.applymap(highlight_errors, subset=['status'])
                st.dataframe(styled_df, use_container_width=True)
                
                # Export options
                st.subheader("Export Results")
                
                col1, col2 = st.columns(2)
                
                # CSV export
                with col1:
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        csv,
                        f"url_analysis_v{__version__}.csv",
                        "text/csv",
                        key='download-csv'
                    )
                
                # Excel export
                with col2:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, sheet_name='URL Analysis', index=False)
                    excel_data = output.getvalue()
                    st.download_button(
                        "Download Excel",
                        excel_data,
                        f"url_analysis_v{__version__}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key='download-excel'
                    )
        
        else:
            st.warning("Please enter at least one URL to analyze.")

if __name__ == "__main__":
    main()
