import streamlit as st
import pandas as pd
from db import engine
from version_control import restore_ag_version

def render():
    st.header("Load Past Versions")

    with engine.begin() as conn:
        versions = pd.read_sql("SELECT * FROM ag_versions ORDER BY timestamp DESC", conn)

    version_list = versions['version_name'].tolist()
    selected_version = st.selectbox("Select a version to load into 'pilot_ag_master':", version_list)

    if st.button("Restore this version"):
        msg = restore_ag_version(selected_version)
        st.success(msg)

        with engine.begin() as conn:
            df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)
        st.dataframe(df.head(20), use_container_width=True)