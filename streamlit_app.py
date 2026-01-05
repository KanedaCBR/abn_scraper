"""
ABN Browser - Streamlit UI for searching and browsing ABN entities.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db_queries import (
    get_dashboard_stats, search_entities, get_entity_detail,
    get_entity_types, get_states, get_analytics_data
)

# Page configuration
st.set_page_config(
    page_title="ABN Browser",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --accent-color: #f093fb;
        --bg-dark: #1a1a2e;
        --card-bg: rgba(255, 255, 255, 0.05);
    }
    
    /* Gradient header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.5rem;
    }
    
    /* Entity card */
    .entity-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        color: white;
    }
    
    .entity-abn {
        font-family: 'Courier New', monospace;
        font-size: 1.2rem;
        color: #667eea;
        font-weight: 600;
    }
    
    .entity-name {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .entity-type {
        background: rgba(102, 126, 234, 0.2);
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        display: inline-block;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, transparent 100%);
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.1rem;
    }
    
    /* Status badges */
    .badge-active {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-inactive {
        background: rgba(255, 255, 255, 0.1);
        color: #888;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.8rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }
    
    /* Table styling */
    .dataframe {
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("## 🔍 ABN Browser")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏠 Dashboard", "🔍 Search", "📋 Entity Detail", "📊 Analytics"],
    label_visibility="collapsed"
)

# ============================================================
# DASHBOARD PAGE
# ============================================================
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>🔍 ABN Browser</h1>
        <p>Australian Business Number Registry Explorer</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        stats = get_dashboard_stats()
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats['total_entities']:,}</div>
                <div class="metric-label">Total Entities</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats['total_documents']:,}</div>
                <div class="metric-label">Documents Ingested</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            success_rate = stats['document_status'].get('SUCCESS', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{success_rate:,}</div>
                <div class="metric-label">Successful Ingestions</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{stats['gst_current']:,}</div>
                <div class="metric-label">Current GST Registrations</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-header">📊 Entity Types</div>', unsafe_allow_html=True)
            if stats['entity_types']:
                df = pd.DataFrame(stats['entity_types'])
                fig = px.pie(
                    df, values='count', names='entity_type',
                    color_discrete_sequence=px.colors.sequential.Purples_r,
                    hole=0.4
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.3)
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown('<div class="section-header">📍 State Distribution</div>', unsafe_allow_html=True)
            if stats['state_distribution']:
                df = pd.DataFrame(stats['state_distribution'])
                fig = px.bar(
                    df, x='state', y='count',
                    color='count',
                    color_continuous_scale='Purples'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    xaxis_title="State",
                    yaxis_title="Count",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"⚠️ Database connection error: {e}")
        st.info("Make sure PostgreSQL is running on localhost:5432")

# ============================================================
# SEARCH PAGE
# ============================================================
elif page == "🔍 Search":
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Entity Search</h1>
        <p>Search by ABN, entity name, trading name, or business name</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Search filters
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "🔎 Search",
                placeholder="Enter ABN, entity name, trading name...",
                label_visibility="collapsed"
            )
        
        with col2:
            entity_types = ["All Types"] + get_entity_types()
            selected_type = st.selectbox("Entity Type", entity_types)
        
        with col3:
            states = ["All States"] + get_states()
            selected_state = st.selectbox("State", states)
        
        # Pagination
        if 'page_num' not in st.session_state:
            st.session_state.page_num = 0
        
        per_page = 20
        offset = st.session_state.page_num * per_page
        
        # Execute search
        results = search_entities(
            query=search_query,
            entity_type=selected_type if selected_type != "All Types" else None,
            state=selected_state if selected_state != "All States" else None,
            limit=per_page,
            offset=offset
        )
        
        st.markdown(f"**{results['total']:,}** entities found", unsafe_allow_html=True)
        st.markdown("---")
        
        # Results
        if results['results']:
            for entity in results['results']:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                    <div class="entity-card">
                        <div class="entity-abn">ABN: {entity['abn']}</div>
                        <div class="entity-name">{entity['entity_name'] or 'Unknown'}</div>
                        <span class="entity-type">{entity['entity_type'] or 'Unknown'}</span>
                        <span style="margin-left: 1rem; color: #888;">
                            📍 {entity['state'] or 'N/A'} {entity['postcode'] or ''}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("View Details", key=f"view_{entity['abn']}"):
                        st.session_state.selected_abn = entity['abn']
                        st.rerun()
            
            # Pagination controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.session_state.page_num > 0:
                    if st.button("← Previous"):
                        st.session_state.page_num -= 1
                        st.rerun()
            with col2:
                total_pages = (results['total'] + per_page - 1) // per_page
                st.markdown(f"<center>Page {st.session_state.page_num + 1} of {total_pages}</center>", unsafe_allow_html=True)
            with col3:
                if offset + per_page < results['total']:
                    if st.button("Next →"):
                        st.session_state.page_num += 1
                        st.rerun()
        else:
            st.info("No entities found matching your criteria.")
    
    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# ============================================================
# ENTITY DETAIL PAGE
# ============================================================
elif page == "📋 Entity Detail":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Entity Details</h1>
        <p>Complete profile with all historical data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ABN input
    col1, col2 = st.columns([3, 1])
    with col1:
        abn_input = st.text_input(
            "Enter ABN",
            value=st.session_state.get('selected_abn', ''),
            placeholder="e.g., 11009413629"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        load_button = st.button("🔍 Load Entity", type="primary")
    
    if abn_input and (load_button or st.session_state.get('selected_abn')):
        try:
            entity_data = get_entity_detail(abn_input.strip())
            
            if entity_data:
                entity = entity_data['entity']
                
                # Entity header
                st.markdown(f"""
                <div class="entity-card">
                    <div class="entity-abn">ABN: {entity['abn']}</div>
                    <div class="entity-name">{entity['entity_name']}</div>
                    <span class="entity-type">{entity['entity_type']}</span>
                    <div style="margin-top: 1rem; color: #888;">
                        First Active: {entity['first_active_date'] or 'N/A'} | 
                        Last Updated: {entity['abn_last_updated_date'] or 'N/A'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Status History
                st.markdown('<div class="section-header">📊 Status History</div>', unsafe_allow_html=True)
                if entity_data['status_history']:
                    df = pd.DataFrame(entity_data['status_history'])
                    df['is_current'] = df['is_current'].apply(lambda x: '✅ Current' if x else '➖ Historical')
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No status history available")
                
                # Location History
                st.markdown('<div class="section-header">📍 Location History</div>', unsafe_allow_html=True)
                if entity_data['location_history']:
                    df = pd.DataFrame(entity_data['location_history'])
                    df['is_current'] = df['is_current'].apply(lambda x: '✅ Current' if x else '➖ Historical')
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No location history available")
                
                # Two column layout for names
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="section-header">🏢 Business Names</div>', unsafe_allow_html=True)
                    if entity_data['business_names']:
                        df = pd.DataFrame(entity_data['business_names'])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No business names registered")
                
                with col2:
                    st.markdown('<div class="section-header">🏷️ Trading Names</div>', unsafe_allow_html=True)
                    if entity_data['trading_names']:
                        df = pd.DataFrame(entity_data['trading_names'])
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No trading names registered")
                
                # GST History
                st.markdown('<div class="section-header">💰 GST Registration History</div>', unsafe_allow_html=True)
                if entity_data['gst_history']:
                    df = pd.DataFrame(entity_data['gst_history'])
                    df['is_current'] = df['is_current'].apply(lambda x: '✅ Current' if x else '➖ Historical')
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No GST registration history")
                
                # ASIC Registration
                st.markdown('<div class="section-header">🏛️ ASIC Registration</div>', unsafe_allow_html=True)
                if entity_data['asic_registration']:
                    df = pd.DataFrame(entity_data['asic_registration'])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No ASIC registration linked")
            
            else:
                st.warning(f"No entity found with ABN: {abn_input}")
        
        except Exception as e:
            st.error(f"⚠️ Error loading entity: {e}")

# ============================================================
# ANALYTICS PAGE
# ============================================================
elif page == "📊 Analytics":
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analytics</h1>
        <p>Insights and trends from the ABN registry data</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        analytics = get_analytics_data()
        
        # Registrations by year
        st.markdown('<div class="section-header">📅 Registrations by Year</div>', unsafe_allow_html=True)
        if analytics['by_year']:
            df = pd.DataFrame(analytics['by_year'])
            fig = px.line(
                df, x='year', y='count',
                markers=True,
                color_discrete_sequence=['#667eea']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                xaxis_title="Year",
                yaxis_title="New Registrations"
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=10))
            st.plotly_chart(fig, use_container_width=True)
        
        # Two column layout
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="section-header">🏷️ Trading Name Reuse</div>', unsafe_allow_html=True)
            st.caption("Trading names used by multiple ABNs")
            if analytics['trading_name_reuse']:
                df = pd.DataFrame(analytics['trading_name_reuse'])
                fig = px.bar(
                    df, x='abn_count', y='trading_name',
                    orientation='h',
                    color='abn_count',
                    color_continuous_scale='Purples'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    xaxis_title="Number of ABNs",
                    yaxis_title="",
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No trading name reuse detected")
        
        with col2:
            st.markdown('<div class="section-header">📍 Location Changes</div>', unsafe_allow_html=True)
            st.caption("Entities with the most address changes")
            if analytics['location_changes']:
                df = pd.DataFrame(analytics['location_changes'])
                df['display_name'] = df['entity_name'].str[:30] + '...'
                fig = px.bar(
                    df, x='location_changes', y='display_name',
                    orientation='h',
                    color='location_changes',
                    color_continuous_scale='Oranges'
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    xaxis_title="Location Changes",
                    yaxis_title="",
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location changes detected")
    
    except Exception as e:
        st.error(f"⚠️ Error loading analytics: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<center style='color: #666; font-size: 0.8rem;'>ABN Browser • Built with Streamlit • Data from ABR</center>",
    unsafe_allow_html=True
)
