# app.py
"""
Meinhardt Assessment Guide WebApp
Integrated Phase 1 + Phase 2
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import traceback
from pathlib import Path

# Import your existing modules
from parsers.excel_parser import MasterFileParser
from database.json_db import JsonDatabase

# Import Phase 2 module
from master_file_module import MasterFileModule

# Import Phase 3 module
from main_ag_module import MainAGModule

# Configure the app
st.set_page_config(
    page_title="Meinhardt Assessment Guide",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional styling - enterprise grade
st.markdown("""
<style>
    .main { padding: 0rem 1rem; }
    .stButton > button {
        background-color: #1e3a8a;
        color: white;
        font-weight: 500;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #1e40af;
        transform: translateY(-1px);
    }
    div[data-testid="metric-container"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .uploadedFile {
        background-color: #f0f9ff;
        border: 2px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
    }
    h1 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        font-weight: 600;
        color: #1e293b;
    }
    h2 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #334155;
    }
</style>
""", unsafe_allow_html=True)

class MeinhardtApp:
    """Main application class with proper state management"""
    
    def __init__(self):
        self.db = JsonDatabase()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'parsed_data' not in st.session_state:
            st.session_state.parsed_data = None
        if 'parse_complete' not in st.session_state:
            st.session_state.parse_complete = False
        if 'save_complete' not in st.session_state:
            st.session_state.save_complete = False
    
    def run(self):
        """Main application entry point"""
        self.render_header()
        self.render_sidebar()
        self.render_main_content()
    
    def render_header(self):
        """Render application header"""
        col1, col2 = st.columns([4, 1])
        with col1:
            st.title("MEINHARDT ASSESSMENT GUIDE")
            st.caption("Enterprise Assessment Management System")
        with col2:
            if st.session_state.parse_complete and not st.session_state.save_complete:
                st.warning("Unsaved data")
    
    def render_sidebar(self):
        """Render sidebar navigation"""
        with st.sidebar:
            st.header("Navigation")
            
            # Navigation buttons - professional, no emojis
            if st.button("Dashboard", use_container_width=True):
                st.session_state.current_page = 'dashboard'
            
            if st.button("Upload & Parse", use_container_width=True):
                st.session_state.current_page = 'upload'
            
            # NEW: Master File Configuration button
            if st.button("Master File Configuration", use_container_width=True):
                st.session_state.current_page = 'master_config'
            
            if st.button("Main AG Module", use_container_width=True):
                st.session_state.current_page = 'main_ag'

            if st.button("View Database", use_container_width=True):
                st.session_state.current_page = 'database'
            
            if st.button("Analytics", use_container_width=True):
                st.session_state.current_page = 'analytics'
            
            if st.button("Export", use_container_width=True):
                st.session_state.current_page = 'export'
            
            st.divider()
            
            # Database status
            st.subheader("Database Status")
            stats = self.db.get_statistics()
            
            if stats and stats.get('total_dps', 0) > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Data Points**")
                    st.write(f"**{stats.get('total_dps', 0)}**")
                    st.write("**Criteria**")
                    st.write(f"**{stats.get('total_acs', 0)}**")
                with col2:
                    st.write("**Signals**")
                    st.write(f"**{stats.get('total_pss', 0)}**")
                    st.write("**Topics**")
                    st.write(f"**{stats.get('total_kts', 0)}**")
                
                if 'last_import' in stats:
                    st.caption(f"Last import: {stats['last_import'][:10]}")
            else:
                st.info("Database empty")
            
            st.divider()
            
            # Database management
            st.subheader("Database Management")
            with st.expander("Reset Options"):
                if st.checkbox("Confirm database reset"):
                    if st.button("Execute Reset", use_container_width=True, type="secondary"):
                        self.db.clear_database()
                        st.session_state.parsed_data = None
                        st.session_state.parse_complete = False
                        st.session_state.save_complete = False
                        st.success("Database reset complete")
                        st.rerun()
    
    def render_main_content(self):
        """Render main content based on current page"""
        if st.session_state.current_page == 'dashboard':
            self.render_dashboard()
        elif st.session_state.current_page == 'upload':
            self.render_upload_page()
        elif st.session_state.current_page == 'master_config':
            # NEW: Render Master File Configuration module
            self.render_master_config_page()
        elif st.session_state.current_page == 'main_ag':
            self.render_main_ag_page()
        elif st.session_state.current_page == 'database':
            self.render_database_page()
        elif st.session_state.current_page == 'analytics':
            self.render_analytics_page()
        elif st.session_state.current_page == 'export':
            self.render_export_page()
    
    def render_master_config_page(self):
        """Render Master File Configuration page (Phase 2)"""
        # Create instance of MasterFileModule and render it
        master_module = MasterFileModule()
        master_module.render()

    def render_main_ag_page(self):
        """Render Main AG Module page (Phase 3)"""
        # Check if database has data
        stats = self.db.get_statistics()
        if stats and stats.get('total_dps', 0) > 0:
            # Create instance of MainAGModule and render it
            main_ag_module = MainAGModule()
            main_ag_module.render()
        else:
            st.warning("No data in database. Please upload and parse a Master File first.")
            if st.button("Go to Upload & Parse", type="primary"):
                st.session_state.current_page = 'upload'
                st.rerun()
    
    def render_dashboard(self):
        """Render dashboard page"""
        st.header("Dashboard")
        
        stats = self.db.get_statistics()
        
        if stats and stats.get('total_dps', 0) > 0:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Data Points", stats.get('total_dps', 0))
            with col2:
                st.metric("Assessment Criteria", stats.get('total_acs', 0))
            with col3:
                st.metric("Performance Signals", stats.get('total_pss', 0))
            with col4:
                st.metric("Key Topics", stats.get('total_kts', 0))
            
            st.divider()
            
            # Quick Actions for Phase 2
            st.subheader("Quick Actions")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Configure Formulas", use_container_width=True):
                    st.session_state.current_page = 'master_config'
                    st.rerun()
            
            with col2:
                if st.button("Manage Weights", use_container_width=True):
                    st.session_state.current_page = 'master_config'
                    st.rerun()
            
            with col3:
                if st.button("Set Thresholds", use_container_width=True):
                    st.session_state.current_page = 'master_config'
                    st.rerun()
            
            st.divider()
            
            # Distribution analysis
            db_data = self.db.load_database()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Data Points by Pillar")
                pillar_counts = {}
                for dp in db_data.get('data_points', {}).values():
                    pillar = dp.get('pillar', 'Unknown')
                    pillar_counts[pillar] = pillar_counts.get(pillar, 0) + 1
                
                df = pd.DataFrame(list(pillar_counts.items()), columns=['Pillar', 'Count'])
                st.bar_chart(df.set_index('Pillar'))
            
            with col2:
                st.subheader("Data Types Distribution")
                type_counts = {}
                for dp in db_data.get('data_points', {}).values():
                    dtype = dp.get('data_type', 'Unknown')
                    type_counts[dtype] = type_counts.get(dtype, 0) + 1
                
                df = pd.DataFrame(list(type_counts.items()), columns=['Type', 'Count'])
                st.bar_chart(df.set_index('Type'))
            
            # System status
            st.divider()
            st.subheader("System Status")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.success("Database: Operational")
            with col2:
                st.success("Parser: Ready")
            with col3:
                st.success("Phase 2: Active")
        else:
            st.info("No data available. Upload and parse a Master File to get started.")
            
            # Direct link to upload
            if st.button("Go to Upload & Parse", type="primary"):
                st.session_state.current_page = 'upload'
                st.rerun()
    
    def render_upload_page(self):
        """Render upload and parse page"""
        st.header("Upload & Parse Master File")
        
        # Check for unsaved parsed data
        if st.session_state.parse_complete and st.session_state.parsed_data and not st.session_state.save_complete:
            self.render_save_section()
        else:
            self.render_upload_section()
    
    def render_upload_section(self):
        """Render file upload section"""
        st.markdown("### Select Master File")
        st.markdown("Upload the Excel file containing assessment criteria and data points.")
        
        uploaded_file = st.file_uploader(
            "Choose Excel file",
            type=['xlsx', 'xls'],
            help="Select the Master File in Excel format"
        )
        
        if uploaded_file:
            # File information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Filename:** {uploaded_file.name}")
            with col2:
                size_mb = uploaded_file.size / (1024 * 1024)
                st.info(f"**Size:** {size_mb:.2f} MB")
            with col3:
                st.info(f"**Format:** {'XLSX' if uploaded_file.name.endswith('.xlsx') else 'XLS'}")
            
            # Parse button
            if st.button("Parse Excel File", type="primary", use_container_width=True):
                self.parse_excel_file(uploaded_file)
    
    def parse_excel_file(self, uploaded_file):
        """Parse the uploaded Excel file"""
        temp_file = f"temp_{datetime.now().timestamp()}.xlsx"
        
        try:
            # Save uploaded file
            with open(temp_file, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Parse with progress indication
            progress = st.progress(0)
            status = st.empty()
            
            status.text("Initializing parser...")
            progress.progress(20)
            
            parser = MasterFileParser(temp_file)
            
            status.text("Parsing Excel structure...")
            progress.progress(50)
            
            parsed_data = parser.parse()
            
            status.text("Validating data...")
            progress.progress(80)
            
            # Store in session state
            st.session_state.parsed_data = parsed_data
            st.session_state.parse_complete = True
            st.session_state.save_complete = False
            
            progress.progress(100)
            status.empty()
            progress.empty()
            
            st.success("Parse complete! Ready to save to database.")
            
            # Show results
            self.display_parse_results(parsed_data)
            
        except Exception as e:
            st.error(f"Parse failed: {str(e)}")
            with st.expander("Error details"):
                st.code(traceback.format_exc())
        
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def display_parse_results(self, parsed_data):
        """Display parsing results"""
        st.markdown("### Parse Results")
        
        hierarchy = parsed_data['hierarchy']
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Data Points", len(hierarchy['data_points']))
        with col2:
            st.metric("Assessment Criteria", len(hierarchy['assessment_criteria']))
        with col3:
            st.metric("Performance Signals", len(hierarchy['performance_signals']))
        with col4:
            st.metric("Key Topics", len(hierarchy['key_topics']))
        
        # Data preview
        with st.expander("Preview Parsed Data"):
            st.write("**Sample Data Points:**")
            sample = list(hierarchy['data_points'].values())[:5]
            for i, dp in enumerate(sample, 1):
                if hasattr(dp, 'name'):
                    st.text(f"{i}. {dp.name} [{dp.data_type}] - {dp.pillar}")
                else:
                    st.text(f"{i}. {dp['name']} [{dp['data_type']}] - {dp['pillar']}")
    
    def render_save_section(self):
        """Render save section"""
        st.warning("Unsaved parsed data detected")
        
        parsed_data = st.session_state.parsed_data
        hierarchy = parsed_data['hierarchy']
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Data Points", len(hierarchy['data_points']))
        with col2:
            st.metric("Assessment Criteria", len(hierarchy['assessment_criteria']))
        with col3:
            st.metric("Performance Signals", len(hierarchy['performance_signals']))
        with col4:
            st.metric("Key Topics", len(hierarchy['key_topics']))
        
        st.divider()
        
        # Actions
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            if st.button("Save to Database", type="primary", use_container_width=True):
                self.save_to_database()
        
        with col2:
            if st.button("Discard", type="secondary", use_container_width=True):
                st.session_state.parsed_data = None
                st.session_state.parse_complete = False
                st.rerun()
    
    def save_to_database(self):
        """Save parsed data to database"""
        try:
            with st.spinner("Saving to database..."):
                success = self.db.save_parsed_data(st.session_state.parsed_data)
            
            if success:
                st.session_state.save_complete = True
                st.success("Data saved successfully! You can now configure formulas, weights, and thresholds.")
                
                # Show button to go to configuration
                if st.button("Go to Master File Configuration", type="primary"):
                    st.session_state.current_page = 'master_config'
                    st.session_state.parsed_data = None
                    st.session_state.parse_complete = False
                    st.rerun()
                
                # Clear parsed data after a delay
                import time
                time.sleep(2)
                st.session_state.parsed_data = None
                st.session_state.parse_complete = False
                
        except Exception as e:
            st.error(f"Save error: {str(e)}")
            with st.expander("Error details"):
                st.code(traceback.format_exc())
    
    def render_database_page(self):
        """Render database view"""
        st.header("Database Contents")
        
        tabs = st.tabs(["Data Points", "Assessment Criteria", "Performance Signals", "Key Topics"])
        
        with tabs[0]:
            self.render_data_points_tab()
        with tabs[1]:
            self.render_assessment_criteria_tab()
        with tabs[2]:
            self.render_performance_signals_tab()
        with tabs[3]:
            self.render_key_topics_tab()
    
    def render_data_points_tab(self):
        """Render data points tab"""
        dps = self.db.get_all_data_points()
        
        if dps:
            col1, col2 = st.columns([2, 1])
            with col1:
                search = st.text_input("Search data points", "")
            with col2:
                pillar_filter = st.selectbox(
                    "Filter by pillar",
                    ["All"] + list(set(dp.get('pillar', '') for dp in dps))
                )
            
            # Filter
            filtered = dps
            if search:
                filtered = [dp for dp in filtered if search.lower() in dp.get('name', '').lower()]
            if pillar_filter != "All":
                filtered = [dp for dp in filtered if dp.get('pillar', '') == pillar_filter]
            
            st.info(f"Showing {len(filtered)} of {len(dps)} data points")
            
            if filtered:
                df = pd.DataFrame(filtered)
                st.dataframe(df, use_container_width=True, height=600)
        else:
            st.info("No data points in database")
    
    def render_assessment_criteria_tab(self):
        """Render assessment criteria tab"""
        acs = self.db.get_all_assessment_criteria()
        
        if acs:
            st.info(f"Total: {len(acs)} assessment criteria")
            
            search = st.text_input("Search criteria", "")
            filtered = acs
            if search:
                filtered = [ac for ac in acs if search.lower() in ac.get('name', '').lower()]
            
            # Display limited for performance
            for ac in filtered[:50]:
                with st.expander(ac.get('name', 'Unknown')[:100]):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Code:** {ac.get('code', 'N/A')}")
                        st.write(f"**Type:** {ac.get('formula_type', 'N/A')}")
                        st.write(f"**Weight:** {ac.get('weight', 0)}%")
                    with col2:
                        st.write(f"**Signal:** {ac.get('performance_signal_name', 'N/A')}")
                        st.write(f"**Data Points:** {len(ac.get('data_points', []))}")
                    
                    if ac.get('formula'):
                        st.code(ac['formula'])
            
            if len(filtered) > 50:
                st.warning(f"Showing first 50 of {len(filtered)} results")
        else:
            st.info("No assessment criteria in database")
    
    def render_performance_signals_tab(self):
        """Render performance signals tab"""
        db_data = self.db.load_database()
        pss = db_data.get('performance_signals', {})
        
        if pss:
            df = pd.DataFrame.from_dict(pss, orient='index')
            st.info(f"Total: {len(pss)} performance signals")
            st.dataframe(df, use_container_width=True, height=600)
        else:
            st.info("No performance signals in database")
    
    def render_key_topics_tab(self):
        """Render key topics tab"""
        db_data = self.db.load_database()
        kts = db_data.get('key_topics', {})
        
        if kts:
            df = pd.DataFrame.from_dict(kts, orient='index')
            st.info(f"Total: {len(kts)} key topics")
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("No key topics in database")
    
    def render_analytics_page(self):
        """Render analytics page"""
        st.header("Analytics")
        
        db_data = self.db.load_database()
        
        if not db_data.get('data_points'):
            st.info("No data available for analytics")
            return
        
        # Distribution analysis
        st.subheader("Distribution by Pillar")
        pillar_stats = {}
        for dp in db_data.get('data_points', {}).values():
            pillar = dp.get('pillar', 'Unknown')
            if pillar not in pillar_stats:
                pillar_stats[pillar] = {'Data Points': 0, 'Criteria': 0}
            pillar_stats[pillar]['Data Points'] += 1
        
        for ac in db_data.get('assessment_criteria', {}).values():
            # Determine pillar from related data points
            if ac.get('data_points'):
                for dp_name in ac['data_points']:
                    if dp_name in db_data.get('data_points', {}):
                        pillar = db_data['data_points'][dp_name].get('pillar', 'Unknown')
                        if pillar in pillar_stats:
                            pillar_stats[pillar]['Criteria'] += 1
                        break
        
        df = pd.DataFrame.from_dict(pillar_stats, orient='index')
        st.bar_chart(df)
        
        # Formula analysis
        st.subheader("Formula Type Distribution")
        formula_types = {}
        for ac in db_data.get('assessment_criteria', {}).values():
            ftype = ac.get('formula_type', 'unknown')
            formula_types[ftype] = formula_types.get(ftype, 0) + 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Quantitative", formula_types.get('quantitative', 0))
        with col2:
            st.metric("Qualitative", formula_types.get('qualitative', 0))
        with col3:
            st.metric("Unknown", formula_types.get('unknown', 0))
    
    def render_export_page(self):
        """Render export page"""
        st.header("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Excel Export")
            st.markdown("Export complete database to Excel spreadsheet format.")
            
            if st.button("Generate Excel Export", type="primary", use_container_width=True):
                self.export_to_excel()
        
        with col2:
            st.subheader("JSON Export")
            st.markdown("Export complete database to JSON format for backup or integration.")
            
            if st.button("Generate JSON Export", type="primary", use_container_width=True):
                self.export_to_json()
    
    def export_to_excel(self):
        """Export database to Excel"""
        try:
            os.makedirs("exports", exist_ok=True)
            filename = f"exports/meinhardt_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            with st.spinner("Generating Excel file..."):
                if self.db.export_to_excel(filename):
                    st.success(f"Export complete")
                    
                    with open(filename, 'rb') as f:
                        st.download_button(
                            "Download Excel File",
                            data=f,
                            file_name=os.path.basename(filename),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("Export failed")
        except Exception as e:
            st.error(f"Export error: {str(e)}")
    
    def export_to_json(self):
        """Export database to JSON"""
        try:
            data = self.db.load_database()
            json_str = json.dumps(data, indent=2, default=str)
            
            st.download_button(
                "Download JSON File",
                data=json_str,
                file_name=f"meinhardt_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        except Exception as e:
            st.error(f"Export error: {str(e)}")

# Run the application
if __name__ == "__main__":
    app = MeinhardtApp()
    app.run()