import streamlit as st
import pandas as pd
from io import BytesIO
from db import engine
from version_control import save_ag_version

def render():
    st.header("Merged AG + DevCo Export")

    # Get merged data from DB
    with engine.connect() as conn:
        ag_df = pd.read_sql("SELECT * FROM pilot_ag_master", conn)
        devco_df = pd.read_sql("SELECT * FROM devco_submissions", conn)

    # Get latest per data_point_id by timestamp
    devco_df['timestamp'] = pd.to_datetime(devco_df['timestamp'], errors='coerce')
    devco_df = devco_df.sort_values('timestamp', ascending=False)
    latest_devco = devco_df.drop_duplicates('data_point_id', keep='first')

    # Merge manually
    merged_df = ag_df.merge(
        latest_devco[['data_point_id', 'value', 'submitted_at']],
        on='data_point_id',
        how='left'
    )

    merged_df.rename(columns={
        'value': 'devco_value',
        'submitted_at': 'submitted_at'
    }, inplace=True)

    # Add placeholder columns so the structure stays the same
    merged_df['devco_comment'] = ''
    merged_df['submitted_by'] = ''

    st.subheader("Merged AG Table Preview")
    st.dataframe(merged_df, use_container_width=True)

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        merged_df.to_excel(writer, index=False)
    buffer.seek(0)

    st.download_button(
        label="Download Merged AG as Excel",
        data=buffer,
        file_name="AG_with_Latest_DevCo_Submissions.xlsx",
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    st.markdown("---")
    st.subheader("Version Control")

    version_input = st.text_input("Enter version name to save:", value="v1_2025_07_11")
    if st.button("Save this AG as a new version"):
        msg = save_ag_version(version_input)
        st.success(msg)

    st.markdown("---")
    st.subheader("Load Past Versions")

    with engine.connect() as conn:
        version_df = pd.read_sql("SELECT * FROM ag_versions ORDER BY timestamp DESC", conn)

    version_names = version_df["version_name"].tolist()
    selected_version = st.selectbox("Select a version to view:", version_names)

    if selected_version:
        version_table = f"ag_snapshot__{selected_version}"
        with engine.connect() as conn:
            version_data = pd.read_sql(f"SELECT * FROM {version_table}", conn)
        st.dataframe(version_data, use_container_width=True)

        buffer2 = BytesIO()
        with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
            version_data.to_excel(writer, index=False)
        buffer2.seek(0)

        st.download_button(
            label=f"Download Snapshot: {selected_version}.xlsx",
            data=buffer2,
            file_name=f"{selected_version}.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )