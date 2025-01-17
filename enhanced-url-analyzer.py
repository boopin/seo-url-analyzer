"""
Enhanced URL Content Analyzer
Version: 2.1
Created: January 2024
Description: Advanced URL analysis tool with enhanced SEO analysis capabilities
"""

[Previous imports remain the same...]

def get_load_time(url):
    """Measure page load time"""
    try:
        start_time = time.time()
        requests.get(url, timeout=10)
        end_time = time.time()
        return round((end_time - start_time) * 1000)  # Convert to milliseconds
    except Exception:
        return None

def json_serialize(obj):
    """Custom JSON serializer to handle sets and other non-serializable objects"""
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, (dict, list)):
        return obj
    return str(obj)

def extract_meta_tags(soup):
    """Extract meta tags from the page"""
    meta_tags = {}
    
    # Extract title
    meta_tags['title'] = soup.title.text.strip() if soup.title else ''
    
    # Extract meta description
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_tags['description'] = meta_description['content'].strip() if meta_description and meta_description.get('content') else ''
    
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

def analyze_images(soup, base_url):
    """Analyze images on the page"""
    try:
        images = soup.find_all('img')
        image_data = {
            'total_count': len(images),
            'missing_alt': len([img for img in images if not img.get('alt')])
        }
        return image_data
    except Exception:
        return {'total_count': 0, 'missing_alt': 0}

def analyze_links(soup, base_url):
    """Analyze links on the page"""
    try:
        links = soup.find_all('a', href=True)
        domain = urlparse(base_url).netloc
        internal_count = sum(1 for link in links if urlparse(urljoin(base_url, link['href'])).netloc == domain)
        return {
            'internal_count': internal_count,
            'external_count': len(links) - internal_count
        }
    except Exception:
        return {'internal_count': 0, 'external_count': 0}

[Previous extract_keywords and extract_anchors functions remain the same...]

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
        
        # Measure load time
        load_time = get_load_time(url)
        result['load_time_ms'] = load_time if load_time else 0
        
        # Check SSL
        ssl_valid, _ = check_ssl(url)
        result['ssl_valid'] = ssl_valid
        
        # Fetch and parse page content
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text_content = ' '.join([p.text.strip() for p in soup.find_all(['p', 'div', 'span'])])
        
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
                    st.json(json.dumps(result['meta_tags'], default=json_serialize))
                    
                    # Headings
                    st.write("Headings:")
                    headings_data = {k: v for k, v in result['headings'].items() if not k.endswith('_count')}
                    st.json(json.dumps(headings_data, default=json_serialize))
                    
                    # Keywords
                    st.write("Top Keywords:")
                    st.json(json.dumps(dict(list(result['keywords'].items())[:20]), default=json_serialize))
                    
                    # Anchors
                    st.write("Anchor Texts:")
                    st.json(json.dumps(result['anchors'], default=json_serialize))
            
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
