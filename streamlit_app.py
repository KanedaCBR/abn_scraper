"""
ABN Browser - Streamlit UI for searching and browsing ABN entities.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from db_queries import (
    get_dashboard_stats, search_entities, get_entity_detail,
    get_entity_types, get_states, get_analytics_data,
    get_postcodes, get_analytics_data_filtered, get_map_data,
    get_postcodes_by_state
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
        --primary-color: #4a5a8a;
        --header-bg: #3d4a6e;
        --card-bg: #2a3550;
        --bg-dark: #1a1a2e;
    }
    
    /* Solid header - no gradient */
    .main-header {
        background: #3d4a6e;
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
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Metric cards - solid color */
    .metric-card {
        background: #4a5a8a;
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
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
    
    /* Entity card - solid color */
    .entity-card {
        background: #2a3550;
        border: 1px solid rgba(102, 126, 234, 0.3);
        padding: 1.5rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        color: white;
    }
    
    .entity-abn {
        font-family: 'Courier New', monospace;
        font-size: 1.2rem;
        color: #8899cc;
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
    
    /* Section headers - solid darker blue */
    .section-header {
        background: #3d4a6e;
        padding: 0.75rem 1rem;
        border-radius: 0.5rem;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.1rem;
        color: white;
    }
    
    /* Status badges - solid colors */
    .badge-active {
        background: #2e7d6a;
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
    
    /* Sidebar styling - solid color */
    [data-testid="stSidebar"] {
        background: #1a2235;
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

# Initialize page in session state if not present
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"

# Navigation pages list
NAV_PAGES = ["🏠 Dashboard", "🔍 Search", "📋 Entity Detail", "📊 Analytics", "🗺️ Map View"]

# Ensure session state page is valid
if st.session_state.current_page not in NAV_PAGES:
    st.session_state.current_page = "🏠 Dashboard"

page = st.sidebar.radio(
    "Navigation",
    NAV_PAGES,
    index=NAV_PAGES.index(st.session_state.current_page),
    label_visibility="collapsed"
)

# Update session state when radio changes
if page != st.session_state.current_page:
    st.session_state.current_page = page

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
                st.plotly_chart(fig, width="stretch")
        
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
                st.plotly_chart(fig, width="stretch")
    
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
                        st.session_state.current_page = "📋 Entity Detail"
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
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("No status history available")
                
                # Location History
                st.markdown('<div class="section-header">📍 Location History</div>', unsafe_allow_html=True)
                if entity_data['location_history']:
                    df = pd.DataFrame(entity_data['location_history'])
                    df['is_current'] = df['is_current'].apply(lambda x: '✅ Current' if x else '➖ Historical')
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("No location history available")
                
                # Two column layout for names
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown('<div class="section-header">🏢 Business Names</div>', unsafe_allow_html=True)
                    if entity_data['business_names']:
                        df = pd.DataFrame(entity_data['business_names'])
                        st.dataframe(df, width="stretch", hide_index=True)
                    else:
                        st.info("No business names registered")
                
                with col2:
                    st.markdown('<div class="section-header">🏷️ Trading Names</div>', unsafe_allow_html=True)
                    if entity_data['trading_names']:
                        df = pd.DataFrame(entity_data['trading_names'])
                        st.dataframe(df, width="stretch", hide_index=True)
                    else:
                        st.info("No trading names registered")
                
                # GST History
                st.markdown('<div class="section-header">💰 GST Registration History</div>', unsafe_allow_html=True)
                if entity_data['gst_history']:
                    df = pd.DataFrame(entity_data['gst_history'])
                    df['is_current'] = df['is_current'].apply(lambda x: '✅ Current' if x else '➖ Historical')
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("No GST registration history")
                
                # ASIC Registration
                st.markdown('<div class="section-header">🏛️ ASIC Registration</div>', unsafe_allow_html=True)
                if entity_data['asic_registration']:
                    df = pd.DataFrame(entity_data['asic_registration'])
                    st.dataframe(df, width="stretch", hide_index=True)
                else:
                    st.info("No ASIC registration linked")
            
            else:
                st.warning(f"No entity found with ABN: {abn_input}")
        
        except Exception as e:
            st.error(f"⚠️ Error loading entity: {e}")

# ============================================================
# ANALYTICS PAGE (with filters)
# ============================================================
elif page == "📊 Analytics":
    st.markdown("""
    <div class="main-header">
        <h1>📊 Analytics</h1>
        <p>Insights and trends from the ABN registry data</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Filters row
        st.markdown('<div class="section-header">🔧 Filters</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            states = ["All States"] + get_states()
            analytics_state = st.selectbox("State", states, key="analytics_state")
        
        with col2:
            # Constrain postcodes by selected state
            if analytics_state != "All States":
                postcodes = ["All Postcodes"] + get_postcodes_by_state(analytics_state)
            else:
                postcodes = ["All Postcodes"] + get_postcodes()
            
            # Reset postcode if current value not in new list
            current_postcode = st.session_state.get("analytics_postcode", "All Postcodes")
            if current_postcode not in postcodes:
                st.session_state["analytics_postcode"] = "All Postcodes"
            
            analytics_postcode = st.selectbox("Postcode", postcodes, key="analytics_postcode")
        
        with col3:
            # Entity type filter uses high-level categories
            high_level_types = ["All Types", "Individual / Sole Trader", "Partnership", "Trust", "Company", "Superannuation Fund"]
            analytics_entity_type = st.selectbox("Entity Type", high_level_types, key="analytics_entity_type")
        
        with col4:
            # Toggle for entity type chart detail level
            show_detailed_types = st.checkbox("Show detailed entity types", value=False, key="show_detailed_types")
        
        # Get filtered data
        filtered_analytics = get_analytics_data_filtered(
            state=analytics_state if analytics_state != "All States" else None,
            postcode=analytics_postcode if analytics_postcode != "All Postcodes" else None,
            entity_type=analytics_entity_type if analytics_entity_type != "All Types" else None
        )
        
        # Filtered count metric
        st.markdown(f"**Showing {filtered_analytics['filtered_count']:,} entities matching filters**")
        st.markdown("---")
        
        # Two column layout for charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Entity Type Chart - toggle between high-level and detailed
            if show_detailed_types:
                st.markdown('<div class="section-header">📊 Entity Types (Detailed)</div>', unsafe_allow_html=True)
                entity_type_data = filtered_analytics.get('entity_types_detailed', [])
            else:
                st.markdown('<div class="section-header">📊 Entity Types (High-Level)</div>', unsafe_allow_html=True)
                entity_type_data = filtered_analytics.get('entity_types_high_level', [])
            
            if entity_type_data:
                df = pd.DataFrame(entity_type_data)
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
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("No data for current filters")
        
        with col2:
            # Context-sensitive distribution chart
            if analytics_state != "All States":
                # Show POSTCODE distribution when state is selected
                st.markdown(f'<div class="section-header">📍 Postcode Distribution ({analytics_state})</div>', unsafe_allow_html=True)
                if filtered_analytics.get('postcode_distribution'):
                    df = pd.DataFrame(filtered_analytics['postcode_distribution'])
                    fig = px.bar(
                        df, x='postcode', y='count',
                        color='count',
                        color_continuous_scale='Purples'
                    )
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font_color='white',
                        xaxis_title="Postcode",
                        yaxis_title="Count",
                        showlegend=False
                    )
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No postcode data for current filters")
            else:
                # Show STATE distribution when no state selected
                st.markdown('<div class="section-header">📍 State Distribution</div>', unsafe_allow_html=True)
                if filtered_analytics.get('state_distribution'):
                    df = pd.DataFrame(filtered_analytics['state_distribution'])
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
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("No state data for current filters")
        
        # Registrations by year
        st.markdown('<div class="section-header">📅 Registrations by Year</div>', unsafe_allow_html=True)
        if filtered_analytics.get('by_year'):
            df = pd.DataFrame(filtered_analytics['by_year'])
            fig = px.line(
                df, x='year', y='count',
                markers=True,
                color_discrete_sequence=['#4a5a8a']
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                xaxis_title="Year",
                yaxis_title="New Registrations"
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=10))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No registration data for current filters")
    
    except Exception as e:
        st.error(f"⚠️ Error loading analytics: {e}")

