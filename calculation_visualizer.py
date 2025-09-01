"""
Professional Calculation Visualizer for Meinhardt WebApp
Industrial-grade visualization with proper DP filtering
"""

import streamlit as st
from typing import Dict, Any, List, Tuple
import pandas as pd


class CalculationVisualizer:
    """Professional calculation hierarchy visualization"""
    
    def __init__(self):
        # Import parser for extracting relevant variables
        from formula_parser_complete import FormulaParser
        self.parser = FormulaParser()
    
    def render_calculation_tree(self, assessment: Dict, database: Dict):
        """Render the complete calculation hierarchy with professional UI"""
        st.subheader("Calculation Hierarchy & Details")
        
        # Overview metrics
        col1, col2, col3 = st.columns(3)
        
        overall_score = assessment.get('overall_score', {})
        with col1:
            self._render_metric_box(
                "Overall Score",
                f"{overall_score.get('value', 0):.1f}%",
                overall_score.get('rating', 'N/A'),
                self._get_rating_color(overall_score.get('rating', 'N/A'))
            )
        
        with col2:
            kt_count = len(assessment.get('kt_results', {}))
            st.metric("Total Key Topics", kt_count)
        
        with col3:
            ac_count = len(assessment.get('ac_results', {}))
            st.metric("Calculations Performed", ac_count)
        
        st.markdown("---")
        
        # Interactive calculation tree
        st.subheader("Interactive Calculation Tree")
        st.info("Click on any item to see detailed calculations and formulas")
        
        # Render KT hierarchy
        for kt_name, kt_result in assessment.get('kt_results', {}).items():
            self._render_kt_node(kt_name, kt_result, assessment, database)
    
    def _render_metric_box(self, title: str, value: str, rating: str, color: str):
        """Render a professional metric box"""
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {color}15 0%, {color}08 100%);
            border: 2px solid {color};
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        ">
            <h4 style="margin: 0; color: #333;">{title}</h4>
            <h2 style="margin: 10px 0; color: {color};">{value}</h2>
            <p style="margin: 0; color: #666; font-weight: 500;">{rating}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_kt_node(self, kt_name: str, kt_result: Dict, assessment: Dict, database: Dict):
        """Render a Key Topic node with drill-down"""
        rating = kt_result.get('rating', 'N/A')
        value = kt_result.get('value', 0)
        color = self._get_rating_color(rating)
        
        with st.expander(f"{kt_name} - {value:.1f}% ({rating})", expanded=False):
            # Show KT calculation details
            st.markdown("### Key Topic Calculation")
            
            # Formula explanation
            st.markdown("**Calculation Formula:** KT Score = Σ(PS Value × PS Weight) / Σ(PS Weight)")
            
            # Get PS details for this KT
            kt_data = database.get('key_topics', {}).get(kt_name, {})
            ps_list = kt_data.get('performance_signals', [])
            
            if ps_list:
                # Create PS table
                ps_data = []
                for ps_name in ps_list:
                    if ps_name in assessment.get('ps_results', {}):
                        ps_result = assessment['ps_results'][ps_name]
                        ps_info = database.get('performance_signals', {}).get(ps_name, {})
                        ps_data.append({
                            'Performance Signal': ps_name,
                            'Value': f"{ps_result.get('value', 0):.2f}%",
                            'Weight': f"{ps_info.get('weight', 0):.1f}%",
                            'Contribution': f"{ps_result.get('value', 0) * ps_info.get('weight', 0) / 100:.2f}",
                            'Rating': ps_result.get('rating', 'N/A')
                        })
                
                if ps_data:
                    df = pd.DataFrame(ps_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Show calculation steps
                    st.markdown("**Calculation Steps:**")
                    total_weighted = sum(float(d['Contribution']) for d in ps_data)
                    total_weight = sum(float(d['Weight'].rstrip('%')) for d in ps_data)
                    
                    steps = [
                        f"1. Weighted Sum = {' + '.join([d['Contribution'] for d in ps_data])}",
                        f"2. Weighted Sum = {total_weighted:.2f}",
                        f"3. Total Weight = {total_weight:.1f}%",
                        f"4. Final Score = {total_weighted:.2f} / {total_weight/100:.2f} = {value:.1f}%"
                    ]
                    
                    for step in steps:
                        st.markdown(f"   {step}")
            
            # Show PS breakdowns
            st.markdown("---")
            st.markdown("### Performance Signals Breakdown")
            
            for ps_name in ps_list:
                if ps_name in assessment.get('ps_results', {}):
                    self._render_ps_details(ps_name, assessment, database)
    
    def _render_ps_details(self, ps_name: str, assessment: Dict, database: Dict):
        """Render Performance Signal details"""
        ps_result = assessment['ps_results'][ps_name]
        ps_data = database.get('performance_signals', {}).get(ps_name, {})
        
        with st.container():
            st.markdown(f"#### {ps_name}")
            st.markdown(f"**Score:** {ps_result.get('value', 0):.1f}% | **Rating:** {ps_result.get('rating', 'N/A')}")
            
            # Get AC details
            ac_list = ps_data.get('assessment_criteria', [])
            if ac_list:
                ac_table = []
                for ac_name in ac_list:
                    if ac_name in assessment.get('ac_results', {}):
                        ac_result = assessment['ac_results'][ac_name]
                        ac_info = database.get('assessment_criteria', {}).get(ac_name, {})
                        ac_table.append({
                            'Assessment Criteria': ac_name,
                            'Value': self._format_ac_value(ac_result),
                            'Weight': f"{ac_info.get('weight', 0):.1f}%",
                            'Status': ac_result.get('status', 'N/A'),
                            'Rating': ac_result.get('rating', 'N/A')
                        })
                
                if ac_table:
                    df = pd.DataFrame(ac_table)
                    st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Show AC formula details checkbox
            if st.checkbox(f"Show AC Formula Details for {ps_name}", key=f"details_{ps_name}"):
                self._render_ac_formulas(ac_list, assessment, database)
    
    def _render_ac_formulas(self, ac_list: List[str], assessment: Dict, database: Dict):
        """Render AC formula details with only relevant DPs"""
        for ac_name in ac_list:
            if ac_name in assessment.get('ac_results', {}):
                ac_result = assessment['ac_results'][ac_name]
                ac_data = database.get('assessment_criteria', {}).get(ac_name, {})
                
                with st.container():
                    st.markdown(f"**{ac_name}**")
                    
                    formula = ac_data.get('formula', '')
                    if formula:
                        # Display formula in code block for clarity
                        st.code(formula, language='text')
                    
                    # Get ONLY the relevant DPs for this formula
                    st.markdown("*Data Points Used:*")
                    
                    # Use parser to extract relevant variables
                    all_dp_values = assessment.get('dp_values', {})
                    relevant_dps = self.parser.extract_variables_for_formula(formula, all_dp_values)
                    
                    if relevant_dps:
                        for dp_name in relevant_dps:
                            if dp_name in all_dp_values:
                                value = all_dp_values[dp_name]
                                # Format value display
                                if isinstance(value, (int, float)):
                                    st.markdown(f"• **{dp_name}** = {value:,.2f}")
                                else:
                                    st.markdown(f"• **{dp_name}** = {value}")
                    else:
                        st.markdown("• *No matching data points found*")
                    
                    # Show result with proper formatting
                    result_value = ac_result.get('value', 0)
                    if ac_result.get('is_qualitative'):
                        qual_result = ac_result.get('qualitative_result', 'N/A')
                        st.success(f"**Result:** {qual_result} → {result_value:.0f}% score")
                    elif ac_result.get('is_ratio'):
                        st.success(f"**Result:** {result_value:.4f} (ratio)")
                    else:
                        st.success(f"**Result:** {result_value:.2f}%")
                    
                    # Show rating thresholds if available
                    thresholds = ac_data.get('thresholds', {})
                    if thresholds:
                        st.markdown("*Rating Thresholds:*")
                        good = thresholds.get('good', '>85')
                        sat = thresholds.get('satisfactory', '70-85')
                        needs = thresholds.get('needs_improvement', '<70')
                        
                        cols = st.columns(3)
                        with cols[0]:
                            st.markdown(f"**Good:** {good}")
                        with cols[1]:
                            st.markdown(f"**Satisfactory:** {sat}")
                        with cols[2]:
                            st.markdown(f"**Needs Improvement:** {needs}")
                    
                    st.markdown("---")
    
    def _format_ac_value(self, ac_result: Dict) -> str:
        """Format AC value based on type"""
        value = ac_result.get('value', 0)
        
        if ac_result.get('is_qualitative'):
            qual_result = ac_result.get('qualitative_result', 'N/A')
            return f"{value:.0f}% ({qual_result})"
        elif ac_result.get('is_ratio'):
            return f"{value:.4f}"
        elif ac_result.get('is_percentage'):
            return f"{value:.1f}%"
        else:
            return f"{value:.2f}"
    
    def _get_rating_color(self, rating: str) -> str:
        """Get color for rating"""
        colors = {
            'Good': '#28a745',
            'Satisfactory': '#ffc107',
            'Needs Improvement': '#dc3545',
            'N/A': '#6c757d'
        }
        return colors.get(rating, '#6c757d')


class QualitativeFormulaHandler:
    """Handle qualitative formula evaluation and display"""
    
    def evaluate_qualitative(self, formula: str, dp_values: Dict[str, Any]) -> Tuple[str, float]:
        """Evaluate qualitative formula and return result and score"""
        if dp_values:
            value = list(dp_values.values())[0]
            
            if isinstance(value, str):
                value_lower = value.lower()
                if value_lower in ['yes', 'completed', 'applied', 'true']:
                    return 'Yes', 100
                elif value_lower in ['no', 'not completed', 'not applied', 'false']:
                    return 'No', 0
                elif value_lower in ['partial', 'partially', 'in progress']:
                    return 'Partially Applied', 50
                else:
                    return value, 50
        
        return 'N/A', 0
    
    def format_qualitative_display(self, formula: str, result: str, score: float) -> str:
        """Format qualitative result for display"""
        return f"{result} ({score:.0f}%)"