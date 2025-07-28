import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter
from db import engine
from utils import clean_headers, extract_cleaned_df, ensure_columns, extract_dataframe_from_sheet
from datetime import datetime
from version_control import save_ag_version, log_ag_action

def render():
    st.header("Admin Panel: Upload Master AG (Multi-Sheet)")

    uploaded_file = st.file_uploader("Upload Master AG Excel", type=["xlsx"])
    if not uploaded_file:
        return

    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names

    selected_sheets = st.multiselect("Select Sheets to Include:", sheet_names)
    if not selected_sheets:
        st.info("Please select at least one sheet.")
        return

    dfs = []
    for sheet in selected_sheets:
        wb = openpyxl.load_workbook(uploaded_file, data_only=True)
        ws = wb[sheet]
        df_raw = extract_dataframe_from_sheet(ws)
        df = extract_cleaned_df(df_raw)
        df["section_id"] = sheet

        from utils import extract_field_type

        if "data_point" in df.columns:
            df["input_type"] = df["data_point"].apply(extract_field_type)
        else:
            df["input_type"] = "Text"
            
        df["devco_id"] = "admin"
        dfs.append(df)

    if not dfs:
        st.error("No sheets processed.")
        return

    final_df = pd.concat(dfs, ignore_index=True)
    ensure_columns(final_df)
    final_df.to_sql("pilot_ag_master", engine, if_exists="replace", index=False)
    version_name = f"upload_{datetime.now().strftime('%Y_%m_%d__%H%M%S')}"
    save_ag_version(version_name)
    st.success("Master AG uploaded successfully.")
    for sheet, df in zip(selected_sheets, dfs):
        st.subheader(f"Preview of: {sheet}")
        st.dataframe(df, use_container_width=True)