# utils/io.py
import streamlit as st
import pandas as pd
import requests

# This is the dataset URL from your prompt
DATA_URL = "https://www.data.gouv.fr/api/1/datasets/r/ce39c9d6-2e7f-4a05-9f95-9e6c06b38219"

# This is a reliable GeoJSON for French departments
GEOJSON_URL = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements.geojson"

@st.cache_data(show_spinner="Loading license data...")
def load_data():
    """
    Loads the main sports license dataset from data.gouv.fr.
    Specifies dtypes for geographic codes to preserve leading zeros.
    """
    # Specify dtypes to keep codes like '01' or '2A' as strings
    dtypes_spec = {
        "Code Commune": str,
        "Code QPV": str,
        "Département": str,
        "Code": str, # Federation Code
    }
    
    try:
        df = pd.read_csv(DATA_URL, sep=';', dtype=dtypes_spec)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Loading map data...")
def load_geojson():
    """
    Loads the GeoJSON file for department boundaries.
    """
    try:
        geojson = requests.get(GEOJSON_URL).json()
        return geojson
    except Exception as e:
        st.error(f"Error loading GeoJSON map: {e}")

        return None