# ============================================================
# MAP VIEW PAGE
# ============================================================
elif page == "🗺️ Map View":
    st.markdown("""
    <div class="main-header">
        <h1>🗺️ Map View</h1>
        <p>Geographic distribution of ABN entities by postcode</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Filters - same as Analytics page
        st.markdown('<div class="section-header">🔧 Filters</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            states = ["All States"] + get_states()
            map_state = st.selectbox("State", states, key="map_state")
        
        with col2:
            # Constrain postcodes by selected state
            if map_state != "All States":
                postcodes = ["All Postcodes"] + get_postcodes_by_state(map_state)
            else:
                postcodes = ["All Postcodes"] + get_postcodes()
            
            # Reset postcode if current value not in new list
            current_postcode = st.session_state.get("map_postcode", "All Postcodes")
            if current_postcode not in postcodes:
                st.session_state["map_postcode"] = "All Postcodes"
            
            map_postcode = st.selectbox("Postcode", postcodes, key="map_postcode")
        
        with col3:
            # Entity type filter uses high-level categories
            high_level_types = ["All Types", "Individual / Sole Trader", "Partnership", "Trust", "Company", "Superannuation Fund"]
            map_entity_type = st.selectbox("Entity Type", high_level_types, key="map_entity_type")
        
        # Get map data with all filters
        map_data = get_map_data(
            state=map_state if map_state != "All States" else None,
            postcode=map_postcode if map_postcode != "All Postcodes" else None,
            entity_type=map_entity_type if map_entity_type != "All Types" else None
        )
        
        st.markdown(f"**{len(map_data):,} entities matching filters**")
        st.markdown("---")
        
        if map_data:
            # Australian postcode approximate coordinates
            # Using state centroids with slight random offset based on postcode for visualization
            state_coords = {
                'NSW': {'lat': -33.0, 'lon': 147.0},
                'VIC': {'lat': -37.0, 'lon': 144.5},
                'QLD': {'lat': -22.0, 'lon': 144.0},
                'WA': {'lat': -27.0, 'lon': 121.0},
                'SA': {'lat': -32.0, 'lon': 137.0},
                'TAS': {'lat': -42.0, 'lon': 146.5},
                'NT': {'lat': -19.5, 'lon': 133.0},
                'ACT': {'lat': -35.3, 'lon': 149.1},
            }
            
            # Aggregate by POSTCODE for map (not state)
            df = pd.DataFrame(map_data)
            postcode_counts = df.groupby(['postcode', 'state']).size().reset_index(name='count')
            
            # Generate approximate coordinates for each postcode
            # Using state centroid with offset based on postcode number
            def get_postcode_coords(row):
                state = row['state'].strip() if row['state'] else ''
                postcode = row['postcode'] if row['postcode'] else '0000'
                base = state_coords.get(state, {'lat': -25, 'lon': 135})
                
                # Use postcode digits to create offset within state
                try:
                    pc_num = int(postcode)
                    lat_offset = ((pc_num % 100) - 50) * 0.05
                    lon_offset = ((pc_num // 100 % 100) - 50) * 0.05
                except:
                    lat_offset = 0
                    lon_offset = 0
                
                return pd.Series({
                    'lat': base['lat'] + lat_offset,
                    'lon': base['lon'] + lon_offset
                })
            
            coords = postcode_counts.apply(get_postcode_coords, axis=1)
            postcode_counts['lat'] = coords['lat']
            postcode_counts['lon'] = coords['lon']
            
            # Create map with POSTCODE-level markers
            st.markdown('<div class="section-header">🗺️ Entity Distribution by Postcode</div>', unsafe_allow_html=True)
            fig = px.scatter_geo(
                postcode_counts,
                lat='lat',
                lon='lon',
                size='count',
                color='count',
                hover_name='postcode',
                hover_data={'state': True, 'count': True, 'lat': False, 'lon': False},
                color_continuous_scale='Purples',
                size_max=30,
                scope='world'
            )
            fig.update_geos(
                visible=True,
                resolution=50,
                showcountries=True,
                countrycolor="Gray",
                showcoastlines=True,
                coastlinecolor="Gray",
                showland=True,
                landcolor="rgb(30, 30, 50)",
                showocean=True,
                oceancolor="rgb(20, 20, 40)",
                center=dict(lat=-27, lon=135),
                projection_scale=4
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                geo_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=500,
                margin=dict(l=0, r=0, t=0, b=0)
            )
            st.plotly_chart(fig, width="stretch")
            
            # Entity table - limited columns
            st.markdown('<div class="section-header">📋 Entity List</div>', unsafe_allow_html=True)
            display_df = df[['abn', 'entity_name', 'entity_type', 'state', 'postcode']].copy()
            display_df.columns = ['ABN', 'Entity Name', 'Entity Type', 'State', 'Postcode']
            st.dataframe(display_df, width="stretch", hide_index=True, height=400)
        else:
            st.info("No entities found matching the selected filters.")
    
    except Exception as e:
        st.error(f"⚠️ Error loading map data: {e}")

# Footer
st.markdown("---")
st.markdown(
    "<center style='color: #666; font-size: 0.8rem;'>ABN Browser • Built with Streamlit • Data from ABR</center>",
    unsafe_allow_html=True
)
