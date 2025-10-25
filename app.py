# app.py
import streamlit as st
import pandas as pd
from utils.io import load_data, load_geojson
from utils.prep import clean_and_prep_data
from utils.viz import (
    plot_kpi_metrics,
    plot_choropleth_map,
    plot_age_pyramid,
    plot_top_federations
)

# --- 1. Page Configuration ---
# Set page config as the first Streamlit command
st.set_page_config(
    page_title="French Sports Licenses Dashboard",
    page_icon="🏅",
    layout="wide"
)

# --- 2. Load and Prepare Data ---
# Load data using cached functions 
raw_df = load_data()
geojson = load_geojson()
df_main, f_cols, h_cols = clean_and_prep_data(raw_df)

st.session_state['f_cols'] = f_cols
st.session_state['h_cols'] = h_cols

if df_main.empty or geojson is None:
    st.error("Failed to load critical data. The app cannot continue.")
    st.stop()

# --- 3. Sidebar Filters ---
# Place all controls in the sidebar
with st.sidebar:
    st.image("assets/efrei_logo.png", width=200)
    st.header("Filters")
    
    # Get unique sorted lists for filters
    all_feds = sorted(df_main['Fédération'].unique())
    all_regions = sorted(df_main['Région'].unique())
    
    # Create filters
    # The user's request: filter by sports. Default is empty (all sports).
    selected_feds = st.multiselect(
        "Select Federation(s)",
        all_feds,
        default=[]
    )
    
    selected_regions = st.multiselect(
        "Select Region(s)",
        all_regions,
        default=[]
    )

    selected_gender = st.radio(
        "Select Gender",
        ["All", "Male", "Female"],
        horizontal=True # C'est plus joli
    )

    st.markdown("---")
    st.markdown("Project by **Enzo Houssiere**")

# --- 4. Filtering Logic ---
# Create the filtered DataFrame based on selections
df_filtered = df_main.copy()

if selected_feds:
    df_filtered = df_filtered[df_filtered['Fédération'].isin(selected_feds)]
if selected_regions:
    df_filtered = df_filtered[df_filtered['Région'].isin(selected_regions)]

f_cols = st.session_state.get('f_cols', [])
h_cols = st.session_state.get('h_cols', [])

if selected_gender == "Male":
    # Remplacer 'Total_Licences' pour ne compter que les hommes
    df_filtered['Total_Licences'] = df_filtered['Male_Licences']
    # Mettre à zéro les femmes pour les KPIs et la pyramide
    df_filtered['Female_Licences'] = 0
    for col in f_cols:
        if col in df_filtered.columns:
            df_filtered[col] = 0

elif selected_gender == "Female":
    # Remplacer 'Total_Licences' pour ne compter que les femmes
    df_filtered['Total_Licences'] = df_filtered['Female_Licences']
    # Mettre à zéro les hommes pour les KPIs et la pyramide
    df_filtered['Male_Licences'] = 0
    for col in h_cols:
         if col in df_filtered.columns:
            df_filtered[col] = 0

# --- 5. Main Page Layout ---
st.title("🏅 French Sports Licenses Data Story")
st.caption("Source: data.gouv.fr - Recensement des licences et clubs 2022")

st.markdown(
    """
    Welcome! This dashboard answers three key questions about sports in France:
    - **What** are the most popular sports?
    - **Where** are they played?
    - **Who** plays them (age and gender)?
    
    Use the filters on the left to explore the data.
    """
)

# Check if filters resulted in empty data
if df_filtered.empty:
    st.warning("No data matches your selection. Please adjust the filters.")
    st.stop()

# --- Section 1: KPIs ---
# Display KPIs based on filtered data
st.subheader("Dashboard Overview for Selection")
plot_kpi_metrics(df_filtered)

st.markdown("---")

# --- Section 2: Map and Age Pyramid ---
st.subheader("The 'Where' and 'Who' of French Sports")
col1, col2 = st.columns([2, 1]) # Give more space to the map

with col1:
    # Map is mandatory
    fig_map = plot_choropleth_map(df_filtered, geojson)
    st.plotly_chart(fig_map, use_container_width=True)

with col2:
    # Age pyramid (one of 3+ interactive visuals)
    fig_pyramid = plot_age_pyramid(df_filtered)
    st.plotly_chart(fig_pyramid, use_container_width=True)

st.markdown("---")

# --- Section 3: Federation Rankings ---
st.subheader("What are the most popular sports?")

col_bar1, col_bar2 = st.columns(2)

with col_bar1:
    # Second interactive visual
    fig_bar_lic = plot_top_federations(df_filtered, by='licences')
    st.plotly_chart(fig_bar_lic, use_container_width=True)

with col_bar2:
    # Third interactive visual
    fig_bar_imp = plot_top_federations(df_filtered, by='implantation')
    st.plotly_chart(fig_bar_imp, use_container_width=True)

st.markdown("---")

# --- Section 4: Data Quality & Insights (Mandatory) ---
col_dq, col_in = st.columns(2)

with col_dq:
    st.markdown("### Data Quality & Limitations")
    st.info(
        """
        - The dataset is a 2022 census. It does not show trends over time.
        - Geographic data is based on the commune of the association's headquarters, not necessarily all practice locations.
        - "NR" (Not Reported) age groups are excluded from the age pyramid.
        - Some associations may be missing geocoding (`latitude`/`longitude`), but they are still included in department-level statistics.
        """
    )

with col_in:
    st.markdown("### Key Insights & Next Steps")
    st.success(
        """
        - **Story:** The app reveals the 'Where', 'Who', and 'What' of French sports.
        - **Insight 1:** Popularity is twofold: Football dominates by *licence count*, but Tennis shows a wider *geographic implantation*.
        - **Insight 2:** The age pyramid for "all sports" shows a massive peak for 5-14 year olds, highlighting the role of clubs in youth activity.
        - **Next Steps:** We could cross-reference this data with population density (INSEE) to find underserved areas (licences per capita).
        """
    )