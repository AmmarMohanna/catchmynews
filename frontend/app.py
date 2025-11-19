"""Streamlit frontend for NewsCatcher."""
import os
import streamlit as st
import requests
from typing import List, Dict, Optional
from datetime import datetime

# Backend URL from environment
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="NewsCatcher",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "selected_criteria" not in st.session_state:
    st.session_state.selected_criteria = None
if "min_relevance" not in st.session_state:
    st.session_state.min_relevance = 0.5


def apply_custom_css():
    """Apply custom CSS styling."""
    # Fixed color scheme
    primary = "#1f77b4"
    secondary = "#ff7f0e"
    text = "#262730"
    
    st.markdown(f"""
    <style>
        .news-card {{
            padding: 1.5rem;
            padding-bottom: 0.5rem;
            border-radius: 0.5rem;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 0.5rem;
            border-left: 4px solid {primary};
            transition: transform 0.2s;
        }}
        .news-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .news-title {{
            color: {primary};
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        .news-summary {{
            color: {text};
            font-size: 0.95rem;
            line-height: 1.5;
            margin-bottom: 0.75rem;
        }}
        .news-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.75rem;
            font-size: 0.85rem;
        }}
        .tag {{
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            background-color: {secondary};
            color: white;
            font-size: 0.8rem;
        }}
        .category {{
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            background-color: {primary};
            color: white;
            font-size: 0.8rem;
        }}
        .relevance-score {{
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            background-color: #28a745;
            color: white;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        .unseen-badge {{
            display: inline-block;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            background-color: #dc3545;
            color: white;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }}
        .stat-card {{
            padding: 1rem;
            border-radius: 0.5rem;
            background: linear-gradient(135deg, {primary}, {secondary});
            color: white;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: 700;
        }}
        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
    </style>
    """, unsafe_allow_html=True)


def fetch_stats() -> Optional[Dict]:
    """Fetch application statistics."""
    try:
        response = requests.get(f"{BACKEND_URL}/stats")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return None


def fetch_urls() -> List[Dict]:
    """Fetch all URLs."""
    try:
        response = requests.get(f"{BACKEND_URL}/urls")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching URLs: {e}")
        return []


def fetch_criteria() -> List[Dict]:
    """Fetch all criteria."""
    try:
        response = requests.get(f"{BACKEND_URL}/criteria")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching criteria: {e}")
        return []


