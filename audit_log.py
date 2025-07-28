import streamlit as st
import pandas as pd
from db import engine

def render():
    st.header("Audit Trail: Version Activity Log")

    with engine.begin() as conn:
        df = pd.read_sql("SELECT * FROM ag_audit_log ORDER BY timestamp DESC", conn)

    st.dataframe(df, use_container_width=True)