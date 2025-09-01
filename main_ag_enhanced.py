"""
Enhanced Main AG Module - Professional Industry-Grade Version
Complete with calculation visualization, qualitative formulas, and professional UI
"""

import streamlit as st
import json
from datetime import datetime
import random
import pandas as pd
from typing import Dict, Any, List, Tuple

# Import the components
from formula_parser_complete import FormulaParser, QualitativeDropdownHandler, WeightedAggregator
from calculation_visualizer import CalculationVisualizer, QualitativeFormulaHandler

class MainAGEnhanced:
    def __init__(self):
        self.parser = FormulaParser()
        self.aggregator = WeightedAggregator()
        self.visualizer = CalculationVisualizer()
        self.qual_handler = QualitativeFormulaHandler()
        self.load_database()
        self.fix_database_hierarchy()
        
        # Professional styling
        self._apply_custom_css()
    
    def _apply_custom_css(self):
        """Apply professional custom CSS styling"""
        st.markdown("""
        <style>
        /* Professional color scheme */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 10px 24px;
            background-color: #f8f9fa;
            border-radius: 8px 8px 0 0;
            font-weight: 500;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #0066cc;
            color: white;
        }
        
        /* Metric cards styling */
        [data-testid="metric-container"] {
            background-color: #ffffff;
            border: 1px solid #e3e3e3;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #f8f9fa;
            border-radius: 8px;
            font-weight: 500;
        }
        
        /* Professional button styling */
        .stButton > button {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            background-color: #0052a3;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Success/Warning/Error messages */
        .stSuccess {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
            border-radius: 6px;
        }
        
        .element-container .stMarkdown h3 {
            color: #333;
            font-weight: 600;
            margin-top: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def load_database(self):
        """Load the database"""
        try:
            with open('data/meinhardt_db.json', 'r') as f:
                self.database = json.load(f)
        except:
            st.error("Database not found. Please run Phase 1 parser first.")
            self.database = {}
    
    def fix_database_hierarchy(self):
        """Fix missing pillar assignments in Key Topics"""
        if 'key_topics' not in self.database:
            return
        
        fixed_count = 0
        
        for kt_name, kt_data in self.database['key_topics'].items():
            if 'pillar' not in kt_data or not kt_data.get('pillar'):
                pillar = self._infer_kt_pillar(kt_name, kt_data)
                if pillar:
                    kt_data['pillar'] = pillar
                    fixed_count += 1
        
        if fixed_count > 0:
            with open('data/meinhardt_db.json', 'w') as f:
                json.dump(self.database, f, indent=2)
    
    def _infer_kt_pillar(self, kt_name: str, kt_data: dict) -> str:
        """Infer pillar for a Key Topic"""
        kt_lower = kt_name.lower()
        
        # Map based on KT name patterns
        pillar_patterns = {
            'Planning & Monitoring': ['schedule', 'planning', 'monitoring', 'progress'],
            'Design & Technical': ['design', 'technical'],
            'Delivery & Construction': ['delivery', 'construction'],
            'Commercial, Economic & Outcomes': ['commercial', 'economic'],
            'Innovation & Technology': ['innovation', 'technology'],
            'Sustainability & Operations': ['sustainability', 'operations']
        }
        
        for pillar, patterns in pillar_patterns.items():
            if any(pattern in kt_lower for pattern in patterns):
                return pillar
        
        # Try to infer from connected data
        for ps_name in kt_data.get('performance_signals', []):
            ps_data = self.database.get('performance_signals', {}).get(ps_name, {})
            for ac_name in ps_data.get('assessment_criteria', []):
                ac_data = self.database.get('assessment_criteria', {}).get(ac_name, {})
                for dp_name in ac_data.get('data_points', []):
                    dp_data = self.database.get('data_points', {}).get(dp_name, {})
                    if dp_data.get('pillar'):
                        return self._expand_pillar_name(dp_data['pillar'])
        
        return None
    
    def _expand_pillar_name(self, abbreviation: str) -> str:
        """Convert pillar abbreviation to full name"""
        pillar_map = {
            'P&M': 'Planning & Monitoring',
            'D&T': 'Design & Technical',
            'D&C': 'Delivery & Construction',
            'CE&O': 'Commercial, Economic & Outcomes',
            'I&T': 'Innovation & Technology',
            'S&O': 'Sustainability & Operations'
        }
        return pillar_map.get(abbreviation, abbreviation)
    
    def render(self):
        """Main render method with professional UI"""
        # Professional header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0066cc 0%, #004499 100%); 
                    padding: 30px; margin: -20px -20px 20px -20px; border-radius: 0 0 15px 15px;">
            <h1 style="color: white; margin: 0;">Assessment Guide Module</h1>
            <p style="color: #e6f0ff; margin: 10px 0 0 0;">Professional Assessment Input & Calculation System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Assessment management section
        self._render_assessment_management()
        
        if 'current_assessment' in st.session_state:
            # Professional tab interface
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                " Data Input",
                " Calculation Analysis",
                " Interactive Visualization",
                " Executive Summary",
                " AC Validation"
            ])
            
            with tab1:
                self._render_data_input_enhanced()
            
            with tab2:
                self._render_calculation_analysis()
            
            with tab3:
                self._render_interactive_visualization()
            
            with tab4:
                self._render_executive_summary()

            with tab5:
                from ac_validation_fixed import ACValidatorFixed
                validator = ACValidatorFixed()
                validator.render_validation_tab()
    
    def _render_assessment_management(self):
        """Enhanced assessment management with better UI"""
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
            
            with col1:
                assessment_name = st.text_input(
                    "Assessment Project",
                    value=st.session_state.get('assessment_name', 'New Assessment'),
                    placeholder="Enter project name..."
                )
            
            with col2:
                if st.button("Create/Load", use_container_width=True):
                    self._create_assessment(assessment_name)
            
            with col3:
                if st.button("Generate Test Data", use_container_width=True):
                    self._fill_test_data()
            
            with col4:
                if st.button("Quick Calculate", use_container_width=True):
                    if 'current_assessment' in st.session_state:
                        self._calculate_all()

            with col5:
                if st.button("🔄", use_container_width=True, help= "Clear all assessment data but keep database structure"):
                    self._clear_assessment_data()
                    st.rerun()
        
        st.markdown("---")
    
    def _create_assessment(self, name: str):
        """Create or load an assessment"""
        assessment_id = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        st.session_state['current_assessment'] = assessment_id
        st.session_state['assessment_name'] = name
        
        if 'assessments' not in st.session_state:
            st.session_state['assessments'] = {}
        
        if assessment_id not in st.session_state['assessments']:
            st.session_state['assessments'][assessment_id] = {
                'name': name,
                'created_at': datetime.now().isoformat(),
                'dp_values': {},
                'ac_results': {},
                'ps_results': {},
                'kt_results': {},
                'overall_score': {},
                'calculation_history': []
            }
        
        st.success(f"Assessment '{name}' ready")
    
    def _fill_test_data(self):
        """Fill all DPs with intelligent test data AND SAVE TO DATABASE"""
        if 'current_assessment' not in st.session_state:
            st.error("Please create an assessment first")
            return
        
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        # Generate test data with more realistic values
        for dp_name, dp_data in self.database.get('data_points', {}).items():
            data_type = dp_data.get('data_type', 'number')
            dp_lower = dp_name.lower()
            
            # CRITICAL FIX: Use realistic values
            if 'earned value' in dp_lower:
                value = random.uniform(1000000, 5000000)  # 1M to 5M
            elif 'planned value' in dp_lower:
                value = random.uniform(5000000, 10000000)  # 5M to 10M
            elif 'actual cost' in dp_lower:
                value = random.uniform(1000000, 8000000)
            elif 'budget' in dp_lower or 'budget at completion' in dp_lower:
                value = random.uniform(5000000, 15000000)
            elif 'number of' in dp_lower:
                if 'total' in dp_lower:
                    value = random.randint(50, 200)
                else:
                    value = random.randint(5, 50)
            elif 'percentage' in dp_lower or '%' in dp_name:
                value = random.uniform(60, 95)
            elif data_type == 'percentage':
                value = random.uniform(65, 90)
            elif data_type == 'boolean':
                value = random.choice(['Yes', 'Yes', 'Partial', 'No'])
            elif data_type == 'date':
                value = datetime.now().strftime('%Y-%m-%d')
            elif 'cost' in dp_lower or 'value' in dp_lower or 'amount' in dp_lower:
                value = random.uniform(100000, 5000000)
            elif data_type == 'number':
                value = random.uniform(100, 10000)
            else:
                value = random.choice(['Completed', 'In Progress', 'Planned'])
            
            assessment['dp_values'][dp_name] = value
        
        # Save to database file
        assessment_id = st.session_state['current_assessment']
        if 'assessments' not in self.database:
            self.database['assessments'] = {}
        self.database['assessments'][assessment_id] = assessment
        
        # Write to file immediately
        with open('data/meinhardt_db.json', 'w') as f:
            json.dump(self.database, f, indent=2)
        
        st.success(f"Generated test data for {len(assessment['dp_values'])} data points")
        st.rerun()

    def _clear_assessment_data(self):
        """Clear only assessment data from database, keeping structure intact"""
        if 'assessments' in self.database:
            del self.database['assessments']
        
        with open('data/meinhardt_db.json', 'w') as f:
            json.dump(self.database, f, indent=2)
        
        if 'assessments' in st.session_state:
            st.session_state['assessments'] = {}
        if 'current_assessment' in st.session_state:
            del st.session_state['current_assessment']
        
        st.info("Cleared assessment data while keeping database structure")
    
    def _render_data_input_enhanced(self):
        """Enhanced data input interface with better organization"""
        st.subheader("Data Point Input Interface")
        
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        # Add search and filter options
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("Search Data Points", placeholder="Type to search...")
        with col2:
            filter_type = st.selectbox("Filter by Type", ["All", "Number", "Percentage", "Boolean", "Text"])
        
        # Group DPs by pillar
        pillars = {}
        for dp_name, dp_data in self.database.get('data_points', {}).items():
            # Apply filters
            if search_term and search_term.lower() not in dp_name.lower():
                continue
            if filter_type != "All" and dp_data.get('data_type', '').lower() != filter_type.lower():
                continue
            
            pillar = dp_data.get('pillar', 'Other')
            if pillar not in pillars:
                pillars[pillar] = []
            pillars[pillar].append((dp_name, dp_data))
        
        # Create tabs for each pillar
        if pillars:
            pillar_tabs = st.tabs(list(pillars.keys()))
            
            for tab, (pillar, dps) in zip(pillar_tabs, pillars.items()):
                with tab:
                    # Show statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total DPs", len(dps))
                    with col2:
                        filled = sum(1 for dp_name, _ in dps if dp_name in assessment['dp_values'])
                        st.metric("Filled", filled)
                    with col3:
                        completion = (filled / len(dps) * 100) if dps else 0
                        st.metric("Completion", f"{completion:.0f}%")
                    
                    st.markdown("---")
                    
                    # Create input grid with better layout
                    cols = st.columns(2)
                    for idx, (dp_name, dp_data) in enumerate(dps):
                        with cols[idx % 2]:
                            current_value = assessment['dp_values'].get(dp_name, '')
                            data_type = dp_data.get('data_type', 'text')
                            
                            # Create appropriate input based on type
                            if data_type == 'number':
                                value = st.number_input(
                                    dp_name,
                                    value=float(current_value) if current_value else 0.0,
                                    key=f"dp_{dp_name}",
                                    format="%.2f"
                                )
                            elif data_type == 'percentage':
                                value = st.slider(
                                    dp_name,
                                    0.0, 100.0,
                                    value=float(current_value) if current_value else 0.0,
                                    key=f"dp_{dp_name}",
                                    format="%.1f%%"
                                )
                            elif data_type == 'boolean' or self.parser._is_qualitative(dp_data.get('formula', '')):
                                # Get appropriate dropdown options
                                qual_handler = QualitativeDropdownHandler()
                                ac_data = self._find_ac_for_dp(dp_name)  # You'll need to implement this
                                
                                if ac_data:
                                    options, scores = qual_handler.get_dropdown_options(
                                        ac_data.get('formula', ''),
                                        ac_data.get('thresholds', {})
                                    )
                                else:
                                    options = ['Yes', 'Partial', 'No']
                                
                                value = st.selectbox(
                                    dp_name,
                                    options,
                                    index=0 if current_value not in options else options.index(current_value),
                                    key=f"dp_{dp_name}"
                                )
                            else:
                                value = st.text_input(
                                    dp_name,
                                    value=current_value,
                                    key=f"dp_{dp_name}",
                                    placeholder="Enter value..."
                                )
                            
                            # Update value if changed
                            if value != current_value:
                                assessment['dp_values'][dp_name] = value
                    
                    # Calculate button for this pillar
                    st.markdown("---")
                    if st.button(f"Calculate {pillar}", key=f"calc_{pillar}", use_container_width=True):
                        self._calculate_pillar(pillar)
        
        # Master calculate button
        st.markdown("---")
        if st.button("Calculate Complete Assessment", type="primary", key="calc_all", use_container_width=True):
            self._calculate_all()
    
    def _render_calculation_analysis(self):
        """Render detailed calculation analysis"""
        st.subheader("Calculation Analysis & Breakdown")
        
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        if not assessment.get('ac_results'):
            st.info("No calculations performed yet. Please input data and calculate.")
            return
        
        # Use the calculation visualizer
        self.visualizer.render_calculation_tree(assessment, self.database)

    def _render_interactive_visualization(self):
        """Render professional interactive visualization"""
        st.subheader("Interactive Calculation Hierarchy")
        
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        if not assessment.get('kt_results'):
            st.info("No results to visualize. Please perform calculations first.")
            return
        
        # Overall score card with professional design
        overall = assessment.get('overall_score', {})
        if overall:
            # Create columns for better layout
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                # Professional score card
                score_color = self._get_score_color(overall.get('value', 0))
                st.markdown(f"""
                <div style="
                    background: white;
                    border: 3px solid {score_color};
                    border-radius: 20px;
                    padding: 40px;
                    text-align: center;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                ">
                    <h2 style="margin: 0; color: #333; font-weight: 300;">Overall Assessment Score</h2>
                    <h1 style="
                        font-size: 72px; 
                        margin: 20px 0; 
                        color: {score_color};
                        font-weight: bold;
                    ">{overall.get('value', 0):.1f}%</h1>
                    <p style="
                        font-size: 24px; 
                        margin: 0; 
                        color: #666;
                        font-weight: 500;
                    ">{overall.get('rating', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Hierarchical View", "Performance Matrix", "Detailed Breakdown"])
        
        with tab1:
            self._render_hierarchical_view(assessment)
        
        with tab2:
            self._render_performance_matrix(assessment)
        
        with tab3:
            self._render_detailed_breakdown(assessment)

    def _render_hierarchical_view(self, assessment: Dict):
        """Render hierarchical tree view"""
        st.markdown("### Assessment Hierarchy")
        
        # Create tree structure
        for kt_name, kt_result in assessment.get('kt_results', {}).items():
            value = kt_result.get('value', 0)
            rating = kt_result.get('rating', 'N/A')
            color = self._get_score_color(value)
            
            # KT level card
            with st.expander(f"📊 **{kt_name}** - {value:.1f}% ({rating})", expanded=False):
                # KT details
                kt_data = self.database.get('key_topics', {}).get(kt_name, {})
                
                # Progress bar for KT score (with safety check)
                progress_value = min(max(value / 100, 0), 1.0)  # Ensure between 0 and 1
                st.progress(progress_value)
                
                # PS breakdown
                st.markdown("#### Performance Signals")
                ps_list = kt_data.get('performance_signals', [])
                
                if ps_list:
                    ps_cols = st.columns(len(ps_list) if len(ps_list) <= 3 else 3)
                    
                    for idx, ps_name in enumerate(ps_list):
                        if ps_name in assessment.get('ps_results', {}):
                            ps_result = assessment['ps_results'][ps_name]
                            ps_value = ps_result.get('value', 0)
                            
                            with ps_cols[idx % len(ps_cols)]:
                                # Mini card for PS
                                ps_color = self._get_score_color(ps_value)
                                st.markdown(f"""
                                <div style="
                                    background: white;
                                    border: 1px solid {ps_color};
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin: 5px 0;
                                    text-align: center;
                                ">
                                    <h5 style="margin: 0; color: #666; font-size: 14px;">{ps_name[:30]}...</h5>
                                    <h3 style="margin: 10px 0; color: {ps_color};">{ps_value:.1f}%</h3>
                                    <p style="margin: 0; color: #999; font-size: 12px;">{ps_result.get('rating', 'N/A')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # AC details in collapsible
                    if st.checkbox(f"Show Assessment Criteria for {kt_name}", key=f"ac_{kt_name}"):
                        st.markdown("#### Assessment Criteria Breakdown")
                        
                        for ps_name in ps_list:
                            ps_data = self.database.get('performance_signals', {}).get(ps_name, {})
                            ac_list = ps_data.get('assessment_criteria', [])
                            
                            if ac_list:
                                st.markdown(f"##### {ps_name}")
                                
                                ac_data = []
                                for ac_name in ac_list:
                                    if ac_name in assessment.get('ac_results', {}):
                                        ac_result = assessment['ac_results'][ac_name]
                                        ac_data.append({
                                            'Criteria': ac_name[:50] + '...' if len(ac_name) > 50 else ac_name,
                                            'Score': f"{ac_result.get('value', 0):.2f}%",
                                            'Weight': f"{self.database.get('assessment_criteria', {}).get(ac_name, {}).get('weight', 0):.1f}%",
                                            'Rating': ac_result.get('rating', 'N/A')
                                        })
                                
                                if ac_data:
                                    df = pd.DataFrame(ac_data)
                                    st.dataframe(df, use_container_width=True, hide_index=True)

    def _render_performance_matrix(self, assessment: Dict):
        """Render performance matrix view"""
        st.markdown("### Performance Matrix")
        
        # Create matrix data
        matrix_data = []
        
        for kt_name, kt_result in assessment.get('kt_results', {}).items():
            kt_data = self.database.get('key_topics', {}).get(kt_name, {})
            
            for ps_name in kt_data.get('performance_signals', []):
                if ps_name in assessment.get('ps_results', {}):
                    ps_result = assessment['ps_results'][ps_name]
                    
                    matrix_data.append({
                        'Key Topic': kt_name[:30] + '...' if len(kt_name) > 30 else kt_name,
                        'Performance Signal': ps_name[:30] + '...' if len(ps_name) > 30 else ps_name,
                        'PS Score': ps_result.get('value', 0),
                        'PS Weight': self.database.get('performance_signals', {}).get(ps_name, {}).get('weight', 0),
                        'Rating': ps_result.get('rating', 'N/A')
                    })
        
        if matrix_data:
            df = pd.DataFrame(matrix_data)
            
            # Create pivot table
            pivot = df.pivot_table(
                index='Key Topic',
                columns='Rating',
                values='PS Score',
                aggfunc='count',
                fill_value=0
            )
            
            # Display matrix
            st.markdown("#### Performance Distribution by Key Topic")
            
            # Create a styled pivot table
            if not pivot.empty:
                styled_pivot = pivot.style.background_gradient(cmap='RdYlGn', axis=None, vmin=0)
                st.dataframe(styled_pivot, use_container_width=True)
            
            st.markdown("---")
            
            # Detailed table
            st.markdown("#### Detailed Performance Signals")
            
            # Style the dataframe
            def color_rating(val):
                if val == 'Good':
                    return 'background-color: #d4edda; color: #155724;'
                elif val == 'Satisfactory':
                    return 'background-color: #fff3cd; color: #856404;'
                else:
                    return 'background-color: #f8d7da; color: #721c24;'
            
            styled_df = df.style.format({
                'PS Score': '{:.1f}%',
                'PS Weight': '{:.1f}%'
            }).applymap(color_rating, subset=['Rating'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

    def _render_detailed_breakdown(self, assessment: Dict):
        """Render detailed breakdown with all calculations"""
        st.markdown("### Detailed Calculation Breakdown")
        
        # Create selection box for KT
        kt_names = list(assessment.get('kt_results', {}).keys())
        selected_kt = st.selectbox("Select Key Topic for Detailed View", kt_names)
        
        if selected_kt:
            kt_result = assessment['kt_results'][selected_kt]
            kt_data = self.database.get('key_topics', {}).get(selected_kt, {})
            
            # KT Summary Card
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("KT Score", f"{kt_result.get('value', 0):.1f}%")
            with col2:
                st.metric("Rating", kt_result.get('rating', 'N/A'))
            with col3:
                st.metric("PS Count", kt_result.get('ps_count', 0))
            with col4:
                st.metric("Status", kt_result.get('status', 'N/A').title())
            
            st.markdown("---")
            
            # PS Details
            st.markdown("#### Performance Signals Detail")
            
            for ps_name in kt_data.get('performance_signals', []):
                if ps_name in assessment.get('ps_results', {}):
                    ps_result = assessment['ps_results'][ps_name]
                    ps_data = self.database.get('performance_signals', {}).get(ps_name, {})
                    
                    with st.expander(f"{ps_name} - {ps_result.get('value', 0):.1f}%", expanded=True):
                        # PS metrics
                        ps_cols = st.columns(4)
                        with ps_cols[0]:
                            st.metric("Score", f"{ps_result.get('value', 0):.1f}%")
                        with ps_cols[1]:
                            st.metric("Weight", f"{ps_data.get('weight', 0):.1f}%")
                        with ps_cols[2]:
                            st.metric("AC Count", ps_result.get('ac_count', 0))
                        with ps_cols[3]:
                            st.metric("Rating", ps_result.get('rating', 'N/A'))
                        
                        # AC Table
                        st.markdown("##### Assessment Criteria")
                        
                        ac_details = []
                        for ac_name in ps_data.get('assessment_criteria', []):
                            if ac_name in assessment.get('ac_results', {}):
                                ac_result = assessment['ac_results'][ac_name]
                                ac_info = self.database.get('assessment_criteria', {}).get(ac_name, {})
                                
                                ac_details.append({
                                    'Assessment Criteria': ac_name,
                                    'Formula': ac_info.get('formula', '')[:50] + '...' if len(ac_info.get('formula', '')) > 50 else ac_info.get('formula', ''),
                                    'Value': self._format_ac_value(ac_result),
                                    'Weight': f"{ac_info.get('weight', 0):.1f}%",
                                    'Rating': ac_result.get('rating', 'N/A')
                                })
                        
                        if ac_details:
                            df = pd.DataFrame(ac_details)
                            st.dataframe(df, use_container_width=True, hide_index=True)
    
    def _render_hierarchy_node(self, kt_name: str, kt_result: Dict, assessment: Dict, level: int):
        """Render a node in the hierarchy with proper indentation"""
        
        indent = "  " * level
        rating = kt_result.get('rating', 'N/A')
        value = kt_result.get('value', 0)
        
        # Color coding
        color = "#28a745" if rating == "Good" else "#ffc107" if rating == "Satisfactory" else "#dc3545"
        
        # Render the node
        with st.expander(f"{indent} {kt_name} - {value:.1f}% ({rating})"):
            # Show details and child nodes
            kt_data = self.database.get('key_topics', {}).get(kt_name, {})
            
            # Show PS nodes
            for ps_name in kt_data.get('performance_signals', []):
                if ps_name in assessment.get('ps_results', {}):
                    ps_result = assessment['ps_results'][ps_name]
                    st.markdown(f"**{ps_name}**: {ps_result.get('value', 0):.1f}% ({ps_result.get('rating', 'N/A')})")
                    
                    # Show AC details
                    ps_data = self.database.get('performance_signals', {}).get(ps_name, {})
                    for ac_name in ps_data.get('assessment_criteria', []):
                        if ac_name in assessment.get('ac_results', {}):
                            ac_result = assessment['ac_results'][ac_name]
                            value_str = self._format_ac_value(ac_result)
                            st.write(f"  • {ac_name}: {value_str} ({ac_result.get('rating', 'N/A')})")

    def _render_executive_summary(self):
        """Render professional executive summary with enhanced UI"""
        st.subheader("Executive Summary")
        
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        if not assessment.get('overall_score'):
            st.info("No assessment results available. Please perform calculations first.")
            return
        
        # Top-level metrics with better styling
        overall = assessment.get('overall_score', {})
        
        # Create a styled header for overall score
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        ">
            <h2 style="margin: 0; color: #333;">Overall Assessment Score</h2>
            <h1 style="font-size: 60px; margin: 15px 0; color: {self._get_score_color(overall.get('value', 0))};">
                {overall.get('value', 0):.1f}%
            </h1>
            <p style="font-size: 24px; margin: 0; font-weight: 600; color: #666;">
                {overall.get('rating', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Rating distribution
        col1, col2, col3, col4 = st.columns(4)
        
        kt_results = assessment.get('kt_results', {})
        total_kts = len(kt_results) if kt_results else 1
        
        good_count = sum(1 for r in kt_results.values() if r.get('rating') == 'Good')
        satisfactory_count = sum(1 for r in kt_results.values() if r.get('rating') == 'Satisfactory')
        needs_improvement_count = sum(1 for r in kt_results.values() if r.get('rating') == 'Needs Improvement')
        
        with col1:
            self._render_stat_card("Total Topics", str(total_kts), "#0066cc")
        
        with col2:
            self._render_stat_card("Good", str(good_count), "#28a745", 
                                f"{good_count/total_kts*100:.0f}%")
        
        with col3:
            self._render_stat_card("Satisfactory", str(satisfactory_count), "#ffc107",
                                f"{satisfactory_count/total_kts*100:.0f}%")
        
        with col4:
            self._render_stat_card("Needs Improvement", str(needs_improvement_count), "#dc3545",
                                f"{needs_improvement_count/total_kts*100:.0f}%")
        
        st.markdown("---")
        
        # Key Topics Grid with uniform cards
        st.markdown("### Key Topics Performance")
        
        if kt_results:
            # Sort by score for better presentation
            sorted_kts = sorted(kt_results.items(), key=lambda x: x[1].get('value', 0), reverse=True)
            
            # Create uniform grid
            cols = st.columns(3)
            for idx, (kt_name, kt_result) in enumerate(sorted_kts):
                with cols[idx % 3]:
                    self._render_uniform_kt_card(kt_name, kt_result)
        
        st.markdown("---")
        
        # Enhanced PS Table (FIXED VERSION - NO HTML IN STATUS)
        st.markdown("### Performance Signals Analysis")
        
        ps_results = assessment.get('ps_results', {})
        if ps_results:
            # Create enhanced DataFrame
            ps_data = []
            for ps_name, ps_result in ps_results.items():
                ps_info = self.database.get('performance_signals', {}).get(ps_name, {})
                ps_data.append({
                    'Signal': ps_name,
                    'Score': ps_result.get('value', 0),
                    'Weight': ps_info.get('weight', 0),
                    'Rating': ps_result.get('rating', 'N/A')
                })
            
            if ps_data:
                df = pd.DataFrame(ps_data)
                df = df.sort_values('Score', ascending=False)
                
                # Create a styled dataframe with color coding for ratings
                def style_rating(val):
                    """Style the rating column"""
                    if val == 'Good':
                        return 'color: #28a745; font-weight: bold'
                    elif val == 'Satisfactory':
                        return 'color: #ffc107; font-weight: bold'
                    elif val == 'Needs Improvement':
                        return 'color: #dc3545; font-weight: bold'
                    return ''
                
                # Apply styling
                styled_df = df.style.format({
                    'Score': '{:.1f}%',
                    'Weight': '{:.1f}%'
                }).background_gradient(
                    subset=['Score'], 
                    cmap='RdYlGn', 
                    vmin=0, 
                    vmax=100
                ).applymap(style_rating, subset=['Rating'])
                
                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
        
        st.markdown("---")
        
        # Professional Recommendations
        self._render_professional_recommendations(assessment)

    def _render_stat_card(self, title: str, value: str, color: str, subtitle: str = ""):
        """Render a professional statistics card"""
        st.markdown(f"""
        <div style="
            background: white;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
            height: 100px;
        ">
            <p style="margin: 0; color: #666; font-size: 14px;">{title}</p>
            <h3 style="margin: 5px 0; color: {color}; font-size: 28px;">{value}</h3>
            <p style="margin: 0; color: #999; font-size: 12px;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

    def _render_uniform_kt_card(self, kt_name: str, kt_result: Dict):
        """Render uniform KT performance card"""
        value = kt_result.get('value', 0)
        rating = kt_result.get('rating', 'N/A')
        color = self._get_score_color(value)
        bg_color = self._get_bg_color(rating)
        
        # Truncate long names for uniformity
        display_name = kt_name[:30] + '...' if len(kt_name) > 30 else kt_name
        
        st.markdown(f"""
        <div style="
            background: white;
            border: 2px solid {color};
            border-radius: 12px;
            padding: 20px;
            margin: 5px 0;
            height: 150px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.08);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
                background: {color};
            "></div>
            <h4 style="
                margin: 10px 0 15px 0;
                color: #333;
                font-size: 16px;
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            " title="{kt_name}">{display_name}</h4>
            <h2 style="
                color: {color};
                margin: 10px 0;
                font-size: 36px;
                font-weight: bold;
            ">{value:.1f}%</h2>
            <span style="
                display: inline-block;
                padding: 4px 12px;
                background: {bg_color};
                color: {color};
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
            ">{rating}</span>
        </div>
        """, unsafe_allow_html=True)

    def _render_professional_recommendations(self, assessment: Dict):
        """Render recommendations with professional styling"""
        st.markdown("### Strategic Recommendations")
        
        # Categorize KTs by performance
        kt_results = assessment.get('kt_results', {})
        critical = []  # <50%
        needs_attention = []  # 50-70%
        monitor = []  # 70-85%
        performing = []  # >85%
        
        for kt_name, kt_result in kt_results.items():
            value = kt_result.get('value', 0)
            if value < 50:
                critical.append((kt_name, value))
            elif value < 70:
                needs_attention.append((kt_name, value))
            elif value < 85:
                monitor.append((kt_name, value))
            else:
                performing.append((kt_name, value))
        
        # Display recommendations by priority
        if critical:
            st.markdown("""
            <div style="
                background: #ffebee;
                border-left: 4px solid #dc3545;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            ">
                <h4 style="color: #dc3545; margin: 0 0 10px 0;">Critical Priority - Immediate Action Required</h4>
            """, unsafe_allow_html=True)
            
            for kt_name, value in sorted(critical, key=lambda x: x[1]):
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <strong>{kt_name}</strong> 
                    <span style="color: #dc3545;">({value:.1f}%)</span>
                    <br>
                    <span style="color: #666; font-size: 14px;">
                        Requires comprehensive review and immediate intervention plan
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if needs_attention:
            st.markdown("""
            <div style="
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            ">
                <h4 style="color: #856404; margin: 0 0 10px 0;">High Priority - Action Plan Required</h4>
            """, unsafe_allow_html=True)
            
            for kt_name, value in sorted(needs_attention, key=lambda x: x[1]):
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <strong>{kt_name}</strong>
                    <span style="color: #856404;">({value:.1f}%)</span>
                    <br>
                    <span style="color: #666; font-size: 14px;">
                        Develop improvement strategy within 30 days
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if monitor:
            st.markdown("""
            <div style="
                background: #e3f2fd;
                border-left: 4px solid #2196f3;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            ">
                <h4 style="color: #1565c0; margin: 0 0 10px 0;">Monitor & Enhance</h4>
            """, unsafe_allow_html=True)
            
            for kt_name, value in sorted(monitor, key=lambda x: x[1], reverse=True):
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <strong>{kt_name}</strong>
                    <span style="color: #1565c0;">({value:.1f}%)</span>
                    <br>
                    <span style="color: #666; font-size: 14px;">
                        Continue monitoring with periodic reviews
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if performing:
            st.markdown("""
            <div style="
                background: #e8f5e9;
                border-left: 4px solid #28a745;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            ">
                <h4 style="color: #2e7d32; margin: 0 0 10px 0;">Performing Well</h4>
            """, unsafe_allow_html=True)
            
            for kt_name, value in sorted(performing, key=lambda x: x[1], reverse=True):
                st.markdown(f"""
                <div style="margin: 10px 0;">
                    <strong>{kt_name}</strong>
                    <span style="color: #2e7d32;">({value:.1f}%)</span>
                    <br>
                    <span style="color: #666; font-size: 14px;">
                        Maintain current practices and share best practices
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    def _get_score_color(self, value: float) -> str:
        """Get color based on score value"""
        if value >= 85:
            return "#28a745"
        elif value >= 70:
            return "#ffc107"
        else:
            return "#dc3545"
        
    def _get_bg_color(self, rating: str) -> str:
        """Get background color for rating"""
        colors = {
            'Good': "#d4edda",
            'Satisfactory': "#fff3cd",
            'Needs Improvement': "#f8d7da",
            'N/A': "#e2e3e5"
        }
        return colors.get(rating, "#e2e3e5")
    
    def _get_status_badge(self, rating: str) -> str:
        """Get HTML status badge"""
        colors = {
            'Good': "#28a745",
            'Satisfactory': "#ffc107",
            'Needs Improvement': "#dc3545"
        }
        color = colors.get(rating, "#6c757d")
        return f'<span style="color: {color};">●</span> {rating}'
    
    def _render_kt_card(self, kt_name: str, kt_result: Dict):
        """Render a professional KT card"""
        rating = kt_result.get('rating', 'N/A')
        value = kt_result.get('value', 0)
        
        # Color scheme
        if rating == "Good":
            color = "#28a745"
            bg_color = "#d4edda"
        elif rating == "Satisfactory":
            color = "#ffc107"
            bg_color = "#fff3cd"
        else:
            color = "#dc3545"
            bg_color = "#f8d7da"
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {bg_color}55 0%, {bg_color}22 100%);
            border: 2px solid {color};
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: all 0.3s;
        ">
            <h4 style="margin: 0; color: #333;">{kt_name}</h4>
            <h2 style="color: {color}; margin: 10px 0;">{value:.1f}%</h2>
            <p style="margin: 0; color: #666; font-weight: 500;">{rating}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _generate_recommendations(self, assessment: Dict):
        """Generate intelligent recommendations based on results"""
        
        # Find areas needing improvement
        needs_improvement = []
        satisfactory = []
        
        for kt_name, kt_result in assessment.get('kt_results', {}).items():
            if kt_result.get('rating') == 'Needs Improvement':
                needs_improvement.append((kt_name, kt_result.get('value', 0)))
            elif kt_result.get('rating') == 'Satisfactory':
                satisfactory.append((kt_name, kt_result.get('value', 0)))
        
        if needs_improvement:
            st.warning("**Priority Areas for Improvement:**")
            for kt_name, value in sorted(needs_improvement, key=lambda x: x[1]):
                st.markdown(f"• **{kt_name}** ({value:.1f}%) - Requires immediate attention")
        
        if satisfactory:
            st.info("**Areas for Enhancement:**")
            for kt_name, value in sorted(satisfactory, key=lambda x: x[1]):
                st.markdown(f"• **{kt_name}** ({value:.1f}%) - Can be improved to achieve excellence")
        
        if not needs_improvement and not satisfactory:
            st.success("**Excellent Performance!** All key topics are performing at optimal levels.")
    
    def _calculate_pillar(self, pillar: str):
        """Calculate scores for a specific pillar"""
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        with st.spinner(f"Calculating {pillar}..."):
            # Find all ACs for this pillar
            pillar_acs = []
            
            for ac_name, ac_data in self.database.get('assessment_criteria', {}).items():
                # Check if AC belongs to this pillar through its DPs
                for dp_name in ac_data.get('data_points', []):
                    dp_data = self.database.get('data_points', {}).get(dp_name, {})
                    dp_pillar = self._expand_pillar_name(dp_data.get('pillar', ''))
                    if dp_pillar == pillar:
                        pillar_acs.append((ac_name, ac_data))
                        break

            # Calculate each AC
            for ac_name, ac_data in pillar_acs:
                formula = ac_data.get('formula', '')
                data_points = ac_data.get('data_points', [])
                thresholds = ac_data.get('thresholds', {
                    'good': '>90',
                    'satisfactory': '70-90',
                    'needs_improvement': '<70'
                })
                
                # Get all DP values
                dp_values = assessment.get('dp_values', {})
                
                # Call with ALL required parameters
                value, rating = self._calculate_ac(
                    ac_name=ac_name,
                    formula=formula,
                    data_points_list=data_points,
                    dp_values=dp_values,
                    thresholds=thresholds
                )
                
                # Store the result
                assessment['ac_results'][ac_name] = {
                    'value': value,
                    'rating': rating,
                    'formula': formula,
                    'timestamp': datetime.now().isoformat()
                }
            
        st.success(f"Calculated {len(pillar_acs)} assessment criteria for {pillar}")

        # Aggregate results
        self._aggregate_results(assessment)

        # Add to history
        assessment['calculation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'action': f'Calculated {pillar}',
            'ac_count': len(pillar_acs)
        })

        st.success(f"Calculated {len(pillar_acs)} assessment criteria for {pillar}")
        st.rerun()  # Add this to refresh the display
    
    def _calculate_ac(self, ac_name: str, formula: str, data_points_list: list, 
                  dp_values: dict, thresholds: dict) -> tuple:
        """Calculate AC score using smart formula calculator"""
        
        # Import the smart calculator
        from smart_formula_calculator_final import SmartFormulaCalculator
        
        # Create calculator instance if not exists
        if not hasattr(self, 'smart_calculator'):
            self.smart_calculator = SmartFormulaCalculator()
        
        # Get AC data from database
        ac_data = self.database.get('assessment_criteria', {}).get(ac_name, {})
        if not ac_data:
            ac_data = {
                'formula': formula,
                'data_points': data_points_list,
                'thresholds': thresholds,
                'formula_type': 'quantitative' if any(op in formula for op in ['+', '-', '*', '/']) else 'qualitative'
            }
        
        # Use smart calculator
        return self.smart_calculator.calculate_ac(ac_name, ac_data, dp_values)

    def _get_rating(self, value: float, ac_name: str = None) -> str:
        """Get rating based on value and AC-specific thresholds"""
        if ac_name:
            # Use the parser's rating method which checks AC-specific thresholds
            return self.parser.get_rating_for_ac(ac_name, value)
        
        # Default fallback
        if value >= 85:
            return 'Good'
        elif value >= 70:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'
    
    def _calculate_all(self):
        """Calculate all assessments with progress tracking"""
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Calculate all ACs
        ac_count = 0
        total_acs = len(self.database.get('assessment_criteria', {}))
        
        for ac_name, ac_data in self.database.get('assessment_criteria', {}).items():
            formula = ac_data.get('formula', '')
            data_points = ac_data.get('data_points', [])
            thresholds = ac_data.get('thresholds', {
                'good': '>90',
                'satisfactory': '70-90',
                'needs_improvement': '<70'
            })
            
            # Get all DP values
            dp_values = assessment.get('dp_values', {})
            
            # Call with ALL required parameters
            value, rating = self._calculate_ac(
                ac_name=ac_name,
                formula=formula,
                data_points_list=data_points,
                dp_values=dp_values,
                thresholds=thresholds
            )
            
            # Store the result
            assessment['ac_results'][ac_name] = {
                'value': value,
                'rating': rating,
                'formula': formula,
                'timestamp': datetime.now().isoformat()
            }
            
            ac_count += 1
        
        # Update progress
        progress = ac_count / total_acs
        progress_bar.progress(progress)
        status_text.text(f"Processing: {ac_count}/{total_acs} Assessment Criteria")

        # Aggregate results
        status_text.text("Aggregating results...")
        self._aggregate_results(assessment)

        # Complete
        progress_bar.progress(1.0)
        status_text.empty()

        # Add to history
        assessment['calculation_history'].append({
            'timestamp': datetime.now().isoformat(),
            'action': 'Complete assessment calculation',
            'ac_count': ac_count
        })

        st.success(f"Successfully calculated {ac_count} assessment criteria")
        st.rerun()
    
    def _aggregate_results(self, assessment: dict):
        """Aggregate AC results to PS and KT levels"""
        
        # Aggregate AC → PS level
        for ps_name, ps_data in self.database.get('performance_signals', {}).items():
            # Get all AC results that belong to this PS
            ps_ac_results = {}
            
            # Find ACs for this PS
            ac_list = ps_data.get('assessment_criteria', [])
            for ac_name in ac_list:
                if ac_name in assessment.get('ac_results', {}):
                    ps_ac_results[ac_name] = assessment['ac_results'][ac_name]
            
            if ps_ac_results:
                # Use the aggregator properly
                ps_result = self.aggregator.aggregate_to_ps(
                    ps_data,  # PS data
                    ps_ac_results,  # AC results for this PS
                    self.database.get('assessment_criteria', {})  # All ACs for weight info
                )
                assessment['ps_results'][ps_name] = ps_result
        
        # Aggregate PS → KT level
        for kt_name, kt_data in self.database.get('key_topics', {}).items():
            # Get all PS results that belong to this KT
            kt_ps_results = {}
            
            # Find PSs for this KT
            ps_list = kt_data.get('performance_signals', [])
            for ps_name in ps_list:
                if ps_name in assessment.get('ps_results', {}):
                    kt_ps_results[ps_name] = assessment['ps_results'][ps_name]
            
            if kt_ps_results:
                # Use the aggregator properly
                kt_result = self.aggregator.aggregate_to_kt(
                    kt_data,  # KT data
                    kt_ps_results,  # PS results for this KT
                    self.database.get('performance_signals', {})  # All PSs for weight info
                )
                assessment['kt_results'][kt_name] = kt_result
        
        # Calculate overall score
        if assessment.get('kt_results'):
            overall_value = self.aggregator.calculate_overall(assessment['kt_results'])
            assessment['overall_score'] = {
                'value': overall_value,
                'rating': self.aggregator._get_rating(overall_value)
            }
    
    def _format_ac_value(self, ac_result: Dict) -> str:
        """Format AC value based on type"""
        value = ac_result.get('value', 0)
        
        if ac_result.get('is_qualitative'):
            return f"{value:.0f}% (Qual)"
        elif ac_result.get('is_ratio'):
            return f"{value:.2f}"
        elif ac_result.get('is_percentage'):
            return f"{value:.1f}%"
        else:
            return f"{value:.2f}"
        
    def _find_ac_for_dp(self, dp_name: str) -> Dict:
        """Find the AC that uses this DP"""
        for ac_name, ac_data in self.database.get('assessment_criteria', {}).items():
            if dp_name in ac_data.get('data_points', []):
                return ac_data
        return None
    
    def test_specific_ac(self, ac_name: str):
        """Test a specific AC calculation for debugging"""
        assessment = st.session_state['assessments'][st.session_state['current_assessment']]
        
        # Find the AC
        ac_data = self.database.get('assessment_criteria', {}).get(ac_name)
        if not ac_data:
            st.error(f"AC '{ac_name}' not found")
            return
        
        st.write(f"Testing AC: {ac_name}")
        st.write(f"Formula: {ac_data.get('formula')}")
        
        # Get DP values
        dp_values = {}
        for dp_name in ac_data.get('data_points', []):
            if dp_name in assessment['dp_values']:
                dp_values[dp_name] = assessment['dp_values'][dp_name]
        
        st.write(f"Available DPs: {list(dp_values.keys())}")
        
        # Test evaluation
        result = self.parser.evaluate(ac_data.get('formula'), dp_values, ac_name)
        st.write(f"Result: {result}")

# Debug function
def debug_specific_ac():
    """Debug a specific AC to see what's happening"""
    import json
    
    # Load database
    with open('data/meinhardt_db.json', 'r') as f:
        database = json.load(f)
    
    # Pick a simple AC to debug
    ac_name = "DevCo Schedule Performance Index (SPI)"
    ac_data = database['assessment_criteria'].get(ac_name)
    
    print(f"\n{'='*60}")
    print(f"DEBUGGING: {ac_name}")
    print(f"{'='*60}")
    print(f"Formula: {ac_data.get('formula')}")
    print(f"Required DPs: {ac_data.get('data_points', [])}")
    
    # Check if we have test data
    if 'assessments' in database:
        for assessment in database['assessments'].values():
            if 'dp_values' in assessment:
                print("\nFound DP values in assessment:")
                for dp in ac_data.get('data_points', []):
                    value = assessment['dp_values'].get(dp, 'NOT FOUND')
                    print(f"  - {dp}: {value}")
                break
    
    # Now test the calculation
    from diagnostic_formula_parser import DiagnosticFormulaParser
    parser = DiagnosticFormulaParser()
    
    # Create test values
    test_dps = {}
    for dp in ac_data.get('data_points', []):
        if 'Earned Value' in dp:
            test_dps[dp] = 1000000
        elif 'Planned Value' in dp:
            test_dps[dp] = 2000000
    
    print(f"\nTest calculation with mock values:")
    print(f"Test DPs: {test_dps}")
    
    value, rating, debug = parser.parse_and_calculate(
        ac_name,
        ac_data.get('formula'),
        test_dps,
        debug=True
    )
    
    print(f"Result: {value:.2f}% ({rating})")

# Entry point
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'debug':
        debug_specific_ac()
    else:
        st.set_page_config(
            page_title="Meinhardt Assessment Guide",
            page_icon="",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        module = MainAGEnhanced()
        module.render()