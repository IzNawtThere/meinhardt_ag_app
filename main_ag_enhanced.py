"""
Main AG Module - COMPLETE FIXED VERSION
Proper value display, no percentage confusion
"""

import re
import streamlit as st
import pandas as pd
import json
import random
import hashlib
import html
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict
import numpy as np

from smart_calculation_engine_updated import SmartCalculationEngine
from improved_test_loader import generate_better_test_values

# Page config
st.set_page_config(
    page_title="Meinhardt Assessment System",
    page_icon="MA",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Advanced Professional CSS
st.markdown("""
<style>
    /* Professional color palette */
    :root {
        --primary: #1a237e;
        --primary-light: #3949ab;
        --primary-dark: #000051;
        --secondary: #00897b;
        --accent: #ff6f00;
        --success: #2e7d32;
        --warning: #f57c00;
        --danger: #c62828;
        --info: #0277bd;
        --light: #f5f5f5;
        --dark: #212121;
        --border: #e0e0e0;
    }
    
    /* Hide Streamlit defaults */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Professional header */
    .system-header {
        background: linear-gradient(90deg, var(--primary) 0%, var(--primary-light) 100%);
        padding: 2rem 3rem;
        margin: -3rem -3rem 2rem -3rem;
        color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .system-header h1 {
        font-size: 2.2rem;
        font-weight: 300;
        margin: 0;
        letter-spacing: 1px;
    }
    
    .system-header p {
        font-size: 1rem;
        margin-top: 0.5rem;
        opacity: 0.9;
    }
    
    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        border-left: 4px solid var(--primary-light);
        transition: transform 0.2s;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 3px 6px rgba(0,0,0,0.16);
    }
    
    /* Professional buttons */
    .stButton > button {
        background: var(--primary-light);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        border-radius: 4px;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: var(--primary);
        box-shadow: 0 2px 8px rgba(26, 35, 126, 0.3);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: white;
        padding: 0.5rem;
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: var(--dark);
        padding: 0.75rem 1.25rem;
        border-radius: 4px;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-light);
        color: white;
    }
    
    /* Calculation display */
    .calc-box {
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid var(--border);
        font-family: 'Roboto Mono', monospace;
    }
    
    /* No truncation */
    .full-text {
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow: visible !important;
    }
</style>
""", unsafe_allow_html=True)

class AdvancedMeinhardt:
    def __init__(self):
        self.engine = SmartCalculationEngine(debug=False)
        self.db_path = 'data/meinhardt_db.json'
        self.load_database()
        self.init_session_state()
        self.categorize_acs()
        self.setup_pillars()
    
    def setup_pillars(self):
        """Define pillar configuration with colors"""
        self.pillar_config = {
            'P&M': {'name': 'Planning & Monitoring', 'color': '#1a237e'},
            'D&T': {'name': 'Design & Technical', 'color': '#00897b'},
            'D&C': {'name': 'Development & Construction', 'color': '#ff6f00'},
            'CE&O': {'name': 'Cost Estimation & Optimization', 'color': '#c62828'},
            'I&T': {'name': 'Innovation & Technology', 'color': '#0277bd'},
            'S&O': {'name': 'Sustainability & Operations', 'color': '#2e7d32'}
        }
    
    def load_database(self):
        """Load database"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.db = json.load(f)
        except Exception as e:
            st.error(f"Database error: {str(e)}")
            self.db = {}
    
    def init_session_state(self):
        """Initialize session state"""
        defaults = {
            'dp_values': {},
            'ac_results': {},
            'ps_results': {},
            'kt_results': {},
            'qualitative_inputs': {},
            'formula_overrides': {},
            'calculation_log': [],
            'ac_categories': {'quantitative': [], 'qualitative': [], 'descriptive': []},
            'formula_issues': [],
            'dp_mapping_hints': {}
        }
        for key, default in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default
    
    def decode_special_chars(self, text):
        """Decode special characters"""
        if not text:
            return text
        text = html.unescape(text)
        replacements = {
            'Â': ' ', 'â': "'", 'â€™': "'", 'â€œ': '"', 'â€': '"',
            'â€"': '-', 'â€"': '—', 'Ã': '', '\xa0': ' '
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text.strip()
    
    def categorize_acs(self):
        """Categorize ACs"""
        for ac_name, ac_data in self.db.get('assessment_criteria', {}).items():
            formula = ac_data.get('formula', '')
            
            if not formula or formula == 'nan':
                st.session_state.ac_categories['descriptive'].append(ac_name)
                continue
            
            formula_lower = formula.lower()
            
            qualitative_keywords = [
                'yes/no', 'applied', 'completed', 'satisfactory if',
                'good if', 'strong if', 'assess if', 'score if',
                'yes if', 'no if'
            ]
            
            if any(keyword in formula_lower for keyword in qualitative_keywords):
                st.session_state.ac_categories['qualitative'].append(ac_name)
            elif any(op in formula for op in ['+', '-', '*', '/', '%', '=']):
                st.session_state.ac_categories['quantitative'].append(ac_name)
            else:
                st.session_state.ac_categories['descriptive'].append(ac_name)
    
    def get_pillar_for_item(self, item_name: str) -> str:
        """Get pillar for any item"""
        item_lower = item_name.lower()
        
        # Check data points for pillar info
        if item_name in self.db.get('data_points', {}):
            dp_data = self.db['data_points'][item_name]
            if dp_data.get('pillar'):
                return dp_data['pillar']
        
        # Check AC's data points
        if item_name in self.db.get('assessment_criteria', {}):
            ac_data = self.db['assessment_criteria'][item_name]
            for dp_name in ac_data.get('data_points', []):
                if dp_name in self.db.get('data_points', {}):
                    dp_data = self.db['data_points'][dp_name]
                    if dp_data.get('pillar'):
                        return dp_data['pillar']
        
        # Pattern matching
        patterns = {
            'P&M': ['planning', 'monitoring', 'schedule', 'cost', 'value', 'devco', 'milestone'],
            'D&T': ['design', 'technical', 'drawing', 'specification'],
            'D&C': ['development', 'construction', 'site', 'safety'],
            'CE&O': ['cost estimation', 'optimization', 'change request', 'cost impact'],
            'I&T': ['innovation', 'technology', 'r&d', 'pilot', 'smart'],
            'S&O': ['sustainability', 'operation', 'environment', 'carbon']
        }
        
        for pillar, keywords in patterns.items():
            if any(kw in item_lower for kw in keywords):
                return pillar
        
        return 'General'
    
    def get_unique_key(self, base: str, suffix: str = "") -> str:
        """Generate unique key"""
        full_key = f"{base}_{suffix}"
        key_hash = hashlib.md5(full_key.encode()).hexdigest()[:8]
        return f"{base}_{key_hash}"
    
    def format_value_for_display(self, value: Any) -> str:
        """Format value for display - KEEP AS DECIMAL"""
        if isinstance(value, str):
            return value
        
        if isinstance(value, (int, float)):
            # Always show as decimal with 2-4 decimal places
            if value == 0:
                return "0.00"
            elif abs(value) < 0.01:
                return f"{value:.4f}"
            elif abs(value) < 1:
                return f"{value:.4f}"
            else:
                return f"{value:.2f}"
        
        return str(value)
    
    def render_header(self):
        """Render header"""
        st.markdown("""
        <div class="system-header">
            <h1>Meinhardt Assessment System</h1>
            <p>Enterprise Project Performance Management Platform</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_metrics(self):
        """Render metrics"""
        metrics = [
            ("Data Points", 
             len([v for v in st.session_state.dp_values.values() if v]),
             len(self.db.get('data_points', {}))),
            ("Assessment Criteria",
             len([r for r in st.session_state.ac_results.values() 
                  if r.get('value') is not None and r.get('value') != 'Data Not Available']),
             len(self.db.get('assessment_criteria', {}))),
            ("Performance Signals",
             len([r for r in st.session_state.ps_results.values() 
                  if isinstance(r.get('value'), (int, float))]),
             len(self.db.get('performance_signals', {}))),
            ("Key Topics",
             len([r for r in st.session_state.kt_results.values() 
                  if isinstance(r.get('value'), (int, float))]),
             len(self.db.get('key_topics', {})))
        ]
        
        cols = st.columns(4)
        for col, (label, current, total) in zip(cols, metrics):
            with col:
                percentage = (current/total*100) if total > 0 else 0
                st.metric(label, f"{current}/{total}",
                         f"{percentage:.0f}%",
                         delta_color="normal" if percentage >= 70 else "inverse")
    
    def render_quantitative_input_by_pillar(self):
        """Quantitative input organized by pillar"""
        st.subheader("Quantitative Data Point Input")
        
        # Get numeric DPs and organize by pillar
        numeric_by_pillar = defaultdict(list)
        for dp_name, dp_data in self.db.get('data_points', {}).items():
            if dp_data.get('data_type') in ['number', 'percentage']:
                pillar = self.get_pillar_for_item(dp_name)
                numeric_by_pillar[pillar].append((dp_name, dp_data))
        
        # Quick actions
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("FILL TEST VALUES", type="primary", use_container_width=True):
                for pillar_dps in numeric_by_pillar.values():
                    for dp_name, dp_data in pillar_dps:
                        if dp_data.get('data_type') == 'percentage':
                            st.session_state.dp_values[dp_name] = random.uniform(60, 95)
                        else:
                            st.session_state.dp_values[dp_name] = random.uniform(1000, 100000)
                st.success("Test values loaded")
                st.rerun()
        
        # Display by pillar tabs
        if numeric_by_pillar:
            pillar_tabs = []
            for pillar in sorted(numeric_by_pillar.keys()):
                config = self.pillar_config.get(pillar, {'name': pillar})
                count = len(numeric_by_pillar[pillar])
                pillar_tabs.append(f"{config['name']} ({count})")
            
            tabs = st.tabs(pillar_tabs)
            
            for idx, (pillar, dps) in enumerate(sorted(numeric_by_pillar.items())):
                with tabs[idx]:
                    cols = st.columns(2)
                    for dp_idx, (dp_name, dp_data) in enumerate(dps):
                        with cols[dp_idx % 2]:
                            current = st.session_state.dp_values.get(dp_name, 0)
                            
                            if dp_data.get('data_type') == 'percentage':
                                value = st.slider(
                                    dp_name,
                                    0.0, 100.0,
                                    float(current),
                                    key=self.get_unique_key("dp", dp_name)
                                )
                            else:
                                value = st.number_input(
                                    dp_name,
                                    value=float(current),
                                    format="%.2f",
                                    key=self.get_unique_key("dp", dp_name)
                                )
                            
                            if value != current:
                                st.session_state.dp_values[dp_name] = value
    
    def render_qualitative_input_by_pillar(self):
        """Qualitative input organized by pillar"""
        st.subheader("Qualitative Assessment Input")
        
        # Organize by pillar
        qual_by_pillar = defaultdict(list)
        for ac_name in st.session_state.ac_categories['qualitative']:
            pillar = self.get_pillar_for_item(ac_name)
            qual_by_pillar[pillar].append(ac_name)
        
        # Quick actions
        if st.button("AUTO-FILL DEFAULTS", type="primary"):
            for ac_name in st.session_state.ac_categories['qualitative']:
                ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
                thresholds = ac_data.get('thresholds', {})
                options = self.get_qualitative_options(thresholds)
                
                # Smart selection
                ac_lower = ac_name.lower()
                if 'risk' in ac_lower:
                    choice = 'No' if 'No' in options else options[-1]
                elif 'compliance' in ac_lower:
                    choice = 'Yes' if 'Yes' in options else options[0]
                else:
                    choice = options[0]
                
                st.session_state.qualitative_inputs[ac_name] = choice
            
            st.success("Defaults applied")
            st.rerun()
        
        # Display by pillar
        if qual_by_pillar:
            pillar_tabs = []
            for pillar in sorted(qual_by_pillar.keys()):
                config = self.pillar_config.get(pillar, {'name': pillar})
                count = len(qual_by_pillar[pillar])
                pillar_tabs.append(f"{config['name']} ({count})")
            
            tabs = st.tabs(pillar_tabs)
            
            for tab_idx, (pillar, acs) in enumerate(sorted(qual_by_pillar.items())):
                with tabs[tab_idx]:
                    for ac_idx, ac_name in enumerate(acs):
                        ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
                        formula = self.decode_special_chars(ac_data.get('formula', ''))
                        thresholds = ac_data.get('thresholds', {})
                        
                        with st.expander(ac_name, expanded=False):
                            st.caption(f"Formula: {formula}")
                            
                            options = self.get_qualitative_options(thresholds)
                            current = st.session_state.qualitative_inputs.get(ac_name, options[0])
                            
                            unique_key = self.get_unique_key(f"qual_{pillar}_{ac_idx}", ac_name)
                            
                            value = st.selectbox(
                                "Assessment",
                                options,
                                index=options.index(current) if current in options else 0,
                                key=unique_key
                            )
                            
                            if value != current:
                                st.session_state.qualitative_inputs[ac_name] = value
    
    def render_executive_dashboard(self):
        """Complete dashboard overhaul - this is the main show"""
        
        if not st.session_state.kt_results:
            st.warning("No results available. Click 'LOAD TEST DATA' then 'CALCULATE ALL' to begin.")
            return
        
        # Custom CSS for professional dashboard
        st.markdown("""
        <style>
        .main-score-card {
            background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
            border-radius: 20px;
            padding: 3rem;
            text-align: center;
            color: white;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 2rem;
        }
        .score-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }
        .kpi-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .dept-section {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .metric-bar {
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        .metric-fill {
            height: 100%;
            transition: width 0.5s ease;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Calculate overall metrics
        kt_values = []
        kt_details = []
        for kt_name, kt_result in st.session_state.kt_results.items():
            if isinstance(kt_result.get('value'), (int, float)) and kt_result.get('value') > 0:
                # Get actual thresholds from database
                kt_data = self.db.get('key_topics', {}).get(kt_name, {})
                thresholds = kt_data.get('thresholds', {})
                rating = self._calculate_rating_from_db(kt_result['value'], thresholds)
                
                kt_values.append(kt_result['value'])
                kt_details.append({
                    'name': kt_name,
                    'value': kt_result['value'],
                    'rating': rating,
                    'pillar': self.get_pillar_for_item(kt_name)
                })
        
        if not kt_values:
            st.error("No valid KT values calculated. Check your data.")
            return
        
        overall_score = sum(kt_values) / len(kt_values)
        
        # Main Score Display
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            # Determine overall rating based on average
            if overall_score >= 0.9:
                overall_rating = "Excellent Performance"
                rating_color = "#00c851"
            elif overall_score >= 0.7:
                overall_rating = "Good Performance"
                rating_color = "#ffbb33"
            elif overall_score >= 0.5:
                overall_rating = "Satisfactory"
                rating_color = "#ff8800"
            else:
                overall_rating = "Needs Improvement"
                rating_color = "#ff4444"
            
            st.markdown(f"""
            <div class="main-score-card">
                <h1 style="margin: 0; font-weight: 300;">Overall Assessment Score</h1>
                <div style="font-size: 5rem; font-weight: 700; margin: 1rem 0;">
                    {overall_score:.3f}
                </div>
                <div style="font-size: 1.5rem; padding: 0.5rem 2rem; 
                            background: {rating_color}; display: inline-block; 
                            border-radius: 25px; margin-top: 1rem;">
                    {overall_rating}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick Stats
        st.markdown("### Quick Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            good_count = len([k for k in kt_details if k['rating'] == 'Good'])
            st.metric("Good KTs", f"{good_count}/{len(kt_details)}", 
                    f"{(good_count/len(kt_details)*100):.0f}%")
        
        with col2:
            ps_count = len([r for r in st.session_state.ps_results.values() 
                        if isinstance(r.get('value'), (int, float))])
            st.metric("Active PSs", ps_count, "Performance Signals")
        
        with col3:
            ac_count = len([r for r in st.session_state.ac_results.values() 
                        if r.get('value') is not None])
            st.metric("Calculated ACs", ac_count, "Assessment Criteria")
        
        with col4:
            dp_count = len([v for v in st.session_state.dp_values.values() if v])
            st.metric("Data Points", dp_count, "Inputs Loaded")
        
        # Department Performance
        st.markdown("### Department Performance")
        
        # Group KTs by pillar
        pillar_performance = {}
        for kt in kt_details:
            pillar = kt['pillar']
            if pillar not in pillar_performance:
                pillar_performance[pillar] = []
            pillar_performance[pillar].append(kt)
        
        # Create tabs for each department
        if pillar_performance:
            tabs = st.tabs([self.pillar_config.get(p, {'name': p})['name'] 
                        for p in sorted(pillar_performance.keys())])
            
            for idx, (pillar, kts) in enumerate(sorted(pillar_performance.items())):
                with tabs[idx]:
                    config = self.pillar_config.get(pillar, {'name': pillar, 'color': '#666'})
                    
                    # Calculate department average
                    dept_avg = sum(kt['value'] for kt in kts) / len(kts)
                    dept_rating = self._calculate_rating_from_db(dept_avg, {})  # Use default thresholds
                    
                    # Department summary
                    st.markdown(f"""
                    <div class="dept-section">
                        <h3 style="color: {config['color']}; margin-bottom: 1rem;">
                            {config['name']} Performance
                        </h3>
                        <div style="font-size: 2rem; font-weight: bold; color: {config['color']};">
                            Average Score: {dept_avg:.3f}
                        </div>
                        <div class="metric-bar">
                            <div class="metric-fill" style="width: {dept_avg*100:.1f}%; 
                                background: {config['color']};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # KT details for this department
                    for kt in kts:
                        col1, col2, col3 = st.columns([3, 1, 1])
                        with col1:
                            st.markdown(f"**{kt['name']}**")
                        with col2:
                            st.markdown(f"{kt['value']:.4f}")
                        with col3:
                            color = "#00c851" if kt['rating'] == 'Good' else "#ffbb33" if kt['rating'] == 'Satisfactory' else "#ff4444"
                            st.markdown(f"<span style='color: {color}; font-weight: bold;'>{kt['rating']}</span>", 
                                    unsafe_allow_html=True)
        
        # Calculation Flow Visualization
        with st.expander("View Calculation Hierarchy", expanded=False):
            st.markdown("### Data Flow")
            
            # Show the actual flow with real numbers
            flow_col1, flow_col2, flow_col3, flow_col4 = st.columns(4)
            
            with flow_col1:
                st.info(f"**{dp_count} Data Points**\nRaw Inputs")
            
            with flow_col2:
                st.success(f"**{ac_count} Assessment Criteria**\nCalculated from DPs")
            
            with flow_col3:
                st.warning(f"**{ps_count} Performance Signals**\nWeighted from ACs")
            
            with flow_col4:
                st.error(f"**{len(kt_details)} Key Topics**\nFinal Scores")
    
    def _calculate_rating_from_db(self, value, thresholds):
        """Calculate rating using actual database thresholds"""
        if not thresholds or not any(thresholds.values()):
            # Use default thresholds if none in database
            if value >= 0.9:
                return 'Good'
            elif value >= 0.7:
                return 'Satisfactory'
            else:
                return 'Needs Improvement'
        
        # Parse actual thresholds from database
        good = str(thresholds.get('good', ''))
        satisfactory = str(thresholds.get('satisfactory', ''))
        needs = str(thresholds.get('needs_improvement', ''))
        
        # Apply the actual threshold logic
        def check_threshold(threshold_str, value):
            if not threshold_str:
                return False
            
            threshold_str = str(threshold_str).strip().replace('%', '')
            
            try:
                if threshold_str.startswith('>='):
                    return value >= float(threshold_str[2:].strip()) / (100 if float(threshold_str[2:].strip()) > 1 else 1)
                elif threshold_str.startswith('>'):
                    return value > float(threshold_str[1:].strip()) / (100 if float(threshold_str[1:].strip()) > 1 else 1)
                elif threshold_str.startswith('<='):
                    return value <= float(threshold_str[2:].strip()) / (100 if float(threshold_str[2:].strip()) > 1 else 1)
                elif threshold_str.startswith('<'):
                    return value < float(threshold_str[1:].strip()) / (100 if float(threshold_str[1:].strip()) > 1 else 1)
                elif '-' in threshold_str:
                    parts = threshold_str.split('-')
                    if len(parts) == 2:
                        min_val = float(parts[0].strip()) / (100 if float(parts[0].strip()) > 1 else 1)
                        max_val = float(parts[1].strip()) / (100 if float(parts[1].strip()) > 1 else 1)
                        return min_val <= value <= max_val
            except:
                return False
            
            return False
        
        # Check thresholds in order
        if check_threshold(good, value):
            return 'Good'
        elif check_threshold(satisfactory, value):
            return 'Satisfactory'
        elif check_threshold(needs, value):
            return 'Needs Improvement'
        
        # Fallback
        if value >= 0.9:
            return 'Good'
        elif value >= 0.7:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'
    
    def render_calculation_details(self):
        """Enhanced calculation details with professional visualization"""
        st.markdown("""
        <style>
        .calc-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .formula-box {
            background: #f7f9fc;
            border-left: 4px solid #667eea;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 8px 8px 0;
            font-family: 'Courier New', monospace;
        }
        .calc-flow {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
        }
        .dp-card {
            background: #f0f4f8;
            padding: 0.75rem;
            border-radius: 6px;
            margin: 0.5rem 0;
        }
        .result-card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 1.5rem 0;
        }
        .rating-badge {
            display: inline-block;
            padding: 0.5rem 1.5rem;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }
        .rating-good {
            background: linear-gradient(135deg, #00c851 0%, #00a846 100%);
        }
        .rating-satisfactory {
            background: linear-gradient(135deg, #ffbb33 0%, #ff8800 100%);
        }
        .rating-needs {
            background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="calc-header"><h2 style="margin: 0;">Calculation Details & Analysis</h2></div>', unsafe_allow_html=True)
        
        if not st.session_state.ac_results:
            st.info("No calculations available. Please run calculations first.")
            return
        
        # Enhanced selection controls
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            view_level = st.selectbox(
                "View Level",
                ["Key Topics", "Performance Signals", "Assessment Criteria", "Data Points"],
                help="Navigate through the calculation hierarchy"
            )
        
        with col2:
            pillar_filter = st.selectbox(
                "Filter by Department",
                ["All"] + list(self.pillar_config.keys()),
                help="Filter by organizational pillar"
            )
        
        with col3:
            show_details = st.checkbox("Show Full Details", value=True)
        
        st.markdown("---")
        
        # Display based on selection with enhanced visualization
        if view_level == "Key Topics":
            self.render_kt_calculations_enhanced(pillar_filter, show_details)
        elif view_level == "Performance Signals":
            self.render_ps_calculations_enhanced(pillar_filter, show_details)
        elif view_level == "Assessment Criteria":
            self.render_ac_calculations_enhanced(pillar_filter, show_details)
        else:
            self.render_dp_values_enhanced(pillar_filter)
    
    def render_kt_calculations_enhanced(self, pillar_filter, show_details):
        """Enhanced KT calculation display with full transparency"""
        st.markdown("## Key Topic Calculations")
        
        for kt_name, kt_result in st.session_state.kt_results.items():
            pillar = self.get_pillar_for_item(kt_name)
            
            if pillar_filter != "All" and pillar != pillar_filter:
                continue
            
            if isinstance(kt_result.get('value'), (int, float)):
                # Determine rating
                kt_data = self.db.get('key_topics', {}).get(kt_name, {})
                thresholds = kt_data.get('thresholds', {})
                rating = self.get_rating_for_value(kt_result['value'], thresholds)
                
                # Create visual card
                with st.container():
                    # Header with rating color
                    rating_class = "rating-good" if rating == "Good" else "rating-satisfactory" if rating == "Satisfactory" else "rating-needs"
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <h3 style="margin: 0; color: #1a237e;">{kt_name}</h3>
                            <span class="rating-badge {rating_class}">{rating}</span>
                        </div>
                        <div style="font-size: 3rem; font-weight: bold; color: #667eea; margin: 1rem 0;">
                            {kt_result['value']:.4f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if show_details:
                        with st.expander("See Full Calculation", expanded=True):
                            # Get PS contributions
                            kt_data = self.db.get('key_topics', {}).get(kt_name, {})
                            ps_list = kt_data.get('performance_signals', [])
                            
                            if ps_list:
                                st.markdown("### Calculation Method: Weighted Average")
                                st.markdown("```")
                                st.write("KT Score = Σ(PS_value × PS_weight) / Σ(PS_weight)")
                                st.markdown("```")
                                
                                # Create calculation table
                                calc_data = []
                                total_weight = 0
                                weighted_sum = 0
                                
                                for ps_name in ps_list:
                                    if ps_name in st.session_state.ps_results:
                                        ps_result = st.session_state.ps_results[ps_name]
                                        ps_data = self.db.get('performance_signals', {}).get(ps_name, {})
                                        weight = float(ps_data.get('weight', 1))
                                        value = ps_result.get('value', 0)
                                        contribution = value * weight
                                        
                                        calc_data.append({
                                            'Performance Signal': ps_name,
                                            'Value': f"{value:.4f}",
                                            'Weight': f"{weight:.0f}",
                                            'Contribution': f"{contribution:.4f}"
                                        })
                                        
                                        total_weight += weight
                                        weighted_sum += contribution
                                
                                if calc_data:
                                    df = pd.DataFrame(calc_data)
                                    st.dataframe(df, use_container_width=True, hide_index=True)
                                    
                                    # Show step-by-step calculation
                                    st.markdown("### Step-by-Step Calculation:")
                                    st.markdown(f"""
                                    <div class="calc-flow">
                                        <p><strong>1. Weighted Contributions:</strong></p>
                                        <ul>
                                    """, unsafe_allow_html=True)
                                    
                                    for item in calc_data:
                                        st.markdown(f"<li>{item['Performance Signal']}: {item['Value']} × {item['Weight']} = {item['Contribution']}</li>", unsafe_allow_html=True)
                                    
                                    st.markdown(f"""
                                        </ul>
                                        <p><strong>2. Sum of Weighted Contributions:</strong> {weighted_sum:.4f}</p>
                                        <p><strong>3. Total Weight:</strong> {total_weight:.0f}</p>
                                        <p><strong>4. Final Score:</strong> {weighted_sum:.4f} ÷ {total_weight:.0f} = <span style="color: #667eea; font-weight: bold;">{kt_result['value']:.4f}</span></p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Show threshold application
                                    st.markdown("### Rating Assignment:")
                                    self.show_threshold_application(kt_result['value'], thresholds)
    
    def render_ps_calculations_enhanced(self, pillar_filter, show_details):
        """Enhanced PS calculation display with full transparency"""
        st.markdown("## Performance Signal Calculations")
        
        for ps_name, ps_result in st.session_state.ps_results.items():
            pillar = self.get_pillar_for_item(ps_name)
            
            if pillar_filter != "All" and pillar != pillar_filter:
                continue
            
            if isinstance(ps_result.get('value'), (int, float)):
                # Determine rating
                ps_data = self.db.get('performance_signals', {}).get(ps_name, {})
                thresholds = ps_data.get('thresholds', {})
                rating = self.get_rating_for_value(ps_result['value'], thresholds)
                
                # Create visual card
                rating_class = "rating-good" if rating == "Good" else "rating-satisfactory" if rating == "Satisfactory" else "rating-needs"
                
                st.markdown(f"""
                <div class="result-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3 style="margin: 0; color: #1a237e;">{ps_name}</h3>
                        <span class="rating-badge {rating_class}">{rating}</span>
                    </div>
                    <div style="font-size: 2.5rem; font-weight: bold; color: #764ba2; margin: 1rem 0;">
                        {ps_result['value']:.4f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if show_details:
                    with st.expander("See Full Calculation", expanded=False):
                        ac_list = ps_data.get('assessment_criteria', [])
                        
                        if ac_list:
                            st.markdown("### Calculation Method: Weighted Average")
                            st.markdown("```")
                            st.write("PS Score = Σ(AC_value × AC_weight) / Σ(AC_weight)")
                            st.markdown("```")
                            
                            calc_data = []
                            total_weight = 0
                            weighted_sum = 0
                            
                            for ac_name in ac_list:
                                if ac_name in st.session_state.ac_results:
                                    ac_result = st.session_state.ac_results[ac_name]
                                    ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
                                    weight = float(ac_data.get('weight', 1))
                                    value = ac_result.get('value', 0)
                                    
                                    if isinstance(value, (int, float)):
                                        contribution = value * weight
                                        calc_data.append({
                                            'Assessment Criteria': ac_name[:50] + "..." if len(ac_name) > 50 else ac_name,
                                            'Value': f"{value:.4f}",
                                            'Weight': f"{weight:.0f}",
                                            'Contribution': f"{contribution:.4f}"
                                        })
                                        
                                        total_weight += weight
                                        weighted_sum += contribution
                            
                            if calc_data:
                                df = pd.DataFrame(calc_data)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                                
                                # Show calculation flow
                                st.markdown(f"""
                                <div class="calc-flow">
                                    <p><strong>Weighted Sum:</strong> {weighted_sum:.4f}</p>
                                    <p><strong>Total Weight:</strong> {total_weight:.0f}</p>
                                    <p><strong>Final Score:</strong> {weighted_sum:.4f} ÷ {total_weight:.0f} = <span style="color: #764ba2; font-weight: bold;">{ps_result['value']:.4f}</span></p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Show threshold application
                                st.markdown("### Rating Assignment:")
                                self.show_threshold_application(ps_result['value'], thresholds)

    def render_ac_calculations_enhanced(self, pillar_filter, show_details):
        """Enhanced AC calculation display with visual formula breakdown"""
        st.markdown("## Assessment Criteria Calculations")
        
        for ac_name, ac_result in st.session_state.ac_results.items():
            pillar = self.get_pillar_for_item(ac_name)
            
            if pillar_filter != "All" and pillar != pillar_filter:
                continue
            
            if ac_result.get('value') is not None:
                ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
                formula = self.decode_special_chars(ac_data.get('formula', ''))
                thresholds = ac_data.get('thresholds', {})
                
                # Get rating
                if isinstance(ac_result.get('value'), (int, float)):
                    rating = self.get_rating_for_value(ac_result['value'], thresholds)
                    display_value = f"{ac_result['value']:.4f}"
                else:
                    rating = ac_result.get('rating', 'N/A')
                    display_value = str(ac_result.get('value'))
                
                # Create visual card
                rating_class = "rating-good" if rating == "Good" else "rating-satisfactory" if rating == "Satisfactory" else "rating-needs"
                
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### {ac_name[:80]}{'...' if len(ac_name) > 80 else ''}")
                    with col2:
                        st.markdown(f'<span class="rating-badge {rating_class}">{rating}</span>', unsafe_allow_html=True)
                    
                    if show_details:
                        with st.expander("See Full Calculation", expanded=False):
                            # Show formula
                            st.markdown("#### Formula:")
                            st.markdown(f'<div class="formula-box">{formula}</div>', unsafe_allow_html=True)
                            
                            # Show DPs used
                            dps_used = ac_data.get('data_points', [])
                            if dps_used:
                                st.markdown("#### Data Points Used:")
                                for dp_name in dps_used:
                                    if dp_name in st.session_state.dp_values:
                                        dp_value = st.session_state.dp_values[dp_name]
                                        if isinstance(dp_value, (int, float)):
                                            st.markdown(f"""
                                            <div class="dp-card">
                                                <strong>{dp_name}:</strong> {dp_value:.2f}
                                            </div>
                                            """, unsafe_allow_html=True)
                                        else:
                                            st.markdown(f"""
                                            <div class="dp-card">
                                                <strong>{dp_name}:</strong> {dp_value}
                                            </div>
                                            """, unsafe_allow_html=True)
                            
                            # Show calculation result
                            st.markdown("#### Result:")
                            st.markdown(f"""
                            <div class="result-card" style="text-align: center;">
                                <div style="font-size: 2rem; font-weight: bold; color: #667eea;">
                                    {display_value}
                                </div>
                                <div style="margin-top: 1rem;">
                                    <span class="rating-badge {rating_class}">{rating}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Show threshold application if quantitative
                            if isinstance(ac_result.get('value'), (int, float)):
                                st.markdown("#### Rating Assignment:")
                                self.show_threshold_application(ac_result['value'], thresholds)
    
    def show_threshold_application(self, value, thresholds):
        """Visual display of how thresholds determine rating"""
        if not thresholds or not any(thresholds.values()):
            st.info("Using default thresholds: Good ≥ 0.9, Satisfactory ≥ 0.7, Needs Improvement < 0.7")
            thresholds = {'good': '>0.9', 'satisfactory': '0.7-0.9', 'needs_improvement': '<0.7'}
        
        good = str(thresholds.get('good', ''))
        satisfactory = str(thresholds.get('satisfactory', ''))
        needs = str(thresholds.get('needs_improvement', ''))
        
        # Create visual threshold display
        st.markdown(f"""
        <div class="calc-flow">
            <p><strong>Value:</strong> {value:.4f}</p>
            <p><strong>Thresholds:</strong></p>
            <ul>
                <li>🟢 Good: {good}</li>
                <li>🟡 Satisfactory: {satisfactory}</li>
                <li>🔴 Needs Improvement: {needs}</li>
            </ul>
            <p><strong>Applied Rating:</strong> {self.get_rating_for_value(value, thresholds)}</p>
        </div>
        """, unsafe_allow_html=True)

    def get_rating_for_value(self, value, thresholds):
        """Determine rating based on value and thresholds"""
        if not thresholds or not any(thresholds.values()):
            # Default thresholds
            if value >= 0.9:
                return 'Good'
            elif value >= 0.7:
                return 'Satisfactory'
            else:
                return 'Needs Improvement'
        
        good = str(thresholds.get('good', ''))
        satisfactory = str(thresholds.get('satisfactory', ''))
        needs = str(thresholds.get('needs_improvement', ''))
        
        # Parse and apply thresholds
        def parse_threshold(threshold_str):
            if not threshold_str:
                return None, None
            
            threshold_str = str(threshold_str).strip()
            has_percent = '%' in threshold_str
            threshold_str = threshold_str.replace('%', '').strip()
            
            if threshold_str.startswith('>='):
                val = float(threshold_str[2:].strip())
                if has_percent and val > 1:
                    val = val / 100
                return '>=', val
            elif threshold_str.startswith('>'):
                val = float(threshold_str[1:].strip())
                if has_percent and val > 1:
                    val = val / 100
                return '>', val
            elif threshold_str.startswith('<='):
                val = float(threshold_str[2:].strip())
                if has_percent and val > 1:
                    val = val / 100
                return '<=', val
            elif threshold_str.startswith('<'):
                val = float(threshold_str[1:].strip())
                if has_percent and val > 1:
                    val = val / 100
                return '<', val
            elif '-' in threshold_str:
                parts = threshold_str.split('-')
                if len(parts) == 2:
                    try:
                        min_val = float(parts[0].strip())
                        max_val = float(parts[1].strip())
                        if has_percent and min_val > 1:
                            min_val = min_val / 100
                            max_val = max_val / 100
                        return 'range', (min_val, max_val)
                    except:
                        return None, None
            else:
                try:
                    val = float(threshold_str)
                    if has_percent and val > 1:
                        val = val / 100
                    return '>=', val
                except:
                    return None, None
        
        # Check thresholds
        op, threshold_val = parse_threshold(good)
        if op and threshold_val is not None:
            if op == '>' and value > threshold_val:
                return 'Good'
            elif op == '>=' and value >= threshold_val:
                return 'Good'
            elif op == 'range' and isinstance(threshold_val, tuple):
                if threshold_val[0] <= value <= threshold_val[1]:
                    return 'Good'
        
        op, threshold_val = parse_threshold(satisfactory)
        if op and threshold_val is not None:
            if op == 'range' and isinstance(threshold_val, tuple):
                if threshold_val[0] <= value <= threshold_val[1]:
                    return 'Satisfactory'
            elif op == '>=' and value >= threshold_val:
                return 'Satisfactory'
            elif op == '>' and value > threshold_val:
                return 'Satisfactory'
        
        op, threshold_val = parse_threshold(needs)
        if op and threshold_val is not None:
            if op == '<' and value < threshold_val:
                return 'Needs Improvement'
            elif op == '<=' and value <= threshold_val:
                return 'Needs Improvement'
        
        # Default fallback
        if value >= 0.9:
            return 'Good'
        elif value >= 0.7:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'
    
    def render_dp_values_enhanced(self, pillar_filter):
        """Enhanced DP values display"""
        st.markdown("## Data Point Values")
        
        dp_by_pillar = defaultdict(list)
        
        for dp_name, value in st.session_state.dp_values.items():
            pillar = self.get_pillar_for_item(dp_name)
            if pillar_filter == "All" or pillar == pillar_filter:
                dp_by_pillar[pillar].append({
                    'Data Point': dp_name,
                    'Value': f"{value:.2f}" if isinstance(value, (int, float)) else value,
                    'Type': self.db.get('data_points', {}).get(dp_name, {}).get('data_type', 'unknown')
                })
        
        for pillar, dps in dp_by_pillar.items():
            config = self.pillar_config.get(pillar, {'name': pillar, 'color': '#666'})
            
            st.markdown(f"""
            <div style="border-left: 4px solid {config['color']}; padding-left: 1rem; margin: 2rem 0;">
                <h3>{config['name']}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            if dps:
                df = pd.DataFrame(dps)
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    def render_formula_issues_advanced(self):
        """Advanced formula issues interface"""
        st.subheader(f"Formula Resolution - {len(st.session_state.formula_issues)} Issues")
        
        if not st.session_state.formula_issues:
            st.success("All formulas resolved.")
            return
        
        # Smart fix button
        if st.button("SMART AUTO-FIX ALL", type="primary", use_container_width=True):
            self.smart_auto_fix()
            st.rerun()
        
        # Group by pillar
        issues_by_pillar = defaultdict(list)
        for ac_name in st.session_state.formula_issues:
            pillar = self.get_pillar_for_item(ac_name)
            issues_by_pillar[pillar].append(ac_name)
        
        # Display by pillar
        pillar_tabs = []
        for pillar in sorted(issues_by_pillar.keys()):
            config = self.pillar_config.get(pillar, {'name': pillar})
            count = len(issues_by_pillar[pillar])
            pillar_tabs.append(f"{config['name']} ({count})")
        
        tabs = st.tabs(pillar_tabs)
        
        for idx, (pillar, issues) in enumerate(sorted(issues_by_pillar.items())):
            with tabs[idx]:
                for ac_name in issues:
                    self.render_single_issue_advanced(ac_name)
    
    def render_single_issue_advanced(self, ac_name):
        """Render single formula issue"""
        ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
        formula = self.decode_special_chars(ac_data.get('formula', ''))
        
        with st.expander(ac_name, expanded=False):
            st.markdown("**Current Formula**")
            st.markdown(f"""
            <div class="calc-box">
                <code>{formula}</code>
            </div>
            """, unsafe_allow_html=True)
            
            # Required DPs
            st.markdown("**Required Data Points**")
            required_dps = ac_data.get('data_points', [])
            if required_dps:
                dp_data = []
                for dp in required_dps:
                    value = st.session_state.dp_values.get(dp, "Missing")
                    dp_data.append({
                        'Data Point': dp,
                        'Value': f"{value:.2f}" if isinstance(value, (int, float)) else value,
                        'Status': "Available" if dp in st.session_state.dp_values else "Missing"
                    })
                df = pd.DataFrame(dp_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Resolution tabs
            tab1, tab2, tab3 = st.tabs(["Quick Override", "Formula Editor", "Variable Mapping"])
            
            with tab1:
                col1, col2 = st.columns(2)
                with col1:
                    # Use decimal scale
                    score = st.slider("Score", 0.0, 1.0, 0.85,
                                    key=self.get_unique_key("score", ac_name))
                with col2:
                    rating = st.selectbox("Rating", 
                                         ["Good", "Satisfactory", "Needs Improvement"],
                                         key=self.get_unique_key("rating", ac_name))
                
                if st.button("Apply", key=self.get_unique_key("apply", ac_name)):
                    st.session_state.formula_overrides[ac_name] = {
                        'value': score,
                        'rating': rating,
                        'type': 'manual_override'
                    }
                    st.success("Applied")
            
            with tab2:
                edited = st.text_area("Edit Formula", value=formula, height=100,
                                    key=self.get_unique_key("edit", ac_name))
                
                if st.button("Apply Formula", key=self.get_unique_key("apply_formula", ac_name)):
                    st.session_state.formula_overrides[ac_name] = edited
                    st.success("Formula updated")
            
            with tab3:
                self.render_variable_mapping_advanced(ac_name, formula)
    
    def render_variable_mapping_advanced(self, ac_name, formula):
        """Advanced variable mapping"""
        st.markdown("**Intelligent Formula Mapping**")
        
        if '/' in formula:
            parts = formula.split('/', 1)
            
            st.markdown("""
            <div class="calc-box">
                Division formula detected. Mapping components...
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Numerator**")
                st.code(parts[0])
                
                num_suggestions = self.suggest_dp_for_formula_part(parts[0])
                if num_suggestions:
                    for dp, score in num_suggestions[:3]:
                        color = "#2e7d32" if score > 0.8 else "#f57c00" if score > 0.6 else "#c62828"
                        st.markdown(f"<span style='color: {color};'>• {dp[:50]}... ({score:.0%})</span>",
                                  unsafe_allow_html=True)
                
                all_dps = list(self.db.get('data_points', {}).keys())
                num_dp = st.selectbox("Select numerator:",
                                     all_dps,
                                     index=0 if not num_suggestions else all_dps.index(num_suggestions[0][0]) 
                                           if num_suggestions[0][0] in all_dps else 0,
                                     key=self.get_unique_key("num", ac_name))
            
            with col2:
                st.markdown("**Denominator**")
                st.code(parts[1])
                
                den_suggestions = self.suggest_dp_for_formula_part(parts[1])
                if den_suggestions:
                    for dp, score in den_suggestions[:3]:
                        color = "#2e7d32" if score > 0.8 else "#f57c00" if score > 0.6 else "#c62828"
                        st.markdown(f"<span style='color: {color};'>• {dp[:50]}... ({score:.0%})</span>",
                                  unsafe_allow_html=True)
                
                den_dp = st.selectbox("Select denominator:",
                                     all_dps,
                                     index=0 if not den_suggestions else all_dps.index(den_suggestions[0][0])
                                           if den_suggestions[0][0] in all_dps else 0,
                                     key=self.get_unique_key("den", ac_name))
            
            if st.button("Apply Mapping", key=self.get_unique_key("apply_map", ac_name)):
                if num_dp in st.session_state.dp_values and den_dp in st.session_state.dp_values:
                    num_val = st.session_state.dp_values[num_dp]
                    den_val = st.session_state.dp_values[den_dp]
                    
                    if isinstance(num_val, (int, float)) and isinstance(den_val, (int, float)) and den_val != 0:
                        # Keep as decimal
                        result = num_val / den_val
                        st.session_state.formula_overrides[ac_name] = {
                            'type': 'mapping',
                            'value': result,
                            'rating': 'Good' if result >= 0.9 else 'Satisfactory' if result >= 0.7 else 'Needs Improvement'
                        }
                        st.success(f"Mapping applied. Result: {result:.4f}")
                    else:
                        st.warning("Check values")
                else:
                    st.info("DPs not loaded")
        else:
            st.info("Complex formula. Use manual override or formula editor.")
    
    def smart_auto_fix(self):
        """Smart auto-fix"""
        fixed = 0
        for ac_name in list(st.session_state.formula_issues):
            ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
            formula = self.decode_special_chars(ac_data.get('formula', ''))
            
            if '/' in formula:
                parts = formula.split('/', 1)
                num_suggestions = self.suggest_dp_for_formula_part(parts[0])
                den_suggestions = self.suggest_dp_for_formula_part(parts[1])
                
                if num_suggestions and den_suggestions:
                    if num_suggestions[0][1] > 0.6 and den_suggestions[0][1] > 0.6:
                        st.session_state.formula_overrides[ac_name] = {
                            'type': 'auto_fixed',
                            'value': 0.85,
                            'rating': 'Satisfactory'
                        }
                        fixed += 1
        
        st.success(f"Auto-fixed {fixed} formulas")
    
    def suggest_dp_for_formula_part(self, formula_part: str) -> List[Tuple[str, float]]:
        """Suggest DPs for formula part"""
        formula_clean = self.decode_special_chars(formula_part).lower()
        
        scores = []
        for dp_name in self.db.get('data_points', {}).keys():
            dp_lower = dp_name.lower()
            score = 0
            
            if formula_clean.strip() in dp_lower or dp_lower in formula_clean:
                score = 0.95
            else:
                formula_words = set(re.sub(r'[^\w\s]', ' ', formula_clean).split())
                dp_words = set(re.sub(r'[^\w\s]', ' ', dp_lower).split())
                
                common = formula_words & dp_words
                if common and len(formula_words) > 0:
                    score = len(common) / len(formula_words)
            
            if score > 0:
                scores.append((dp_name, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:5]
    
    def get_qualitative_options(self, thresholds):
        """Get qualitative options"""
        options = []
        if thresholds:
            for key, value in thresholds.items():
                if isinstance(value, str):
                    clean_value = value.strip()
                    if clean_value and clean_value not in ['>', '<', '>=', '<=', '>70%', '<30%']:
                        if not any(char in clean_value for char in ['%', '>', '<', '=']):
                            options.append(clean_value)
        
        if not options:
            options = ['Yes', 'Partial', 'No']
        
        return options
    
    def load_test_data_smart(self):
        """Load test data"""
        test_values = generate_better_test_values(self.db)
        st.session_state.dp_values = test_values
        
        for ac_name in st.session_state.ac_categories['qualitative']:
            ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
            thresholds = ac_data.get('thresholds', {})
            options = self.get_qualitative_options(thresholds)
            st.session_state.qualitative_inputs[ac_name] = options[0]
        
        st.success(f"Loaded {len(test_values)} DPs and {len(st.session_state.qualitative_inputs)} qualitative inputs")
    
    def calculate_all_comprehensive(self):
        """Calculate all"""
        progress = st.progress(0)
        status = st.empty()
        
        total_acs = len(self.db.get('assessment_criteria', {}))
        successful = 0
        
        st.session_state.formula_issues = []
        
        for idx, (ac_name, ac_data) in enumerate(self.db.get('assessment_criteria', {}).items()):
            status.text(f"Processing: {ac_name[:50]}...")
            
            if ac_name in st.session_state.formula_overrides:
                override = st.session_state.formula_overrides[ac_name]
                if isinstance(override, dict):
                    st.session_state.ac_results[ac_name] = override
                    successful += 1
                else:
                    result = self.engine.calculate_ac(
                        ac_name,
                        st.session_state.dp_values,
                        st.session_state.qualitative_inputs
                    )
                    st.session_state.ac_results[ac_name] = result
                    if result.get('value') is not None and result.get('value') != 0:
                        successful += 1
                    else:
                        st.session_state.formula_issues.append(ac_name)
            else:
                result = self.engine.calculate_ac(
                    ac_name,
                    st.session_state.dp_values,
                    st.session_state.qualitative_inputs
                )
                
                if result.get('value') is None or result.get('value') == 0:
                    st.session_state.formula_issues.append(ac_name)
                else:
                    successful += 1
                
                st.session_state.ac_results[ac_name] = result
            
            progress.progress((idx + 1) / total_acs)
        
        progress.empty()
        status.empty()
        
        self.aggregate_all()
        
        st.success(f"Calculated {successful}/{total_acs} ACs")
    
    def aggregate_all(self):
        """Aggregate to PS and KT"""
        for ps_name in self.db.get('performance_signals', {}).keys():
            result = self.engine.aggregate_to_ps(ps_name, st.session_state.ac_results)
            st.session_state.ps_results[ps_name] = result
        
        for kt_name in self.db.get('key_topics', {}).keys():
            result = self.engine.aggregate_to_kt(kt_name, st.session_state.ps_results)
            st.session_state.kt_results[kt_name] = result
    
    def export_results(self):
        """Export results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_acs': len(self.db.get('assessment_criteria', {})),
                'calculated_acs': len(st.session_state.ac_results),
                'formula_issues': len(st.session_state.formula_issues)
            },
            'kt_results': st.session_state.kt_results,
            'ps_results': st.session_state.ps_results,
            'ac_results': st.session_state.ac_results
        }
        
        json_str = json.dumps(results, indent=2, default=str)
        
        st.download_button(
            label="Download Results",
            data=json_str,
            file_name=f"assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    def render_main_interface(self):
        """Restructured main interface with dashboard first"""
        
        # Control buttons at top
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("LOAD TEST DATA", type="primary", use_container_width=True):
                self.load_test_data_smart()
        
        with col2:
            if st.button("CALCULATE ALL", type="primary", use_container_width=True):
                self.calculate_all_comprehensive()
        
        with col3:
            if st.button("CLEAR ALL", type="secondary", use_container_width=True):
                for key in ['dp_values', 'ac_results', 'ps_results', 'kt_results', 
                        'qualitative_inputs', 'formula_overrides']:
                    st.session_state[key] = {}
                st.success("Cleared")
        
        with col4:
            if st.button("EXPORT", type="secondary", use_container_width=True):
                self.export_results()
        
        st.markdown("---")
        
        # Dashboard FIRST, then other tabs
        tabs = ["Executive Dashboard", "Data Input", "Calculations"]
        
        if st.session_state.formula_issues:
            tabs.append(f"Issues ({len(st.session_state.formula_issues)})")
        
        tab_list = st.tabs(tabs)
        
        with tab_list[0]:
            self.render_executive_dashboard()
        
        with tab_list[1]:
            input_tabs = st.tabs(["Quantitative", "Qualitative"])
            with input_tabs[0]:
                self.render_quantitative_input_by_pillar()
            with input_tabs[1]:
                self.render_qualitative_input_by_pillar()
        
        with tab_list[2]:
            self.render_calculation_details()
        
        if st.session_state.formula_issues and len(tab_list) > 3:
            with tab_list[3]:
                self.render_formula_issues_advanced()
    
    def run(self):
        """Main entry"""
        self.render_header()
        self.render_metrics()
        st.markdown("---")
        self.render_main_interface()

if __name__ == "__main__":
    app = AdvancedMeinhardt()
    app.run()