def fetch_articles(criteria_id: Optional[int] = None, min_relevance: float = 0.0, unseen_only: bool = False) -> List[Dict]:
    """Fetch articles with filters."""
    try:
        params = {
            "limit": 100,
            "unseen_only": unseen_only
        }
        if criteria_id:
            params["criteria_id"] = criteria_id
            params["min_relevance"] = min_relevance
        
        response = requests.get(f"{BACKEND_URL}/articles", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching articles: {e}")
        return []


def search_articles(query: str) -> List[Dict]:
    """Search articles by query."""
    try:
        response = requests.get(f"{BACKEND_URL}/articles/search", params={"q": query, "limit": 50})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error searching articles: {e}")
        return []


def trigger_scrape():
    """Trigger scraping for all URLs."""
    try:
        response = requests.post(f"{BACKEND_URL}/scrape")
        response.raise_for_status()
        result = response.json()
        st.success(result["message"])
    except Exception as e:
        st.error(f"Error triggering scrape: {e}")


def add_url(url: str):
    """Add a new URL to track."""
    try:
        response = requests.post(f"{BACKEND_URL}/urls", json={"url": url})
        response.raise_for_status()
        st.success(f"Added URL: {url}")
        return True
    except Exception as e:
        st.error(f"Error adding URL: {e}")
        return False


def delete_url(url_id: int):
    """Delete a URL."""
    try:
        response = requests.delete(f"{BACKEND_URL}/urls/{url_id}")
        response.raise_for_status()
        st.success("URL deleted successfully")
        return True
    except Exception as e:
        st.error(f"Error deleting URL: {e}")
        return False


def add_criteria(name: str, description: str, keywords: List[str], prompt: str):
    """Add new criteria."""
    try:
        data = {
            "name": name,
            "description": description,
            "keywords": keywords,
            "prompt": prompt if prompt else None
        }
        response = requests.post(f"{BACKEND_URL}/criteria", json=data)
        response.raise_for_status()
        st.success(f"Added criteria: {name}")
        return True
    except Exception as e:
        st.error(f"Error adding criteria: {e}")
        return False


def delete_criteria(criteria_id: int):
    """Delete criteria."""
    try:
        response = requests.delete(f"{BACKEND_URL}/criteria/{criteria_id}")
        response.raise_for_status()
        st.success("Criteria deleted successfully")
        return True
    except Exception as e:
        st.error(f"Error deleting criteria: {e}")
        return False


def fetch_criteria_suggestions() -> List[Dict]:
    """Fetch AI-suggested criteria."""
    try:
        response = requests.get(f"{BACKEND_URL}/criteria/suggestions")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching suggestions: {e}")
        return []


def mark_article_seen(article_ids: List[int]):
    """Mark articles as seen."""
    try:
        response = requests.post(f"{BACKEND_URL}/articles/mark-seen", json={"article_ids": article_ids})
        response.raise_for_status()
    except Exception as e:
        st.error(f"Error marking articles as seen: {e}")


def render_article_card(article: Dict):
    """Render a news article card."""
    
    # Escape HTML in title and summary
    import html
    title = html.escape(article.get('title', 'No Title'))
    summary = html.escape(article.get('summary', 'No summary available.'))
    
    # Build categories HTML
    categories_html = " ".join([f'<span class="category">{html.escape(cat)}</span>' for cat in article.get("categories", [])])
    
    # Build tags HTML
    tags_html = " ".join([f'<span class="tag">{html.escape(tag)}</span>' for tag in article.get("tags", [])])
    
    # Get relevance score if criteria is selected
    relevance_html = ""
    if st.session_state.selected_criteria:
        score = article.get("relevance_scores", {}).get(str(st.session_state.selected_criteria), 0)
        if score > 0:
            relevance_html = f'<span class="relevance-score">Relevance: {score:.0%}</span>'
    
    # Unseen badge
    unseen_badge = '<span class="unseen-badge">NEW</span>' if not article.get("is_seen", True) else ""
    
    # Format published date if available
    published_html = ""
    published_at = article.get("published_at")
    if published_at:
        try:
            dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d %H:%M")
            published_html = f'<span style="margin-left: auto; opacity: 0.7;">Published: {date_str}</span>'
        except:
            pass
    
    # Complete card HTML
    st.markdown(f"""
    <div class="news-card">
        <div class="news-title">
            {title}{unseen_badge}
        </div>
        <div class="news-summary">
            {summary}
        </div>
        <div class="news-meta">
            {categories_html}
            {tags_html}
            {relevance_html}
            {published_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons right after (will appear below card)
    col1, col2, col3 = st.columns([1, 1, 8])
    with col1:
        st.link_button("🔗 Open", article['url'], use_container_width=True)
    with col2:
        if not article.get("is_seen", True):
            if st.button("✓ Seen", key=f"seen_{article['id']}", use_container_width=True):
                mark_article_seen([article['id']])
                st.rerun()


def main():
    """Main application."""
    apply_custom_css()
    
    # Sidebar
    with st.sidebar:
        st.title("📰 NewsCatcher")
        st.markdown("---")
        
        # Stats
        st.subheader("📊 Statistics")
        stats = fetch_stats()
        if stats:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{stats['total_urls']}</div>
                    <div class="stat-label">URLs</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{stats['total_articles']}</div>
                    <div class="stat-label">Articles</div>
                </div>
                """, unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            with col3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{stats['unseen_articles']}</div>
                    <div class="stat-label">New</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-number">{stats['total_criteria']}</div>
                    <div class="stat-label">Criteria</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Update button
        if st.button("🔄 UPDATE", use_container_width=True, type="primary"):
            with st.spinner("Starting scraping..."):
                trigger_scrape()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📰 News Feed", "🔗 Manage URLs", "🎯 Manage Criteria"])
    
    # Tab 1: News Feed
    with tab1:
        st.header("News Feed")
        
        # Search bar
        search_query = st.text_input("🔍 Search articles", placeholder="Search by title, summary, or content...")
        
        if search_query:
            # Show search results
            articles = search_articles(search_query)
            if articles:
                st.info(f"Found {len(articles)} articles matching '{search_query}'")
                for article in articles:
                    render_article_card(article)
            else:
                st.warning(f"No articles found for '{search_query}'")
        else:
            # Show regular filtered feed
            # Filters
            col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            criteria_list = fetch_criteria()
            criteria_options = {"All Articles": None}
            criteria_options.update({c["name"]: c["id"] for c in criteria_list})
            
            selected = st.selectbox(
                "Filter by Criteria",
                options=list(criteria_options.keys())
            )
            st.session_state.selected_criteria = criteria_options[selected]
        
        with col2:
            if st.session_state.selected_criteria:
                st.session_state.min_relevance = st.slider(
                    "Min Relevance",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.min_relevance,
                    step=0.1
                )
        
            with col3:
                unseen_only = st.checkbox("Unseen Only", value=False)
            
            # Fetch and display articles
            articles = fetch_articles(
                criteria_id=st.session_state.selected_criteria,
                min_relevance=st.session_state.min_relevance,
                unseen_only=unseen_only
            )
            
            if articles:
                st.info(f"Showing {len(articles)} articles")
                
                for article in articles:
                    render_article_card(article)
            else:
                st.info("No articles found. Add some URLs and click UPDATE to start scraping!")
    
    # Tab 2: URL Management
    with tab2:
        st.header("Manage URLs")
        
        # Add new URL
        with st.expander("➕ Add New URL", expanded=False):
            new_url = st.text_input("URL", placeholder="https://example.com")
            if st.button("Add URL"):
                if new_url:
                    if add_url(new_url):
                        st.rerun()
                else:
                    st.warning("Please enter a URL")
        
        # List existing URLs
        st.subheader("Tracked URLs")
        urls = fetch_urls()
        
        if urls:
            for url in urls:
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    status = "✅" if url["is_active"] else "⏸️"
                    subdomain = " (subdomain)" if url["is_subdomain"] else ""
                    st.write(f"{status} {url['url']}{subdomain}")
                
                with col2:
                    last_scraped = url.get("last_scraped_at")
                    if last_scraped:
                        st.caption(f"Last: {last_scraped[:10]}")
                
                with col3:
                    if st.button("🗑️", key=f"del_url_{url['id']}"):
                        if delete_url(url["id"]):
                            st.rerun()
        else:
            st.info("No URLs tracked yet. Add your first URL above!")
    
    # Tab 3: Criteria Management
    with tab3:
        st.header("Manage Criteria")
        
        # Add new criteria
        with st.expander("➕ Add New Criteria", expanded=False):
            st.info("💡 **Matching Logic**: Articles are matched using simple keyword search. Both keywords and sentence words (excluding common words) are used for matching.")
            
            crit_name = st.text_input("Criteria Name", placeholder="e.g., AI & Machine Learning")
            crit_desc = st.text_area("Description (optional)", placeholder="For your reference only")
            
            st.markdown("**Keywords (optional)**")
            crit_keywords = st.text_input(
                "Comma-separated keywords",
                placeholder="AI, machine learning, neural networks, GPT",
                label_visibility="collapsed"
            )
            
            st.markdown("**Sentence (optional)**")
            crit_prompt = st.text_area(
                "Natural language description",
                placeholder="Articles about artificial intelligence and deep learning applications",
                label_visibility="collapsed",
                help="Words from this sentence will be extracted and used for keyword matching (common words like 'the', 'a', 'is' are filtered out)"
            )
            
            if st.button("Add Criteria"):
                if crit_name:
                    keywords = [k.strip() for k in crit_keywords.split(",") if k.strip()]
                    if not keywords and not crit_prompt:
                        st.warning("Please enter either keywords or a sentence")
                    elif add_criteria(crit_name, crit_desc, keywords, crit_prompt):
                        st.rerun()
                else:
                    st.warning("Please enter a criteria name")
        
        # AI Suggestions
        with st.expander("💡 Get AI Recommendations", expanded=False):
            st.info("Uses LLM to analyze your articles and suggest criteria ideas based on common themes")
            if st.button("Generate Recommendations"):
                with st.spinner("Analyzing articles with AI..."):
                    suggestions = fetch_criteria_suggestions()
                    if suggestions:
                        st.success(f"Found {len(suggestions)} recommendations!")
                        for sug in suggestions:
                            st.write(f"**{sug['name']}**")
                            st.write(sug['description'])
                            st.markdown("---")
                    else:
                        st.warning("No articles found to analyze. Scrape some articles first!")
        
        # List existing criteria
        st.subheader("Your Criteria")
        criteria = fetch_criteria()
        
        if criteria:
            for crit in criteria:
                with st.container():
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        st.write(f"**{crit['name']}**")
                        if crit['description']:
                            st.caption(crit['description'])
                        if crit['keywords']:
                            st.write("🔑 Keywords: " + ", ".join(crit['keywords']))
                        if crit['prompt']:
                            st.write("📝 Sentence: " + crit['prompt'])
                    
                    with col2:
                        if st.button("🗑️", key=f"del_crit_{crit['id']}"):
                            if delete_criteria(crit["id"]):
                                st.rerun()
                    
                    st.markdown("---")
        else:
            st.info("No criteria defined yet. Add your first criteria above!")


if __name__ == "__main__":
    main()

