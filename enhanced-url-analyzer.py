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
import plotly.express as px
import plotly.graph_objects as go

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

def extract_internal_links(soup, base_url):
    """Extract internal links and their anchor texts"""
    internal_links = []
    domain = urlparse(base_url).netloc
    for a in soup.find_all('a', href=True):
        href = urljoin(base_url, a['href'])
        if urlparse(href).netloc == domain:  # Check if it's an internal link
            anchor_text = a.text.strip()
            internal_links.append({'url': href, 'anchor_text': anchor_text})
    return internal_links

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
        'keywords': {},
        'headings': [],
        'internal_links': [],
        'internal_link_count': 0
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

        # Meta tags
        meta_tags = extract_meta_tags(soup)
        result['meta_title'] = meta_tags.get('title', '')
        result['meta_description'] = meta_tags.get('description', '')

        # Headings
        headings = extract_headings(soup)
        result['headings'] = headings
        for i in range(1, 7):
            result[f'h{i}_count'] = sum(1 for h in headings if h['level'] == f'H{i}')

        # Internal links
        internal_links = extract_internal_links(soup, url)
        result['internal_links'] = internal_links
        result['internal_link_count'] = len(internal_links)

        # Readability
        result['readability_score'] = flesch_reading_ease(text_content)

        # Keywords
        result['keywords'] = extract_keywords(text_content)

    except Exception as e:
        result['status'] = f"Error: {str(e)}"

    return result

def create_readability_gauge(score):
    """Create a gauge chart for readability score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "red"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 100], 'color': "green"}
            ],
        },
        title={'text': "Readability Score"}
    ))
    fig.update_layout(height=250)
    return fig

def create_heading_distribution(df):
    """Create heading distribution chart"""
    heading_cols = ['h1_count', 'h2_count', 'h3_count', 'h4_count', 'h5_count', 'h6_count']
    heading_data = df[heading_cols].mean()
    fig = px.bar(
        x=['H1', 'H2', 'H3', 'H4', 'H5', 'H6'],
        y=heading_data.values,
        title="Average Heading Distribution",
        labels={'x': 'Heading Level', 'y': 'Average Count'}
    )
    fig.update_traces(marker_color='darkblue')
    return fig

def main():
    st.set_page_config(
        page_title="Enhanced SEO Content Analyzer",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar configuration
    with st.sidebar:
        st.title("SEO Analyzer Settings")
        max_keywords = st.slider("Number of keywords to extract", 5, 50, 20)
        show_advanced = st.checkbox("Show Advanced Metrics", value=False)

    # Main content
    st.title("SEO Content Analyzer")
    st.markdown("""
    Analyze multiple URLs for SEO metrics including content structure, readability, and internal linking.
    Enter up to 10 URLs below to begin your analysis.
    """)

    # URL input section
    urls_input = st.text_area(
        "Enter URLs (one per line)",
        height=150,
        help="Enter up to 10 URLs, each on a new line"
    )
    urls = [url.strip() for url in urls_input.split('\n') if url.strip()]

    # Analysis button and URL counter
    col1, col2 = st.columns([2, 1])
    with col1:
        analyze_button = st.button("Analyze URLs", use_container_width=True)
    with col2:
        if urls:
            st.metric("URLs to analyze", len(urls))

    if analyze_button:
        if not urls:
            st.error("Please enter at least one URL to analyze")
            return

        if len(urls) > 10:
            st.warning("Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
            urls = urls[:10]

        # Analysis section
        with st.spinner("Analyzing URLs..."):
            results = []
            headings_data = []
            internal_links_data = []
            progress_bar = st.progress(0)

            for i, url in enumerate(urls):
                progress_bar.progress((i + 1) / len(urls))
                result = analyze_url(url)
                results.append(result)
                
                # Collect additional data
                for heading in result['headings']:
                    headings_data.append({'url': url, 'level': heading['level'], 'text': heading['text']})
                for link in result['internal_links']:
                    internal_links_data.append({
                        'url': url,
                        'internal_url': link['url'],
                        'anchor_text': link['anchor_text']
                    })

            df = pd.DataFrame(results)

        # Results Display
        st.success("Analysis Complete!")

        # Summary metrics
        st.subheader("Summary Metrics")
        metric_cols = st.columns(4)
        metric_cols[0].metric(
            "Average Word Count",
            f"{df['word_count'].mean():.0f}",
            f"{df['word_count'].std():.0f} σ"
        )
        metric_cols[1].metric(
            "Average Internal Links",
            f"{df['internal_link_count'].mean():.0f}",
            f"{df['internal_link_count'].std():.0f} σ"
        )
        metric_cols[2].metric(
            "Average Load Time",
            f"{df['load_time_ms'].mean():.0f}ms",
            f"{df['load_time_ms'].std():.0f}ms σ"
        )
        metric_cols[3].metric(
            "Average Readability",
            f"{df['readability_score'].mean():.1f}",
            f"{df['readability_score'].std():.1f} σ"
        )

        # Results tabs
        tab1, tab2, tab3 = st.tabs(["Metrics", "Content Analysis", "Links Analysis"])

        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(create_readability_gauge(df['readability_score'].mean()), use_container_width=True)
            with col2:
                st.plotly_chart(create_heading_distribution(df), use_container_width=True)

        with tab2:
            st.subheader("Content Analysis")
            content_cols = st.columns(2)
            with content_cols[0]:
                st.dataframe(
                    df[['url', 'word_count', 'readability_score', 'meta_title', 'meta_description']],
                    use_container_width=True
                )
            with content_cols[1]:
                if show_advanced:
                    st.dataframe(
                        pd.DataFrame(headings_data),
                        use_container_width=True
                    )

        with tab3:
            st.subheader("Internal Links Analysis")
            st.dataframe(
                pd.DataFrame(internal_links_data),
                use_container_width=True
            )

        # Export section
        st.subheader("Export Results")
        export_cols = st.columns(3)
        with export_cols[0]:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Main Analysis",
                csv,
                "seo_analysis.csv",
                "text/csv",
                use_container_width=True
            )
        with export_cols[1]:
            headings_csv = pd.DataFrame(headings_data).to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Headings",
                headings_csv,
                "headings_analysis.csv",
                "text/csv",
                use_container_width=True
            )
        with export_cols[2]:
            links_csv = pd.DataFrame(internal_links_data).to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Internal Links",
                links_csv,
                "internal_links.csv",
                "text/csv",
                use_container_width=True
            )

if __name__ == "__main__":
    main()
