# utils/prep.py
import streamlit as st
import pandas as pd

@st.cache_data
def clean_and_prep_data(df_raw):
    """
    Cleans the raw DataFrame:
    1. Renames columns for clarity.
    2. Converts all age-group columns to numeric, filling NaNs with 0.
    3. Creates new columns for total Female and Male licenses.
    """
    if df_raw.empty:
        return pd.DataFrame()

    df = df_raw.copy()
    
    # 1. Rename 'Total' column
    df = df.rename(columns={"Total": "Total_Licences"})

    # 2. Find all age columns and convert to numeric
    age_cols = [col for col in df.columns if ' - ' in col]
    for col in age_cols + ['Total_Licences']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df[age_cols + ['Total_Licences']] = df[age_cols + ['Total_Licences']].fillna(0).astype(int)

    # 3. Create total columns for Gender
    f_cols = [col for col in age_cols if col.startswith('F - ')]
    h_cols = [col for col in age_cols if col.startswith('H - ')]

    df['Female_Licences'] = df[f_cols].sum(axis=1)
    df['Male_Licences'] = df[h_cols].sum(axis=1)
    
    return df, f_cols, h_cols