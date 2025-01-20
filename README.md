# Enhanced SEO Content Analyzer

A Streamlit-based web application for analyzing SEO metrics of webpages. This tool allows users to extract key SEO data, such as meta tags, headings, keywords, internal links, and more, from a list of URLs.

---

## Features

1. **Load Time Analysis**:
   - Measures page load time in milliseconds for each URL.

2. **Meta Tag Extraction**:
   - Extracts meta title and meta description from each page.

3. **Headings Analysis**:
   - Extracts all headings (H1 to H6) and provides their counts.

4. **Word Count Analysis**:
   - Displays the word count for each URL and the average word count across all URLs.

5. **Internal Link Analysis**:
   - Extracts all internal links and their anchor texts.
   - Displays the internal link count for each URL and the average internal link count.

6. **Readability Score**:
   - Computes the Flesch Reading Ease score for each page.

7. **Keyword Extraction**:
   - Identifies the top 20 most common keywords from the page content.

8. **Exportable Data**:
   - Provides downloadable CSV files for:
     - Main analysis.
     - Headings.
     - Internal links.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/seo-content-analyzer.git
   cd seo-content-analyzer
