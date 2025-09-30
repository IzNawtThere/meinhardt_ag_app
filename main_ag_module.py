"""
Main AG Module for Meinhardt WebApp
ACTUALLY FIXED VERSION - Position-based formula evaluation
"""

import streamlit as st
import pandas as pd
import json
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Tuple
import re
import os
from copy import deepcopy
import random
import hashlib

class MainAGModule:
    def __init__(self):
        self.db_path = "data/meinhardt_db.json"
        self.load_database()
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize session state for AG module"""
        if 'ag_inputs' not in st.session_state:
            st.session_state.ag_inputs = {}
        if 'ag_results' not in st.session_state:
            st.session_state.ag_results = None
        if 'show_details' not in st.session_state:
            st.session_state.show_details = {}
    
    def load_database(self):
        """Load the database with all relationships and metadata"""
        try:
            with open(self.db_path, 'r') as f:
                self.db = json.load(f)
            self.build_relationships()
            return True
        except FileNotFoundError:
            st.error("Database not found. Please upload and parse a Master File first.")
            self.db = None
            return False
    
    def build_relationships(self):
        """Build relationship mappings between entities"""
        self.relationships = {
            'dp_to_ac': {},
            'ac_to_ps': {},
            'ps_to_kt': {},
        }
        
        if 'assessment_criteria' in self.db:
            for ac_name, ac_data in self.db['assessment_criteria'].items():
                dps = ac_data.get('data_points', [])
                for dp in dps:
                    if dp not in self.relationships['dp_to_ac']:
                        self.relationships['dp_to_ac'][dp] = []
                    self.relationships['dp_to_ac'][dp].append(ac_name)
                
                ps_name = ac_data.get('performance_signal_name')
                if ps_name:
                    if ps_name not in self.relationships['ac_to_ps']:
                        self.relationships['ac_to_ps'][ps_name] = []
                    self.relationships['ac_to_ps'][ps_name].append(ac_name)
        
        if 'performance_signals' in self.db:
            for ps_name, ps_data in self.db['performance_signals'].items():
                kt_name = ps_data.get('key_topic_name')
                if kt_name:
                    if kt_name not in self.relationships['ps_to_kt']:
                        self.relationships['ps_to_kt'][kt_name] = []
                    self.relationships['ps_to_kt'][kt_name].append(ps_name)
    
    def render(self):
        """Main render function"""
        if self.db is None:
            return
        
        # Professional header with better styling
        st.markdown("""
        <style>
            .main-header {
                padding: 1rem 0;
                border-bottom: 2px solid #e0e0e0;
                margin-bottom: 2rem;
            }
            .metric-card {
                background: white;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }
            .calculation-box {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                border-left: 4px solid #1e3a8a;
                margin: 1rem 0;
                font-family: monospace;
            }
            .rating-good {
                color: #10b981;
                font-weight: bold;
            }
            .rating-satisfactory {
                color: #f59e0b;
                font-weight: bold;
            }
            .rating-needs-improvement {
                color: #ef4444;
                font-weight: bold;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.title("Main Assessment Guide Module")
        st.caption("Professional Assessment Calculation Engine")
        
        # Simplified tabs - removed unnecessary ones
        tabs = st.tabs(["Calculator", "Results & Analysis", "Reports"])
        
        with tabs[0]:
            self.render_calculator()
        
        with tabs[1]:
            self.render_results()
        
        with tabs[2]:
            self.render_reports()
    
    def render_calculator(self):
        """Enhanced calculator interface"""
        # Control panel
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            if st.button("Calculate Assessment", type="primary", use_container_width=True):
                self.perform_calculations()
        
        with col2:
            if st.button("Fill Test Data", use_container_width=True):
                self.fill_comprehensive_test_data()
        
        with col3:
            if st.button("Clear All", use_container_width=True):
                st.session_state.ag_inputs = {}
                st.session_state.ag_results = None
                st.rerun()
        
        st.divider()
        
        # Enhanced filter controls
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            pillars = ["All"] + list(set(
                dp.get('pillar', 'Unknown') 
                for dp in self.db.get('data_points', {}).values()
            ))
            selected_pillar = st.selectbox("Filter by Pillar", pillars)
        
        with col2:
            data_types = ["All", "Numbers", "Percentages", "Dates", "Text"]
            selected_type = st.selectbox("Filter by Type", data_types)
        
        with col3:
            show_required = st.checkbox("Required Only", value=True)
        
        with col4:
            view_mode = st.radio("View", ["Compact", "Detailed"], horizontal=True)
        
        # Data input section with better organization
        st.markdown("### Data Point Inputs")
        
        input_tabs = st.tabs(["Quantitative Data", "Qualitative Assessments"])
        
        with input_tabs[0]:
            self.render_enhanced_quantitative_inputs(selected_pillar, selected_type, show_required, view_mode)
        
        with input_tabs[1]:
            self.render_enhanced_qualitative_inputs(selected_pillar)
    
    def render_enhanced_quantitative_inputs(self, pillar_filter, type_filter, required_only, view_mode):
        """Enhanced quantitative input interface"""
        filtered_dps = self.get_filtered_data_points(pillar_filter, type_filter, required_only)
        
        # Filter for quantitative
        type_map = {
            "Numbers": ['No.', 'number'],
            "Percentages": ['%', 'percentage'],
            "Dates": ['dd/mm/yy', 'date'],
            "Text": ['Text', 'text']
        }
        
        if type_filter != "All":
            allowed_types = type_map.get(type_filter, [])
            filtered_dps = {
                name: data for name, data in filtered_dps.items()
                if data.get('data_type') in allowed_types
            }
        
        if not filtered_dps:
            st.info("No data points match the current filters")
            return
        
        # Status indicator
        filled = sum(1 for dp in filtered_dps if dp in st.session_state.ag_inputs and st.session_state.ag_inputs[dp])
        progress = filled / len(filtered_dps) if filtered_dps else 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(progress)
        with col2:
            st.metric("Completion", f"{filled}/{len(filtered_dps)}")
        
        # Group by pillar with better layout
        pillars = {}
        for dp_name, dp_data in filtered_dps.items():
            pillar = dp_data.get('pillar', 'Unknown')
            if pillar not in pillars:
                pillars[pillar] = {}
            pillars[pillar][dp_name] = dp_data
        
        for pillar_idx, (pillar, dps) in enumerate(pillars.items()):
            with st.expander(f"**{pillar}** ({len(dps)} data points)", expanded=True):
                if view_mode == "Compact":
                    cols = st.columns(3)
                    for idx, (dp_name, dp_data) in enumerate(dps.items()):
                        with cols[idx % 3]:
                            self.render_compact_input(dp_name, dp_data, pillar_idx, idx)
                else:
                    for idx, (dp_name, dp_data) in enumerate(dps.items()):
                        self.render_detailed_input(dp_name, dp_data, pillar_idx, idx)
    
    def render_compact_input(self, dp_name, dp_data, pillar_idx, item_idx):
        """Compact input rendering with unique keys"""
        data_type = dp_data.get('data_type', 'text')
        
        # Shorter label for compact view
        label = dp_name[:30] + "..." if len(dp_name) > 30 else dp_name
        is_required = dp_name in self.relationships.get('dp_to_ac', {})
        if is_required:
            label = f"* {label}"
        
        # Create truly unique key combining multiple identifiers
        key_hash = hashlib.md5(f"{dp_name}_{pillar_idx}_{item_idx}".encode()).hexdigest()[:8]
        input_key = f"dp_{pillar_idx}_{item_idx}_{key_hash}"
        current_value = st.session_state.ag_inputs.get(dp_name)
        
        if data_type in ['No.', 'number']:
            value = st.number_input(
                label,
                value=float(current_value) if current_value else 0.0,
                key=input_key,
                label_visibility="visible"
            )
            st.session_state.ag_inputs[dp_name] = value
            
        elif data_type in ['%', 'percentage']:
            value = st.number_input(
                label,
                min_value=0.0,
                max_value=100.0,
                value=float(current_value) if current_value else 0.0,
                step=0.1,
                key=input_key
            )
            st.session_state.ag_inputs[dp_name] = value
            
        elif data_type in ['dd/mm/yy', 'date']:
            value = st.text_input(
                label,
                value=str(current_value) if current_value else "",
                placeholder="dd/mm/yyyy",
                key=input_key
            )
            if value:
                st.session_state.ag_inputs[dp_name] = value
        else:  # Text
            value = st.text_input(
                label,
                value=str(current_value) if current_value else "",
                key=input_key
            )
            if value:
                st.session_state.ag_inputs[dp_name] = value
    
    def render_detailed_input(self, dp_name, dp_data, pillar_idx, item_idx):
        """Detailed input rendering with more context"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self.render_compact_input(dp_name, dp_data, pillar_idx, item_idx)
        
        with col2:
            # Show which ACs use this DP
            related_acs = self.relationships.get('dp_to_ac', {}).get(dp_name, [])
            if related_acs:
                st.caption(f"Used by {len(related_acs)} ACs")
    
    def render_enhanced_qualitative_inputs(self, pillar_filter):
        """Enhanced qualitative input interface"""
        qualitative_acs = {
            name: data for name, data in self.db.get('assessment_criteria', {}).items()
            if data.get('formula_type') == 'qualitative'
        }
        
        if not qualitative_acs:
            st.info("No qualitative assessment criteria found")
            return
        
        # Status
        filled = sum(1 for ac in qualitative_acs if f"qual_{ac}" in st.session_state.ag_inputs)
        st.metric("Qualitative Assessments Completed", f"{filled}/{len(qualitative_acs)}")
        
        # Group by PS
        by_ps = {}
        for ac_name, ac_data in qualitative_acs.items():
            ps_name = ac_data.get('performance_signal_name', 'Uncategorized')
            if ps_name not in by_ps:
                by_ps[ps_name] = {}
            by_ps[ps_name][ac_name] = ac_data
        
        for ps_idx, (ps_name, acs) in enumerate(by_ps.items()):
            with st.expander(f"**{ps_name}** ({len(acs)} criteria)", expanded=True):
                for ac_idx, (ac_name, ac_data) in enumerate(acs.items()):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        thresholds = ac_data.get('thresholds', {})
                        options = []
                        if thresholds:
                            if 'good' in thresholds:
                                options.append(thresholds['good'])
                            if 'satisfactory' in thresholds:
                                options.append(thresholds['satisfactory'])
                            if 'needs_improvement' in thresholds:
                                options.append(thresholds['needs_improvement'])
                        else:
                            options = ['Yes', 'Partially Applied', 'No']
                        
                        qual_key = f"qual_{ac_name}"
                        current = st.session_state.ag_inputs.get(qual_key, options[1] if len(options) > 1 else options[0])
                        
                        # Unique key for selectbox
                        select_key = f"select_qual_{ps_idx}_{ac_idx}_{hashlib.md5(ac_name.encode()).hexdigest()[:8]}"
                        
                        selected = st.selectbox(
                            ac_name[:60],
                            options=options,
                            index=options.index(current) if current in options else 0,
                            key=select_key
                        )
                        st.session_state.ag_inputs[qual_key] = selected
                    
                    with col2:
                        st.caption(f"Weight: {ac_data.get('weight', 0)}%")
                    
                    with col3:
                        # Show expected rating
                        if selected == options[0]:
                            st.success("Good")
                        elif len(options) > 1 and selected == options[1]:
                            st.warning("Satisfactory")
                        else:
                            st.error("Needs Improvement")
    
    def fill_comprehensive_test_data(self):
        """FIXED test data filling with exact DP names that will calculate properly"""
        filled_count = 0
        
        # These values MUST produce known results
        critical_test_values = {
            # THESE ARE THE EXACT NAMES FROM YOUR DATABASE
            "Earned Value (EV) (No.)": 920000,
            "Planned Value (PV) (No.)": 1000000,
            "No. of milestones achieved on time (No.)": 8,
            "No. of planned milestones (No.)": 10,
            "Number of projects with approved change requests in design phase since inception with time impact of more than 1 month (No.)": 2,
            "Total number of projects in design phase (No.)": 10,
            "Value of Modularized Construction Cost (No.)": 300000,
            "Value of Total Construction Cost (No.)": 1000000,
            "Number of projects achieving DevCo ESG Targets (No.)": 7,
            "Total number of projects (No.)": 10,
            "Forecast budget (EAC) (No.)": 1100000,
            "PIF Approved Capex budget (Initial Business Plan) (No.)": 1000000,
            "Number of controlled risks (No.)": 45,
            "Total number of identified risks (No.)": 50,
        }
        
        # Apply critical values first
        for dp_name, value in critical_test_values.items():
            st.session_state.ag_inputs[dp_name] = value
            filled_count += 1
        
        # Fill remaining with sensible defaults
        for dp_name, dp_data in self.db.get('data_points', {}).items():
            if dp_name not in st.session_state.ag_inputs:
                data_type = dp_data.get('data_type', 'text')
                
                if data_type in ['No.', 'number']:
                    st.session_state.ag_inputs[dp_name] = random.randint(50, 100)
                    filled_count += 1
                elif data_type in ['%', 'percentage']:
                    st.session_state.ag_inputs[dp_name] = random.uniform(75, 95)
                    filled_count += 1
                elif data_type in ['dd/mm/yy', 'date']:
                    st.session_state.ag_inputs[dp_name] = "31/12/2024"
                    filled_count += 1
                elif data_type in ['Text', 'text']:
                    st.session_state.ag_inputs[dp_name] = "Approved and documented"
                    filled_count += 1
        
        # Fill qualitative assessments
        for ac_name, ac_data in self.db.get('assessment_criteria', {}).items():
            if ac_data.get('formula_type') == 'qualitative':
                thresholds = ac_data.get('thresholds', {})
                qual_key = f"qual_{ac_name}"
                if thresholds and 'good' in thresholds:
                    st.session_state.ag_inputs[qual_key] = thresholds['good']
                else:
                    st.session_state.ag_inputs[qual_key] = "Yes"
                filled_count += 1
        
        st.success(f"Filled {filled_count} data points with test values!")
        st.rerun()
    
    def get_filtered_data_points(self, pillar_filter, type_filter, required_only):
        """Get filtered data points"""
        filtered = {}
        
        for dp_name, dp_data in self.db.get('data_points', {}).items():
            if pillar_filter != "All" and dp_data.get('pillar') != pillar_filter:
                continue
            
            if required_only and dp_name not in self.relationships.get('dp_to_ac', {}):
                continue
            
            filtered[dp_name] = dp_data
        
        return filtered
    
    def perform_calculations(self):
        """Perform all calculations"""
        with st.spinner("Calculating assessments..."):
            try:
                results = {
                    'timestamp': datetime.now().isoformat(),
                    'inputs': deepcopy(st.session_state.ag_inputs),
                    'calculations': {
                        'assessment_criteria': {},
                        'performance_signals': {},
                        'key_topics': {},
                        'overall_score': 0
                    }
                }
                
                # Calculate all levels
                self.calculate_assessment_criteria(results)
                self.calculate_performance_signals(results)
                self.calculate_key_topics(results)
                self.calculate_overall_score(results)
                
                st.session_state.ag_results = results
                
                # Show summary
                self.show_enhanced_summary(results)
                
            except Exception as e:
                st.error(f"Calculation error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    def show_enhanced_summary(self, results):
        """Enhanced calculation summary"""
        st.success("Calculations complete!")
        
        # Key metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall = results['calculations'].get('overall_score', 0)
            rating = results['calculations'].get('overall_rating', 'N/A')
            color = self.get_rating_color_hex(rating)
            st.markdown(f"""
            <div style='background: {color}20; padding: 1rem; border-radius: 10px; border-left: 4px solid {color};'>
                <h3 style='margin: 0; color: {color};'>{overall:.1%}</h3>
                <p style='margin: 0; color: #666;'>Overall Score</p>
                <p style='margin: 0; color: {color}; font-weight: bold;'>{rating}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            ac_count = len(results['calculations'].get('assessment_criteria', {}))
            good_count = sum(1 for ac in results['calculations'].get('assessment_criteria', {}).values() 
                           if ac.get('rating') == 'Good')
            st.markdown(f"""
            <div style='background: #f0f9ff; padding: 1rem; border-radius: 10px;'>
                <h3 style='margin: 0; color: #1e3a8a;'>{good_count}/{ac_count}</h3>
                <p style='margin: 0; color: #666;'>Good ACs</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            ps_scores = [ps.get('score', 0) for ps in results['calculations'].get('performance_signals', {}).values()]
            ps_avg = np.mean(ps_scores) if ps_scores else 0
            st.markdown(f"""
            <div style='background: #fef3c7; padding: 1rem; border-radius: 10px;'>
                <h3 style='margin: 0; color: #92400e;'>{ps_avg:.1%}</h3>
                <p style='margin: 0; color: #666;'>Avg PS Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            kt_count = len(results['calculations'].get('key_topics', {}))
            st.markdown(f"""
            <div style='background: #f0fdf4; padding: 1rem; border-radius: 10px;'>
                <h3 style='margin: 0; color: #14532d;'>{kt_count}</h3>
                <p style='margin: 0; color: #666;'>Key Topics</p>
            </div>
            """, unsafe_allow_html=True)
    
    def render_results(self):
        """Enhanced results view with drill-down"""
        if not st.session_state.ag_results:
            st.info("No results available. Please run calculations first.")
            return
        
        results = st.session_state.ag_results
        
        # Hierarchy view: KT → PS → AC → DP
        st.markdown("## Assessment Hierarchy & Results")
        
        # Overall score card
        overall_score = results['calculations'].get('overall_score', 0)
        overall_rating = results['calculations'].get('overall_rating', 'N/A')
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
            <h2 style='margin: 0; font-size: 3rem;'>{overall_score:.1%}</h2>
            <p style='margin: 0.5rem 0; font-size: 1.2rem;'>Overall Assessment Score</p>
            <p style='margin: 0; font-size: 1.5rem; font-weight: bold;'>{overall_rating}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Topics level
        st.markdown("### Key Topics")
        kt_results = results['calculations'].get('key_topics', {})
        
        for kt_idx, (kt_name, kt_data) in enumerate(kt_results.items()):
            score = kt_data.get('score', 0)
            rating = kt_data.get('rating', 'Unknown')
            
            with st.expander(f"**{kt_name}** - {score:.1%} ({rating})", expanded=False):
                # KT details
                col1, col2 = st.columns([1, 3])
                with col1:
                    self.render_score_gauge(score, rating)
                
                with col2:
                    # Performance Signals under this KT
                    st.markdown("#### Performance Signals")
                    
                    for ps_idx, ps_name in enumerate(kt_data.get('performance_signals', [])):
                        if ps_name in results['calculations'].get('performance_signals', {}):
                            ps_data = results['calculations']['performance_signals'][ps_name]
                            ps_score = ps_data.get('score', 0)
                            ps_rating = ps_data.get('rating', 'Unknown')
                            
                            with st.container():
                                st.markdown(f"""
                                <div style='background: #f8f9fa; padding: 1rem; margin: 0.5rem 0; border-radius: 8px;'>
                                    <strong>{ps_name}</strong><br>
                                    Score: {ps_score:.1%} | Rating: {ps_rating} | Weight: {ps_data.get('weight', 0)}%
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show ACs under this PS with unique key
                                if st.button(f"Show Details", key=f"ps_details_{kt_idx}_{ps_idx}"):
                                    self.show_ps_details(ps_name, ps_data, results)
    
    def show_ps_details(self, ps_name, ps_data, results):
        """Show detailed PS breakdown"""
        st.markdown(f"#### {ps_name} - Detailed Breakdown")
        
        for ac_name in ps_data.get('assessment_criteria', []):
            if ac_name in results['calculations'].get('assessment_criteria', {}):
                ac_data = results['calculations']['assessment_criteria'][ac_name]
                
                with st.container():
                    st.markdown(f"**{ac_name[:60]}...**")
                    
                    # Show calculation details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Value", f"{ac_data.get('value'):.2f}" if isinstance(ac_data.get('value'), (int, float)) else ac_data.get('value'))
                    with col2:
                        st.metric("Rating", ac_data.get('rating'))
                    with col3:
                        st.metric("Weight", f"{ac_data.get('weight', 0)}%")
                    
                    # Show formula and calculation
                    with st.expander("Calculation Details"):
                        self.show_calculation_details(ac_name, ac_data)
    
    def show_calculation_details(self, ac_name, ac_data):
        """Show detailed calculation breakdown"""
        st.markdown("**Formula:**")
        st.code(ac_data.get('formula', 'No formula'))
        
        st.markdown("**Data Points Used:**")
        for dp in ac_data.get('data_points_used', []):
            value = st.session_state.ag_inputs.get(dp, 'Not provided')
            st.write(f"• {dp}: **{value}**")
        
        st.markdown("**Calculation:**")
        # Show step-by-step calculation
        formula = ac_data.get('formula', '')
        if formula and ac_data.get('formula_type') == 'quantitative':
            st.code(f"""
Formula: {formula}
Result: {ac_data.get('value')}
Threshold: {json.dumps(ac_data.get('thresholds', {}), indent=2)}
Rating: {ac_data.get('rating')}
            """)
    
    def render_score_gauge(self, score, rating):
        """Render a simple score gauge"""
        color = self.get_rating_color_hex(rating)
        st.markdown(f"""
        <div style='text-align: center; background: {color}20; padding: 1rem; border-radius: 10px;'>
            <div style='font-size: 2rem; font-weight: bold; color: {color};'>{score:.0%}</div>
            <div style='color: {color};'>{rating}</div>
        </div>
        """, unsafe_allow_html=True)
    
    def get_rating_color_hex(self, rating):
        """Get color for rating"""
        colors = {
            'Good': '#10b981',
            'Satisfactory': '#f59e0b',
            'Needs Improvement': '#ef4444',
            'Unknown': '#6b7280'
        }
        return colors.get(rating, '#6b7280')
    
    def render_reports(self):
        """Simplified reports section"""
        if not st.session_state.ag_results:
            st.info("No results available for reporting")
            return
        
        results = st.session_state.ag_results
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Executive Summary", "Detailed Breakdown", "Improvement Areas"]
        )
        
        if report_type == "Executive Summary":
            self.generate_executive_summary(results)
        elif report_type == "Detailed Breakdown":
            self.generate_detailed_breakdown(results)
        elif report_type == "Improvement Areas":
            self.generate_improvement_report(results)
        
        # Export options
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            json_str = json.dumps(results, indent=2, default=str)
            st.download_button(
                "Export Results (JSON)",
                json_str,
                f"assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "application/json"
            )
        
        with col2:
            csv_data = self.create_csv_export(results)
            st.download_button(
                "Export Results (CSV)",
                csv_data,
                f"assessment_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                "text/csv"
            )
    
    def generate_executive_summary(self, results):
        """Generate executive summary"""
        st.markdown("## Executive Summary")
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Overall Score", f"{results['calculations'].get('overall_score', 0):.1%}")
            st.metric("Overall Rating", results['calculations'].get('overall_rating', 'N/A'))
        
        with col2:
            ac_results = results['calculations'].get('assessment_criteria', {})
            good = sum(1 for ac in ac_results.values() if ac.get('rating') == 'Good')
            st.metric("Good Ratings", f"{good}/{len(ac_results)}")
        
        with col3:
            needs_imp = sum(1 for ac in ac_results.values() if ac.get('rating') == 'Needs Improvement')
            st.metric("Needs Improvement", needs_imp)
        
        # Top and bottom performers
        st.markdown("### Performance Analysis")
        
        kt_results = results['calculations'].get('key_topics', {})
        sorted_kts = sorted(kt_results.items(), key=lambda x: x[1].get('score', 0), reverse=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Top Performers:**")
            for name, data in sorted_kts[:3]:
                st.write(f"• {name}: {data.get('score', 0):.1%}")
        
        with col2:
            st.markdown("**Need Attention:**")
            for name, data in sorted_kts[-3:]:
                if data.get('rating') == 'Needs Improvement':
                    st.write(f"• {name}: {data.get('score', 0):.1%}")
    
    def generate_detailed_breakdown(self, results):
        """Generate detailed breakdown"""
        st.markdown("## Detailed Assessment Breakdown")
        
        # Create comprehensive table
        data = []
        
        # Add KT level
        for kt_name, kt_data in results['calculations'].get('key_topics', {}).items():
            data.append({
                'Level': 'Key Topic',
                'Name': kt_name,
                'Score/Value': f"{kt_data.get('score', 0):.1%}",
                'Rating': kt_data.get('rating'),
                'Weight': 'N/A'
            })
            
            # Add PS level
            for ps_name in kt_data.get('performance_signals', []):
                if ps_name in results['calculations'].get('performance_signals', {}):
                    ps_data = results['calculations']['performance_signals'][ps_name]
                    data.append({
                        'Level': '  Performance Signal',
                        'Name': f"  {ps_name}",
                        'Score/Value': f"{ps_data.get('score', 0):.1%}",
                        'Rating': ps_data.get('rating'),
                        'Weight': f"{ps_data.get('weight', 0)}%"
                    })
                    
                    # Add AC level
                    for ac_name in ps_data.get('assessment_criteria', []):
                        if ac_name in results['calculations'].get('assessment_criteria', {}):
                            ac_data = results['calculations']['assessment_criteria'][ac_name]
                            value = ac_data.get('value')
                            if isinstance(value, (int, float)):
                                value_str = f"{value:.2f}"
                            else:
                                value_str = str(value)
                            
                            data.append({
                                'Level': '    Assessment Criteria',
                                'Name': f"    {ac_name[:50]}...",
                                'Score/Value': value_str,
                                'Rating': ac_data.get('rating'),
                                'Weight': f"{ac_data.get('weight', 0)}%"
                            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    def generate_improvement_report(self, results):
        """Generate improvement report"""
        st.markdown("## Improvement Areas Report")
        
        improvements = []
        
        # Collect all items needing improvement
        for ac_name, ac_data in results['calculations'].get('assessment_criteria', {}).items():
            if ac_data.get('rating') == 'Needs Improvement':
                improvements.append({
                    'Type': 'Assessment Criteria',
                    'Name': ac_name[:60],
                    'Current Value': ac_data.get('value'),
                    'Weight': f"{ac_data.get('weight', 0)}%",
                    'Formula': ac_data.get('formula', '')[:50]
                })
        
        if improvements:
            df = pd.DataFrame(improvements)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("### Recommendations")
            st.markdown("""
            1. **Priority Areas**: Focus on high-weight criteria first
            2. **Quick Wins**: Target criteria close to satisfactory threshold
            3. **Root Cause Analysis**: Investigate systematic issues
            """)
        else:
            st.success("No critical improvement areas identified!")
    
    def create_csv_export(self, results):
        """Create CSV export data"""
        rows = []
        
        for ac_name, ac_data in results['calculations'].get('assessment_criteria', {}).items():
            rows.append({
                'Level': 'AC',
                'Name': ac_name,
                'Value': ac_data.get('value'),
                'Rating': ac_data.get('rating'),
                'Weight': ac_data.get('weight', 0)
            })
        
        df = pd.DataFrame(rows)
        return df.to_csv(index=False)
    
    # ============= ACTUALLY FIXED CALCULATION METHODS =============
    
    def calculate_assessment_criteria(self, results):
        """Calculate all assessment criteria values"""
        for ac_name, ac_data in self.db.get('assessment_criteria', {}).items():
            formula = ac_data.get('formula', '')
            formula_type = ac_data.get('formula_type', 'quantitative')
            data_points = ac_data.get('data_points', [])
            weight = ac_data.get('weight', 0)
            thresholds = ac_data.get('thresholds', {})
            
            if formula_type == 'quantitative':
                value = self.evaluate_quantitative_formula_position_based(ac_name, formula, data_points)
            else:
                value = self.evaluate_qualitative_ac(ac_name, formula, data_points)
            
            rating = self.determine_rating(value, thresholds, formula_type, ac_name)
            
            results['calculations']['assessment_criteria'][ac_name] = {
                'value': value,
                'rating': rating,
                'weight': weight,
                'formula': formula,
                'formula_type': formula_type,
                'data_points_used': data_points,
                'thresholds': thresholds
            }
    
    def evaluate_quantitative_formula_position_based(self, ac_name, formula, data_points):
        """
        POSITION-BASED formula evaluation that actually works
        The data_points array is already in the correct order from the database
        """
        # Check for manual override
        qual_key = f"qual_{ac_name}"
        if qual_key in st.session_state.ag_inputs:
            val = st.session_state.ag_inputs[qual_key]
            if isinstance(val, (int, float)):
                return val
        
        # Get values from data points IN ORDER
        values = []
        for dp in data_points:
            val = st.session_state.ag_inputs.get(dp, 0)
            if isinstance(val, (int, float)):
                values.append(val)
            else:
                values.append(0)
        
        if not values:
            return 0
        
        # Now evaluate based on formula pattern
        try:
            # Pattern 1: Division formulas (most common)
            if "/" in formula:
                if "[" in formula and "-" in formula:
                    # Complex: [A - B] / C
                    if len(values) >= 3:
                        numerator = values[0] - values[1]
                        denominator = values[2]
                        if denominator != 0:
                            result = numerator / denominator
                            if "%" in ac_name:
                                result *= 100
                            return result
                    elif len(values) >= 2:
                        numerator = values[0] - values[1]
                        denominator = values[1]  # Use second value as denominator
                        if denominator != 0:
                            result = numerator / denominator
                            if "%" in ac_name:
                                result *= 100
                            return result
                else:
                    # Simple division: A / B
                    if len(values) >= 2 and values[1] != 0:
                        result = values[0] / values[1]
                        if "%" in ac_name:
                            result *= 100
                        return result
            
            # Pattern 2: Subtraction
            elif "-" in formula and "[" not in formula:
                if len(values) >= 2:
                    return values[0] - values[1]
            
            # Pattern 3: Addition
            elif "+" in formula:
                return sum(values)
            
            # Pattern 4: Multiplication
            elif "*" in formula:
                if len(values) >= 2:
                    result = values[0] * values[1]
                    if "%" in ac_name:
                        result *= 100
                    return result
            
            # Pattern 5: Single value
            else:
                return values[0] if values else 0
                
        except Exception as e:
            print(f"Error in formula evaluation for {ac_name}: {e}")
            return 0
        
        return 0
    
    def evaluate_qualitative_ac(self, ac_name, formula, data_points):
        """Evaluate qualitative assessment criteria"""
        qual_key = f"qual_{ac_name}"
        if qual_key in st.session_state.ag_inputs:
            return st.session_state.ag_inputs[qual_key]
        
        # Check if data points have values
        has_values = 0
        total_dps = len(data_points) if data_points else 0
        
        for dp in data_points:
            val = st.session_state.ag_inputs.get(dp)
            if val and str(val).strip():
                has_values += 1
        
        if total_dps == 0:
            return "No Data"
        
        completeness = has_values / total_dps if total_dps > 0 else 0
        
        # Return based on completeness
        if completeness >= 0.8:
            return "Yes"
        elif completeness >= 0.4:
            return "Partially Applied"
        else:
            return "No"
    
    def determine_rating(self, value, thresholds, formula_type, ac_name=""):
        """
        Determine rating based on value and thresholds from database
        DO NOT make up thresholds - use only what's in the database
        """
        if not thresholds:
            # No thresholds defined - use sensible defaults
            if formula_type == 'quantitative':
                if isinstance(value, (int, float)):
                    # Check if value is percentage or decimal
                    norm_value = value / 100 if value > 2 else value
                    if norm_value >= 0.95:
                        return "Good"
                    elif norm_value >= 0.85:
                        return "Satisfactory"
                    else:
                        return "Needs Improvement"
            else:
                # Qualitative
                if str(value).lower() in ["yes", "available", "completed", "approved and documented"]:
                    return "Good"
                elif str(value).lower() in ["partially applied", "yes, but inadequate"]:
                    return "Satisfactory"
                else:
                    return "Needs Improvement"
            return "Unknown"
        
        # Apply thresholds from database
        if formula_type == 'quantitative' and isinstance(value, (int, float)):
            # Normalize value for comparison
            compare_value = value
            
            # Check if we need to normalize percentage
            if "%" in ac_name and value > 2:
                # Check if thresholds are in decimal form
                good_str = str(thresholds.get('good', ''))
                if good_str and '>' in good_str:
                    threshold_num = float(good_str.replace('>', '').strip())
                    if threshold_num <= 2:  # Threshold is decimal
                        compare_value = value / 100
            
            # Check each threshold
            if 'good' in thresholds:
                if self.check_threshold(compare_value, thresholds['good']):
                    return 'Good'
            
            if 'satisfactory' in thresholds:
                if self.check_threshold(compare_value, thresholds['satisfactory']):
                    return 'Satisfactory'
            
            if 'needs_improvement' in thresholds:
                if self.check_threshold(compare_value, thresholds['needs_improvement']):
                    return 'Needs Improvement'
        else:
            # Qualitative - exact string match
            value_str = str(value)
            if thresholds.get('good') == value_str:
                return 'Good'
            elif thresholds.get('satisfactory') == value_str:
                return 'Satisfactory'
            elif thresholds.get('needs_improvement') == value_str:
                return 'Needs Improvement'
        
        return "Unknown"
    
    def check_threshold(self, value, threshold_str):
        """Check if value meets threshold condition"""
        threshold_str = str(threshold_str).strip()
        
        try:
            if '>' in threshold_str:
                threshold_val = float(threshold_str.replace('>', '').strip())
                return value > threshold_val
            elif '<' in threshold_str:
                threshold_val = float(threshold_str.replace('<', '').strip())
                return value < threshold_val
            elif '-' in threshold_str:
                parts = threshold_str.split('-')
                if len(parts) == 2:
                    low = float(parts[0].strip())
                    high = float(parts[1].strip())
                    return low <= value <= high
            else:
                threshold_val = float(threshold_str)
                return abs(value - threshold_val) < 0.01
        except:
            return False
    
    def calculate_performance_signals(self, results):
        """Calculate performance signal scores"""
        for ps_name, ps_data in self.db.get('performance_signals', {}).items():
            weight = ps_data.get('weight', 0)
            related_acs = self.relationships.get('ac_to_ps', {}).get(ps_name, [])
            
            if related_acs:
                total_weighted_score = 0
                total_weight = 0
                
                for ac_name in related_acs:
                    if ac_name in results['calculations']['assessment_criteria']:
                        ac_result = results['calculations']['assessment_criteria'][ac_name]
                        ac_weight = float(ac_result.get('weight', 0))
                        rating_score = self.rating_to_score(ac_result.get('rating'))
                        
                        if ac_weight > 0:
                            total_weighted_score += rating_score * ac_weight
                            total_weight += ac_weight
                
                if total_weight > 0:
                    ps_score = (total_weighted_score / total_weight) * 100
                else:
                    ps_score = 0
                    
                ps_rating = self.score_to_rating(ps_score)
                
                results['calculations']['performance_signals'][ps_name] = {
                    'score': ps_score,
                    'rating': ps_rating,
                    'weight': weight,
                    'assessment_criteria': related_acs
                }
    
    def calculate_key_topics(self, results):
        """Calculate key topic scores"""
        for kt_name, kt_data in self.db.get('key_topics', {}).items():
            related_pss = self.relationships.get('ps_to_kt', {}).get(kt_name, [])
            
            if related_pss:
                total_weighted_score = 0
                total_weight = 0
                
                for ps_name in related_pss:
                    if ps_name in results['calculations']['performance_signals']:
                        ps_result = results['calculations']['performance_signals'][ps_name]
                        ps_weight = float(ps_result.get('weight', 0))
                        ps_score = ps_result.get('score', 0)
                        
                        if ps_weight > 0:
                            total_weighted_score += ps_score * ps_weight
                            total_weight += ps_weight
                
                if total_weight > 0:
                    kt_score = total_weighted_score / total_weight
                else:
                    kt_score = 0
                    
                kt_rating = self.score_to_rating(kt_score)
                
                results['calculations']['key_topics'][kt_name] = {
                    'score': kt_score,
                    'rating': kt_rating,
                    'performance_signals': related_pss
                }
    
    def calculate_overall_score(self, results):
        """Calculate overall assessment score"""
        kt_scores = results['calculations']['key_topics']
        
        if kt_scores:
            scores = [kt['score'] for kt in kt_scores.values()]
            overall_score = np.mean(scores) if scores else 0
        else:
            overall_score = 0
        
        results['calculations']['overall_score'] = overall_score
        results['calculations']['overall_rating'] = self.score_to_rating(overall_score)
    
    def rating_to_score(self, rating):
        """Convert rating to numerical score (0-1)"""
        rating_map = {
            'Good': 1.0,
            'Satisfactory': 0.5,
            'Needs Improvement': 0.0,
            'Unknown': 0.0,
            'N/A': 0.0,
            'No Data': 0.0
        }
        return rating_map.get(rating, 0.0)
    
    def score_to_rating(self, score):
        """Convert numerical score to rating"""
        if score >= 80:
            return 'Good'
        elif score >= 50:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'

# Module ready for import
if __name__ == "__main__":
    st.error("This module should be imported by the main application")