# utils/viz.py
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def simple_si_format(val):
    """Formate un nombre en 'k' (milliers) ou 'M' (millions)"""
    val = abs(val)
    if val >= 1_000_000:
        return f'{val/1_000_000:.0f}M' # ex: 1M
    if val >= 1_000:
        return f'{val/1_000:.0f}k' # ex: 500k
    return f'{val:.0f}' # ex: 0

def plot_kpi_metrics(df_filtered):
    """
    Displays the 4 main KPIs in st.metric columns.
    Calculates KPIs based *only* on the filtered data.
    """
    # Calculate KPIs from the filtered dataframe
    total_licences = df_filtered['Total_Licences'].sum()
    total_associations = len(df_filtered)

    if total_associations > 0:
        avg_lic_per_club = total_licences / total_associations
    else:
        avg_lic_per_club = 0

    # Create 3 columns for metrics
    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="Total Licences",
        value=f"{total_licences:,.0f}"
    )
    col2.metric(
        label="Total Associations (Clubs)",
        value=f"{total_associations:,.0f}"
    )
    col3.metric(
        label="Avg. Licences per Club",
        value=f"{avg_lic_per_club:,.1f}" # On affiche avec une décimale
    )

def plot_choropleth_map(df_filtered, geojson):
    """
    Creates the choropleth mapbox figure based on filtered data.
    """
    # Aggregate filtered data by department
    df_dept = df_filtered.groupby('Département').agg(
        Total_Licences=('Total_Licences', 'sum'),
        Nb_Associations=('Code Commune', 'count')
    ).reset_index()

    fig = px.choropleth_mapbox(
        df_dept, 
        geojson=geojson, 
        locations='Département',         # Column in df
        featureidkey="properties.code",  # Key in geojson
        color='Total_Licences',
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=4.5, 
        center={"lat": 46.603354, "lon": 1.888334},
        opacity=0.7,
        hover_name='Département',
        hover_data={
            'Nb_Associations': ':,0f', 
            'Total_Licences': ':,0f'
        },
        labels={
            'Total_Licences': 'Total Licences', 
            'Nb_Associations': 'Nb. of Associations'
        }
    )
    fig.update_layout(
        title="Where are the athletes?",
        margin={"r":0, "t":40, "l":0, "b":0}
    )
    return fig

def plot_age_pyramid(df_filtered):
    """
    Creates the age pyramid for the selected federations.
    CORRECTED:
    - Fixed order of operations for data_h['Abs_Licences']
    - Moved 'data_pyramide.empty' check to *after* concatenation
    """
    # Retrieve column lists from session_state
    f_cols = st.session_state.get('f_cols', [])
    h_cols = st.session_state.get('h_cols', [])

    if not f_cols or not h_cols:
        return go.Figure().update_layout(title="Age pyramid data not available.")

    if df_filtered.empty:
        return go.Figure().update_layout(title="No data for this selection.")
    
    # Aggregate all data in the filtered selection
    data_agg = df_filtered[f_cols + h_cols].sum()
    
    data_f = data_agg[f_cols].reset_index()
    data_f.columns = ['Tranche', 'Licences']
    data_f['Tranche'] = data_f['Tranche'].str.replace('F - ', '')
    data_f['Sexe'] = 'Female'
    data_f['Abs_Licences'] = data_f['Licences']
    
    data_h = data_agg[h_cols].reset_index()
    data_h.columns = ['Tranche', 'Licences']
    data_h['Tranche'] = data_h['Tranche'].str.replace('H - ', '')
    data_h['Sexe'] = 'Male'
    data_h['Abs_Licences'] = data_h['Licences']
    data_h['Licences'] = -data_h['Licences']
    
    # 3. Create the dataframe FIRST
    data_pyramide = pd.concat([data_f, data_h])

    # 4. Check if it's empty AFTER creation
    if data_pyramide.empty:
       return go.Figure().update_layout(title="No age data to display.")
    
    # Define the correct order
    age_order = [
        '1 à 4 ans', '5 à 9 ans', '10 à 14 ans', '15 à 19 ans', 
        '20 à 24 ans', '25 à 29 ans', '30 à 34 ans', '35 à 39 ans', 
        '40 à 44 ans', '45 à 49 ans', '50 à 54 ans', '55 à 59 ans', 
        '60 à 64 ans', '65 à 69 ans', '70 à 74 ans', '75 à 79 ans', '80 à 99 ans', 'NR'
    ]

    fig = px.bar(
        data_pyramide,
        y='Tranche',
        x='Licences',
        color='Sexe',
        orientation='h',
        title='Who are the athletes? (Age & Gender Pyramid)',
        category_orders={'Tranche': age_order},
        labels={'Licences': 'Number of Licences'},
        barmode='relative',
        template='plotly_white',
        color_discrete_map={'Female': 'purple', 'Male': 'orange'},
        custom_data=['Sexe', 'Abs_Licences']
    )
    
    # Clean up tooltips and axes
    fig.update_traces(
        hovertemplate='Sexe: %{customdata[0]}<br>Age: %{y}<br>Licences: %{customdata[1]:,.0f}<extra></extra>'
    )

    # This check is now redundant, but safe
    if 'Abs_Licences' not in data_pyramide.columns:
            st.error("Data error: 'Abs_Licences' column is missing.")
            return fig

    # This line (131 in your old file) should now work
    max_val = data_pyramide['Abs_Licences'].max() 
    max_val = max_val * 1.1

    # Handle case where max_val is 0
    if max_val == 0:
        max_val = 100 # Default axis range
    
    tick_vals = np.linspace(-max_val, max_val, 5)
    tick_text = [simple_si_format(val) for val in tick_vals]

    fig.update_layout(
        xaxis_title='Number of Licences', 
        yaxis_title='Age Group',
        xaxis=dict(
            tickvals=tick_vals,
            ticktext=tick_text,
            range=[-max_val, max_val]
        )
    )
    return fig

def plot_top_federations(df_filtered, by='licences'):
    """
    Creates horizontal bar charts for top 15 federations.
    Can plot by 'licences' or 'implantation'.
    """
    if by == 'licences':
        df_agg = df_filtered.groupby('Fédération')['Total_Licences'].sum().nlargest(15).reset_index().sort_values(by='Total_Licences', ascending=True)
        x_col = 'Total_Licences'
        title = 'Top 15 Federations by Licences'
        x_label = 'Total Licences'
    else:
        # Count number of rows (associations)
        df_agg = df_filtered['Fédération'].value_counts().nlargest(15).reset_index().sort_values(by='count', ascending=True)
        df_agg.columns = ['Fédération', 'Count']
        x_col = 'Count'
        title = 'Top 15 Federations by Implantation'
        x_label = 'Number of Associations'

    fig = px.bar(
        df_agg,
        x=x_col,
        y='Fédération',
        orientation='h',
        title=title,
        labels={x_col: x_label, 'Fédération': ''},
        text=x_col
    )
    fig.update_traces(texttemplate='%{text:,.0s}', textposition='outside')
    fig.update_layout(yaxis=dict(tickfont=dict(size=10)))
    return fig