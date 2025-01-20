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
from datetime import datetime

# Configure page settings
st.set_page_config(
    page_title="Enhanced SEO Content Analyzer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f8f9fa;
        border-radius: 4px;
        padding: 10px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Previous helper functions remain the same
# [preprocess_url, get_load_time, extract_keywords, extract_meta_tags, etc.]

def create_metric_card(title, value, description):
    """Create a styled metric card"""
    st.markdown(f"""
        <div class="metric-card">
            <h3 style="margin:0;font-size:1rem;color:#666;">{title}</h3>
            <p style="margin:8px 0;font-size:1.5rem;font-weight:bold;">{value}</p>
            <p style="margin:0;font-size:0.875rem;color:#666;">{description}</p>
        </div>
    """, unsafe_allow_html=True)

def create_recommendations(result):
    """Generate SEO recommendations based on analysis"""
    recommendations = []
    
    if len(result['meta_description']) < 50:
        recommendations.append("🔸 Meta description is too short. Aim for 150-160 characters.")
    
    if result['h1_count'] != 1:
        recommendations.append("🔸 Page should have exactly one H1 tag.")
        
    if result['word_count'] < 300:
        recommendations.append("🔸 Content length is below recommended minimum (300 words).")
        
    if result['load_time_ms'] > 3000:
        recommendations.append("🔸 Page load time is high. Consider optimization.")
        
    if result['internal_link_count'] < 3:
        recommendations.append("🔸 Add more internal links for better site structure.")
        
    if result['readability_score'] < 60:
        recommendations.append("🔸 Content readability could be improved.")
        
    return recommendations

def main():
    # Header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://via.placeholder.com/100", width=80)  # Replace with your logo
    with col2:
        st.title("Enhanced SEO Content Analyzer")
        st.markdown("*Analyze and optimize your website content for better SEO performance*")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Analysis Settings")
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Basic", "Standard", "Deep"],
            value="Standard"
        )
        
        st.subheader("Custom Checks")
        check_meta = st.checkbox("Meta Tags", value=True)
        check_headings = st.checkbox("Heading Structure", value=True)
        check_links = st.checkbox("Link Analysis", value=True)
        check_content = st.checkbox("Content Analysis", value=True)
        
        st.markdown("---")
        st.markdown("📅 Analysis Date: " + datetime.now().strftime("%Y-%m-%d"))

    # Main content area
    urls_input = st.text_area(
        "Enter URLs to Analyze",
        placeholder="Enter URLs (one per line, max 10 URLs)",
        height=100
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        analyze_button = st.button("🔍 Start Analysis", type="primary", use_container_width=True)
    with col2:
        url_count = len([url for url in urls_input.split('\n') if url.strip()])
        st.metric("URLs to Analyze", f"{url_count}/10")
    with col3:
        st.markdown("ℹ️ *Analysis depth:* " + analysis_depth)

    if analyze_button and urls_input:
        urls = [url.strip() for url in urls_input.split('\n') if url.strip()]
        
        if len(urls) > 10:
            st.warning("⚠️ Maximum 10 URLs allowed. Only the first 10 will be analyzed.")
            urls = urls[:10]

        # Progress tracking
        progress_text = "Analysis in progress... Please wait."
        progress_bar = st.progress(0, text=progress_text)
        
        results = []
        for i, url in enumerate(urls):
            with st.spinner(f"Analyzing URL {i+1}/{len(urls)}: {url}"):
                result = analyze_url(url)
                results.append(result)
                progress_bar.progress((i + 1)/len(urls), text=progress_text)

        # Clear progress bar after completion
        progress_bar.empty()
        
        # Success message
        st.success(f"✅ Analysis completed for {len(urls)} URLs!")

        # Results display using tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "📋 Detailed Results",
            "📈 Visualizations",
            "🔍 Technical SEO",
            "💡 Recommendations"
        ])

        with tab1:
            # Overview metrics in cards
            st.subheader("Key Metrics Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_load_time = sum(r['load_time_ms'] for r in results) / len(results)
                create_metric_card(
                    "Average Load Time",
                    f"{avg_load_time:.0f}ms",
                    "Target: < 3000ms"
                )
                
            with col2:
                avg_word_count = sum(r['word_count'] for r in results) / len(results)
                create_metric_card(
                    "Average Word Count",
                    f"{avg_word_count:.0f}",
                    "Target: > 300 words"
                )
                
            with col3:
                avg_readability = sum(r['readability_score'] for r in results) / len(results)
                create_metric_card(
                    "Average Readability",
                    f"{avg_readability:.1f}",
                    "Flesch Reading Ease Score"
                )

        with tab2:
            st.subheader("Detailed Analysis Results")
            df = pd.DataFrame(results)
            st.dataframe(
                df[[
                    'url', 'status', 'load_time_ms', 'word_count',
                    'readability_score', 'internal_link_count',
                    'external_link_count', 'h1_count'
                ]],
                use_container_width=True
            )
            
            # Export buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "📥 Download Full Report (CSV)",
                    df.to_csv(index=False).encode('utf-8'),
                    "seo_analysis_report.csv",
                    "text/csv"
                )
            with col2:
                st.download_button(
                    "📥 Download Full Report (Excel)",
                    df.to_excel(index=False).encode('utf-8'),
                    "seo_analysis_report.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with tab3:
            st.subheader("Data Visualizations")
            
            # Load Time Distribution
            fig_load_time = px.bar(
                df,
                x='url',
                y='load_time_ms',
                title='Page Load Times',
                labels={'load_time_ms': 'Load Time (ms)', 'url': 'URL'}
            )
            st.plotly_chart(fig_load_time, use_container_width=True)
            
            # Word Count vs Readability
            fig_scatter = px.scatter(
                df,
                x='word_count',
                y='readability_score',
                size='internal_link_count',
                hover_data=['url'],
                title='Content Length vs Readability'
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with tab4:
            st.subheader("Technical SEO Analysis")
            
            for url, result in zip(urls, results):
                with st.expander(f"Technical Details - {url}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Meta Tags**")
                        st.code(f"""
Title: {result['meta_title']}
Description: {result['meta_description']}
                        """)
                        
                    with col2:
                        st.markdown("**Heading Structure**")
                        for i in range(1, 7):
                            count = result[f'h{i}_count']
                            st.progress(count/10, text=f"H{i} Tags: {count}")

        with tab5:
            st.subheader("SEO Recommendations")
            
            for url, result in zip(urls, results):
                with st.expander(f"Recommendations - {url}"):
                    recommendations = create_recommendations(result)
                    if recommendations:
                        for rec in recommendations:
                            st.markdown(rec)
                    else:
                        st.success("✅ No major issues found!")

if __name__ == "__main__":
    main()
