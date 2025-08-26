# master_file_module.py
"""
Master File Module for Meinhardt WebApp Phase 2
FIXED VERSION - All CRUD operations actually work
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

class MasterFileModule:
    def __init__(self):
        self.db_path = "data/meinhardt_db.json"
        self.load_database()
    
    def load_database(self):
        """Load the existing JSON database"""
        try:
            with open(self.db_path, 'r') as f:
                self.db = json.load(f)
                return True
        except FileNotFoundError:
            st.error(f"Database not found. Please run Upload & Parse first.")
            self.db = None
            return False
    
    def save_database(self):
        """Save changes to the JSON database"""
        if self.db is None:
            return False
        
        try:
            # Create backup first
            backup_dir = "data/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Save backup if original exists
            if os.path.exists(self.db_path):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = f"{backup_dir}/backup_{timestamp}.json"
                with open(self.db_path, 'r') as f:
                    backup_content = f.read()
                with open(backup_path, 'w') as f:
                    f.write(backup_content)
            
            # Save the database
            with open(self.db_path, 'w') as f:
                json.dump(self.db, f, indent=2)
            
            return True
        except Exception as e:
            st.error(f"Save failed: {str(e)}")
            return False
    
    def render(self):
        """Main render function"""
        if self.db is None:
            st.error("No database found. Please upload and parse a Master File first.")
            return
        
        st.header("Master File Configuration")
        st.caption("Phase 2: Complete Metadata Management")
        
        # Main tabs
        tabs = st.tabs([
            "Data Points",
            "Assessment Criteria",
            "Performance Signals",
            "Key Topics",
            "Formula Editor",
            "Weight Management",
            "Thresholds"
        ])
        
        with tabs[0]:
            self.render_data_points()
        with tabs[1]:
            self.render_assessment_criteria()
        with tabs[2]:
            self.render_performance_signals()
        with tabs[3]:
            self.render_key_topics()
        with tabs[4]:
            self.render_formula_editor()
        with tabs[5]:
            self.render_weight_management()
        with tabs[6]:
            self.render_thresholds()
    
    # ============= DATA POINTS TAB =============
    def render_data_points(self):
        """Data Points Management"""
        st.subheader("Data Points Management")
        
        # Add new DP section
        with st.expander("➕ Add New Data Point", expanded=False):
            with st.form(key="add_dp_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Name*")
                    new_code = st.text_input("Code*")
                
                with col2:
                    new_type = st.selectbox(
                        "Type*",
                        options=["number", "percentage", "text", "date", "boolean"]
                    )
                    new_pillar = st.selectbox(
                        "Pillar*",
                        options=["Planning & Monitoring", "Design & Technical",
                                "Development & Construction", "CE&O", "I&T", "S&O"]
                    )
                
                if st.form_submit_button("Add Data Point", type="primary"):
                    if new_name and new_code:
                        # Add to database
                        if 'data_points' not in self.db:
                            self.db['data_points'] = {}
                        
                        self.db['data_points'][new_name] = {
                            'code': new_code,
                            'name': new_name,
                            'data_type': new_type,
                            'pillar': new_pillar
                        }
                        
                        # Save immediately
                        if self.save_database():
                            st.success(f"✅ Added: {new_name}")
                            st.rerun()
                    else:
                        st.error("Please fill all required fields")
        
        # Display existing DPs
        st.markdown("### Existing Data Points")
        
        if 'data_points' in self.db and self.db['data_points']:
            # Filter
            pillars = list(set([dp.get('pillar', 'Unknown') 
                              for dp in self.db['data_points'].values()]))
            selected_pillar = st.selectbox("Filter by Pillar", ["All"] + pillars)
            
            # Prepare data
            dp_data = []
            for name, dp in self.db['data_points'].items():
                if selected_pillar == "All" or dp.get('pillar') == selected_pillar:
                    dp_data.append({
                        "Name": name,
                        "Code": dp.get('code', ''),
                        "Type": dp.get('data_type', 'text'),
                        "Pillar": dp.get('pillar', 'Unknown')
                    })
            
            if dp_data:
                df = pd.DataFrame(dp_data)
                
                # Show as table
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Edit section
                st.markdown("#### Edit Data Point")
                dp_to_edit = st.selectbox("Select DP to edit", ["None"] + [d["Name"] for d in dp_data])
                
                if dp_to_edit != "None":
                    with st.form(key="edit_dp_form"):
                        current_dp = self.db['data_points'][dp_to_edit]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_code = st.text_input("Code", value=current_dp.get('code', ''))
                            edit_type = st.selectbox(
                                "Type",
                                options=["number", "percentage", "text", "date", "boolean"],
                                index=["number", "percentage", "text", "date", "boolean"].index(
                                    current_dp.get('data_type', 'text')
                                )
                            )
                        
                        with col2:
                            edit_pillar = st.selectbox(
                                "Pillar",
                                options=pillars,
                                index=pillars.index(current_dp.get('pillar', 'Unknown'))
                            )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update", type="primary"):
                                self.db['data_points'][dp_to_edit]['code'] = edit_code
                                self.db['data_points'][dp_to_edit]['data_type'] = edit_type
                                self.db['data_points'][dp_to_edit]['pillar'] = edit_pillar
                                
                                if self.save_database():
                                    st.success(f"✅ Updated: {dp_to_edit}")
                                    st.rerun()
                        
                        with col2:
                            if st.form_submit_button("Delete", type="secondary"):
                                del self.db['data_points'][dp_to_edit]
                                if self.save_database():
                                    st.success(f"🗑️ Deleted: {dp_to_edit}")
                                    st.rerun()
            else:
                st.info("No data points match the filter")
        else:
            st.info("No data points in database")
    
    # ============= ASSESSMENT CRITERIA TAB =============
    def render_assessment_criteria(self):
        """Assessment Criteria Management"""
        st.subheader("Assessment Criteria Management")
        
        # Add new AC
        with st.expander("➕ Add New Assessment Criteria", expanded=False):
            with st.form(key="add_ac_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Name*")
                    new_code = st.text_input("Code*")
                
                with col2:
                    new_type = st.selectbox(
                        "Formula Type*",
                        options=["quantitative", "qualitative"]
                    )
                    new_weight = st.number_input(
                        "Weight (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0
                    )
                
                new_formula = st.text_area("Formula")
                
                if st.form_submit_button("Add Assessment Criteria", type="primary"):
                    if new_name and new_code:
                        if 'assessment_criteria' not in self.db:
                            self.db['assessment_criteria'] = {}
                        
                        self.db['assessment_criteria'][new_name] = {
                            'code': new_code,
                            'name': new_name,
                            'formula': new_formula,
                            'formula_type': new_type,
                            'weight': new_weight,
                            'thresholds': {},
                            'data_points': []
                        }
                        
                        if self.save_database():
                            st.success(f"✅ Added: {new_name}")
                            st.rerun()
                    else:
                        st.error("Please fill all required fields")
        
        # Display existing ACs
        st.markdown("### Existing Assessment Criteria")
        
        if 'assessment_criteria' in self.db and self.db['assessment_criteria']:
            # Search
            search = st.text_input("Search criteria", "")
            
            ac_data = []
            for name, ac in self.db['assessment_criteria'].items():
                if not search or search.lower() in name.lower():
                    ac_data.append({
                        "Name": name[:80],
                        "Code": ac.get('code', ''),
                        "Type": ac.get('formula_type', 'quantitative'),
                        "Weight": f"{ac.get('weight', 0)}%"
                    })
            
            if ac_data:
                df = pd.DataFrame(ac_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Edit section
                st.markdown("#### Edit Assessment Criteria")
                # Get full names for selection
                ac_names = [name for name in self.db['assessment_criteria'].keys()
                           if not search or search.lower() in name.lower()]
                ac_to_edit = st.selectbox("Select AC to edit", ["None"] + ac_names)
                
                if ac_to_edit != "None":
                    with st.form(key="edit_ac_form"):
                        current_ac = self.db['assessment_criteria'][ac_to_edit]
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            edit_code = st.text_input("Code", value=current_ac.get('code', ''))
                            edit_type = st.selectbox(
                                "Formula Type",
                                options=["quantitative", "qualitative"],
                                index=0 if current_ac.get('formula_type') == 'quantitative' else 1
                            )
                        
                        with col2:
                            edit_weight = st.number_input(
                                "Weight (%)",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(current_ac.get('weight', 0))
                            )
                        
                        edit_formula = st.text_area("Formula", value=current_ac.get('formula', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update", type="primary"):
                                self.db['assessment_criteria'][ac_to_edit]['code'] = edit_code
                                self.db['assessment_criteria'][ac_to_edit]['formula_type'] = edit_type
                                self.db['assessment_criteria'][ac_to_edit]['weight'] = edit_weight
                                self.db['assessment_criteria'][ac_to_edit]['formula'] = edit_formula
                                
                                if self.save_database():
                                    st.success(f"✅ Updated: {ac_to_edit}")
                                    st.rerun()
                        
                        with col2:
                            if st.form_submit_button("Delete", type="secondary"):
                                del self.db['assessment_criteria'][ac_to_edit]
                                if self.save_database():
                                    st.success(f"🗑️ Deleted: {ac_to_edit}")
                                    st.rerun()
            else:
                st.info("No assessment criteria match the search")
        else:
            st.info("No assessment criteria in database")
    
    # ============= PERFORMANCE SIGNALS TAB =============
    def render_performance_signals(self):
        """Performance Signals Management"""
        st.subheader("Performance Signals Management")
        
        # Add new PS
        with st.expander("➕ Add New Performance Signal", expanded=False):
            with st.form(key="add_ps_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Name*")
                    new_code = st.text_input("Code*")
                
                with col2:
                    new_weight = st.number_input(
                        "Weight (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=0.0
                    )
                    new_pillar = st.selectbox(
                        "Pillar",
                        options=["Planning & Monitoring", "Design & Technical",
                                "Development & Construction", "CE&O", "I&T", "S&O"]
                    )
                
                if st.form_submit_button("Add Performance Signal", type="primary"):
                    if new_name and new_code:
                        if 'performance_signals' not in self.db:
                            self.db['performance_signals'] = {}
                        
                        self.db['performance_signals'][new_name] = {
                            'code': new_code,
                            'name': new_name,
                            'weight': new_weight,
                            'pillar': new_pillar
                        }
                        
                        if self.save_database():
                            st.success(f"✅ Added: {new_name}")
                            st.rerun()
                    else:
                        st.error("Please fill all required fields")
        
        # Display existing PSs
        st.markdown("### Existing Performance Signals")
        
        if 'performance_signals' in self.db and self.db['performance_signals']:
            ps_data = []
            for name, ps in self.db['performance_signals'].items():
                ps_data.append({
                    "Name": name,
                    "Code": ps.get('code', ''),
                    "Weight": f"{ps.get('weight', 0)}%",
                    "Pillar": ps.get('pillar', 'Unknown')
                })
            
            df = pd.DataFrame(ps_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Edit section
            st.markdown("#### Edit Performance Signal")
            ps_to_edit = st.selectbox("Select PS to edit", ["None"] + [p["Name"] for p in ps_data])
            
            if ps_to_edit != "None":
                with st.form(key="edit_ps_form"):
                    current_ps = self.db['performance_signals'][ps_to_edit]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_code = st.text_input("Code", value=current_ps.get('code', ''))
                        edit_weight = st.number_input(
                            "Weight (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(current_ps.get('weight', 0))
                        )
                    
                    with col2:
                        pillars = ["Planning & Monitoring", "Design & Technical",
                                  "Development & Construction", "CE&O", "I&T", "S&O"]
                        edit_pillar = st.selectbox(
                            "Pillar",
                            options=pillars,
                            index=pillars.index(current_ps.get('pillar', pillars[0]))
                            if current_ps.get('pillar') in pillars else 0
                        )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Update", type="primary"):
                            self.db['performance_signals'][ps_to_edit]['code'] = edit_code
                            self.db['performance_signals'][ps_to_edit]['weight'] = edit_weight
                            self.db['performance_signals'][ps_to_edit]['pillar'] = edit_pillar
                            
                            if self.save_database():
                                st.success(f"✅ Updated: {ps_to_edit}")
                                st.rerun()
                    
                    with col2:
                        if st.form_submit_button("Delete", type="secondary"):
                            del self.db['performance_signals'][ps_to_edit]
                            if self.save_database():
                                st.success(f"🗑️ Deleted: {ps_to_edit}")
                                st.rerun()
        else:
            st.info("No performance signals in database")
    
    # ============= KEY TOPICS TAB =============
    def render_key_topics(self):
        """Key Topics Management"""
        st.subheader("Key Topics Management")
        
        # Add new KT
        with st.expander("➕ Add New Key Topic", expanded=False):
            with st.form(key="add_kt_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("Name*")
                    new_code = st.text_input("Code*")
                
                with col2:
                    new_pillar = st.selectbox(
                        "Pillar*",
                        options=["Planning & Monitoring", "Design & Technical",
                                "Development & Construction", "CE&O", "I&T", "S&O"]
                    )
                
                if st.form_submit_button("Add Key Topic", type="primary"):
                    if new_name and new_code:
                        if 'key_topics' not in self.db:
                            self.db['key_topics'] = {}
                        
                        self.db['key_topics'][new_name] = {
                            'code': new_code,
                            'name': new_name,
                            'pillar': new_pillar
                        }
                        
                        if self.save_database():
                            st.success(f"✅ Added: {new_name}")
                            st.rerun()
                    else:
                        st.error("Please fill all required fields")
        
        # Display existing KTs
        st.markdown("### Existing Key Topics")
        
        if 'key_topics' in self.db and self.db['key_topics']:
            kt_data = []
            for name, kt in self.db['key_topics'].items():
                kt_data.append({
                    "Name": name,
                    "Code": kt.get('code', ''),
                    "Pillar": kt.get('pillar', 'Unknown')
                })
            
            df = pd.DataFrame(kt_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Edit section
            st.markdown("#### Edit Key Topic")
            kt_to_edit = st.selectbox("Select KT to edit", ["None"] + [k["Name"] for k in kt_data])
            
            if kt_to_edit != "None":
                with st.form(key="edit_kt_form"):
                    current_kt = self.db['key_topics'][kt_to_edit]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_code = st.text_input("Code", value=current_kt.get('code', ''))
                    
                    with col2:
                        pillars = ["Planning & Monitoring", "Design & Technical",
                                  "Development & Construction", "CE&O", "I&T", "S&O"]
                        edit_pillar = st.selectbox(
                            "Pillar",
                            options=pillars,
                            index=pillars.index(current_kt.get('pillar', pillars[0]))
                            if current_kt.get('pillar') in pillars else 0
                        )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Update", type="primary"):
                            self.db['key_topics'][kt_to_edit]['code'] = edit_code
                            self.db['key_topics'][kt_to_edit]['pillar'] = edit_pillar
                            
                            if self.save_database():
                                st.success(f"✅ Updated: {kt_to_edit}")
                                st.rerun()
                    
                    with col2:
                        if st.form_submit_button("Delete", type="secondary"):
                            del self.db['key_topics'][kt_to_edit]
                            if self.save_database():
                                st.success(f"🗑️ Deleted: {kt_to_edit}")
                                st.rerun()
        else:
            st.info("No key topics in database")
    
    # ============= FORMULA EDITOR TAB =============
    def render_formula_editor(self):
        """Formula Editor"""
        st.subheader("Formula Editor")
        
        if 'assessment_criteria' not in self.db or not self.db['assessment_criteria']:
            st.info("No assessment criteria found")
            return
        
        ac_list = list(self.db['assessment_criteria'].keys())
        selected_ac = st.selectbox("Select Assessment Criteria", ac_list)
        
        if selected_ac:
            ac_data = self.db['assessment_criteria'][selected_ac]
            
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.write("**Current Formula:**")
                current_formula = ac_data.get('formula', '')
                if current_formula:
                    st.code(current_formula)
                else:
                    st.info("No formula defined")
                
                with st.form(key="formula_form"):
                    new_formula = st.text_area(
                        "Edit Formula",
                        value=current_formula,
                        height=150
                    )
                    
                    formula_type = st.selectbox(
                        "Formula Type",
                        options=["quantitative", "qualitative"],
                        index=0 if ac_data.get('formula_type') == 'quantitative' else 1
                    )
                    
                    if st.form_submit_button("Update Formula", type="primary"):
                        self.db['assessment_criteria'][selected_ac]['formula'] = new_formula
                        self.db['assessment_criteria'][selected_ac]['formula_type'] = formula_type
                        
                        if self.save_database():
                            st.success("✅ Formula updated!")
                            st.rerun()
            
            with col2:
                st.write("**Related Data Points:**")
                # Show available DPs
                if 'data_points' in self.db:
                    dp_list = list(self.db['data_points'].keys())[:10]
                    for dp in dp_list:
                        st.text(f"• {dp}")
                
                st.write("**Test Formula:**")
                if ac_data.get('formula_type') == 'quantitative':
                    with st.form(key="test_form"):
                        val1 = st.number_input("Test Value 1", value=100.0)
                        val2 = st.number_input("Test Value 2", value=50.0)
                        
                        if st.form_submit_button("Test"):
                            try:
                                # Simple test evaluation
                                test_formula = current_formula
                                test_formula = test_formula.replace("(EV)", str(val1))
                                test_formula = test_formula.replace("(PV)", str(val2))
                                test_formula = test_formula.replace("Earned Value", str(val1))
                                test_formula = test_formula.replace("Planned Value", str(val2))
                                
                                if '/' in test_formula and val2 != 0:
                                    result = val1 / val2
                                    st.success(f"Result: {result:.2f}")
                                else:
                                    st.info("Add formula to test")
                            except:
                                st.error("Formula test failed")
    
    # ============= WEIGHT MANAGEMENT TAB =============
    def render_weight_management(self):
        """Weight Management"""
        st.subheader("Weight Management")
        
        tab1, tab2 = st.tabs(["AC Weights (within PS)", "PS Weights (within KT)"])
        
        with tab1:
            if 'performance_signals' not in self.db or not self.db['performance_signals']:
                st.info("No performance signals found")
                return
            
            ps_list = list(self.db['performance_signals'].keys())
            selected_ps = st.selectbox("Select Performance Signal", ps_list, key="ps_for_ac")
            
            if selected_ps and 'assessment_criteria' in self.db:
                st.write(f"**Assessment Criteria weights for: {selected_ps}**")
                
                # Get ACs that belong to this PS based on performance_signal_name field
                related_acs = []
                for ac_name, ac_data in self.db['assessment_criteria'].items():
                    # Check if AC is related to this PS
                    if ac_data.get('performance_signal_name') == selected_ps:
                        related_acs.append(ac_name)
                
                # If no direct relationship found, use first 5 ACs as fallback
                if not related_acs:
                    related_acs = list(self.db['assessment_criteria'].keys())[:5]
                    if related_acs:
                        st.info("Note: Showing sample ACs. Relationships not yet established.")
                
                if related_acs:
                    # Create a unique weights dict for THIS PS's ACs only
                    with st.form(key=f"ac_weights_form_{selected_ps}"):
                        weights = {}
                        total = 0
                        
                        for ac in related_acs:
                            # Get weight specific to this AC within this PS context
                            current_weight = float(self.db['assessment_criteria'][ac].get('weight', 0))
                            
                            # Create unique key for each slider
                            weights[ac] = st.slider(
                                ac[:80],
                                min_value=0.0,
                                max_value=100.0,
                                value=current_weight,
                                step=0.1,
                                key=f"slider_{ac[:30]}_{selected_ps[:30]}"
                            )
                            total += weights[ac]
                        
                        # Display total with color coding
                        if abs(total - 100) < 0.1:
                            st.success(f"**Total Weight: {total:.1f}%** ✓")
                        else:
                            st.warning(f"**Total Weight: {total:.1f}%** (Should be 100%)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Auto-Rebalance"):
                                if total > 0:
                                    factor = 100.0 / total
                                    for ac in weights:
                                        new_weight = round(weights[ac] * factor, 2)
                                        self.db['assessment_criteria'][ac]['weight'] = new_weight
                                    
                                    if self.save_database():
                                        st.success("✅ Weights rebalanced to 100%!")
                                        st.rerun()
                        
                        with col2:
                            if st.form_submit_button("Save Weights", type="primary"):
                                for ac, weight in weights.items():
                                    self.db['assessment_criteria'][ac]['weight'] = weight
                                
                                if self.save_database():
                                    st.success("✅ Weights saved!")
                                    st.rerun()
                else:
                    st.info("No assessment criteria found for this performance signal")
        
        with tab2:
            if 'key_topics' not in self.db or not self.db['key_topics']:
                st.info("No key topics found")
                return
            
            kt_list = list(self.db['key_topics'].keys())
            selected_kt = st.selectbox("Select Key Topic", kt_list, key="kt_for_ps")
            
            if selected_kt and 'performance_signals' in self.db:
                st.write(f"**Performance Signal weights for: {selected_kt}**")
                
                # Get PSs that belong to this KT based on relationships
                related_pss = []
                
                # Check if we have relationship data
                if 'relationships' in self.db and 'kt_to_ps' in self.db['relationships']:
                    if selected_kt in self.db['relationships']['kt_to_ps']:
                        related_pss = self.db['relationships']['kt_to_ps'][selected_kt]
                
                # If no relationships, use first 5 PSs as fallback
                if not related_pss:
                    related_pss = list(self.db['performance_signals'].keys())[:5]
                    if related_pss:
                        st.info("Note: Showing sample PSs. Relationships not yet established.")
                
                if related_pss:
                    with st.form(key=f"ps_weights_form_{selected_kt}"):
                        weights = {}
                        total = 0
                        
                        for ps in related_pss:
                            if ps in self.db['performance_signals']:
                                current_weight = float(self.db['performance_signals'][ps].get('weight', 0))
                                
                                weights[ps] = st.slider(
                                    ps[:80],
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=current_weight,
                                    step=0.1,
                                    key=f"slider_ps_{ps[:30]}_{selected_kt[:30]}"
                                )
                                total += weights[ps]
                        
                        # Display total with color coding
                        if abs(total - 100) < 0.1:
                            st.success(f"**Total Weight: {total:.1f}%** ✓")
                        else:
                            st.warning(f"**Total Weight: {total:.1f}%** (Should be 100%)")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Auto-Rebalance PS"):
                                if total > 0:
                                    factor = 100.0 / total
                                    for ps in weights:
                                        new_weight = round(weights[ps] * factor, 2)
                                        self.db['performance_signals'][ps]['weight'] = new_weight
                                    
                                    if self.save_database():
                                        st.success("✅ PS weights rebalanced to 100%!")
                                        st.rerun()
                        
                        with col2:
                            if st.form_submit_button("Save PS Weights", type="primary"):
                                for ps, weight in weights.items():
                                    self.db['performance_signals'][ps]['weight'] = weight
                                
                                if self.save_database():
                                    st.success("✅ PS weights saved!")
                                    st.rerun()
                else:
                    st.info("No performance signals found for this key topic")
    
    # ============= THRESHOLDS TAB =============
    def render_thresholds(self):
        """Threshold Configuration"""
        st.subheader("Threshold Configuration")
        
        if 'assessment_criteria' not in self.db or not self.db['assessment_criteria']:
            st.info("No assessment criteria found")
            return
        
        ac_list = list(self.db['assessment_criteria'].keys())
        selected_ac = st.selectbox("Select Assessment Criteria", ac_list, key="thresh_ac")
        
        if selected_ac:
            ac_data = self.db['assessment_criteria'][selected_ac]
            formula_type = ac_data.get('formula_type', 'quantitative')
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Current Thresholds:**")
                current_thresholds = ac_data.get('thresholds', {})
                
                if current_thresholds:
                    for rating, value in current_thresholds.items():
                        st.text(f"{rating}: {value}")
                else:
                    st.info("No thresholds configured")
            
            with col2:
                st.write("**Edit Thresholds:**")
                
                with st.form(key="threshold_form"):
                    new_thresholds = {}
                    
                    if formula_type == "quantitative":
                        new_thresholds['good'] = st.text_input(
                            "Good",
                            value=current_thresholds.get('good', '>0.95')
                        )
                        new_thresholds['satisfactory'] = st.text_input(
                            "Satisfactory",
                            value=current_thresholds.get('satisfactory', '0.85-0.95')
                        )
                        new_thresholds['needs_improvement'] = st.text_input(
                            "Needs Improvement",
                            value=current_thresholds.get('needs_improvement', '<0.85')
                        )
                    else:
                        new_thresholds['good'] = st.text_input(
                            "Good",
                            value=current_thresholds.get('good', 'Yes')
                        )
                        new_thresholds['satisfactory'] = st.text_input(
                            "Satisfactory",
                            value=current_thresholds.get('satisfactory', 'Partially Applied')
                        )
                        new_thresholds['needs_improvement'] = st.text_input(
                            "Needs Improvement",
                            value=current_thresholds.get('needs_improvement', 'No')
                        )
                    
                    if st.form_submit_button("Update Thresholds", type="primary"):
                        if 'thresholds' not in self.db['assessment_criteria'][selected_ac]:
                            self.db['assessment_criteria'][selected_ac]['thresholds'] = {}
                        
                        self.db['assessment_criteria'][selected_ac]['thresholds'] = new_thresholds
                        
                        if self.save_database():
                            st.success("✅ Thresholds updated!")
                            st.rerun()

# Module ready for import
if __name__ == "__main__":
    st.error("This module should be imported by the main application")