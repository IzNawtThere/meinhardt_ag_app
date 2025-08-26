# main_ag_module.py

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import re
from typing import Dict, Any, Optional, List, Self, Tuple
import ast
import operator
from difflib import SequenceMatcher
import numpy as np

class FormulaEngine:
    """Intelligent formula parser and evaluator"""
    
    def __init__(self, database):
        self.db = database
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow
        }
        
    def evaluate(self, formula: str, dp_values: Dict[str, Any], formula_type: str) -> Tuple[Any, str]:
        """
        Evaluate formula and return (value, status)
        Status can be: 'calculated', 'incomplete', 'error'
        """
        if not formula:
            return None, 'error'
            
        if formula_type == 'qualitative':
            return self._evaluate_qualitative(formula, dp_values)
        else:
            return self._evaluate_quantitative(formula, dp_values)
    
    def _evaluate_quantitative(self, formula: str, dp_values: Dict[str, Any]) -> Tuple[Any, str]:
        """Evaluate mathematical formulas with intelligent DP matching"""
        
        # First, find all DP references in the formula
        dp_references = self._extract_dp_references(formula)
        
        if not dp_references:
            return None, 'error'
        
        # Create a working formula by replacing text with values
        working_formula = formula
        
        # Sort by length (longest first) to avoid partial replacements
        sorted_refs = sorted(dp_references, key=len, reverse=True)
        
        for dp_name in sorted_refs:
            if dp_name in dp_values:
                value = dp_values[dp_name]
                if value is not None:
                    # Find the part of formula that matches this DP
                    dp_core = dp_name.lower().replace(' (no.)', '').replace(' (%)', '')
                    formula_lower = working_formula.lower()
                    
                    # Try to find and replace the matching portion
                    import re
                    # Create pattern from DP words
                    words = [w for w in dp_core.split() if len(w) > 2]
                    if words:
                        # Build a flexible pattern
                        pattern = r'\b' + r'.*?'.join(re.escape(w) for w in words) + r'[^/]*?'
                        matches = re.finditer(pattern, formula_lower)
                        for match in matches:
                            start, end = match.span()
                            # Replace with value
                            working_formula = working_formula[:start] + str(value) + working_formula[end:]
                            break
        
        # Now try to evaluate if we have a mathematical expression
        try:
            # Clean up the formula
            working_formula = re.sub(r'[a-zA-Z]+', '', working_formula)  # Remove remaining text
            working_formula = working_formula.replace('/', '/').replace('*', '*')
            
            if '/' in working_formula or '*' in working_formula or '+' in working_formula or '-' in working_formula:
                result = eval(working_formula)
                if isinstance(result, (int, float)):
                    return round(result, 4), 'calculated'
        except:
            pass
        
        return None, 'error'
    
    def _evaluate_qualitative(self, formula: str, dp_values: Dict[str, Any]) -> Tuple[Any, str]:
        """Evaluate text-based formulas"""
        
        # Simple pattern matching for now
        formula_lower = formula.lower()
        
        # Extract the main DP being evaluated
        dp_references = self._extract_dp_references(formula)
        
        if not dp_references:
            # If no specific DP reference, try to match the formula itself
            if 'yes' in formula_lower and 'no' in formula_lower:
                # It's a conditional formula
                return self._evaluate_conditional(formula, dp_values)
            return None, 'error'
        
        # Get the value of the referenced DP
        main_ref = dp_references[0]
        value, _ = self._fuzzy_match_dp(main_ref, dp_values)
        
        if value is None:
            return None, 'incomplete'
        
        # Apply qualitative logic
        if 'yes' in formula_lower and 'no' in formula_lower:
            # Binary evaluation
            if str(value).lower() in ['yes', 'true', '1', 'completed', 'done']:
                return 'Yes', 'calculated'
            elif str(value).lower() in ['no', 'false', '0', 'not completed', 'pending']:
                return 'No', 'calculated'
            else:
                return 'Partially Applied', 'calculated'
        
        # Default: return the value as-is
        return value, 'calculated'
    
    def _extract_dp_references(self, formula: str) -> List[str]:
        """Extract all DP references from a formula using intelligent matching"""
        references = []
        formula_lower = formula.lower()
        
        # Get all data points from database
        data = self.db.load_database()
        if 'data_points' in data:
            for dp_name, dp_data in data['data_points'].items():
                dp_name_lower = dp_name.lower()
                
                # Strip common suffixes
                dp_core = dp_name_lower.replace(' (no.)', '').replace(' (%)', '').strip()
                
                # Split into meaningful words (ignore small words)
                dp_words = [w for w in dp_core.split() if len(w) > 2]
                formula_words = [w for w in formula_lower.split() if len(w) > 2]
                
                # Count matching words
                if dp_words:
                    matches = sum(1 for word in dp_words if any(word in fw or fw in word for fw in formula_words))
                    match_ratio = matches / len(dp_words)
                    
                    # If 50% or more words match, consider it a reference
                    if match_ratio >= 0.5:
                        references.append(dp_name)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_refs = []
        for ref in references:
            if ref not in seen:
                seen.add(ref)
                unique_refs.append(ref)
        
        return unique_refs
    
    def _fuzzy_match_dp(self, reference: str, dp_values: Dict[str, Any]) -> Tuple[Any, str]:
        """
        Fuzzy match a DP reference to actual DP names
        Returns (value, matched_dp_name) or (None, None) if not found
        """
        reference_lower = reference.lower().strip()
        
        # First try exact match
        for dp_name, value in dp_values.items():
            if dp_name.lower() == reference_lower:
                return value, dp_name
        
        # Try substring matching
        for dp_name, value in dp_values.items():
            if reference_lower in dp_name.lower() or dp_name.lower() in reference_lower:
                return value, dp_name
        
        # Try fuzzy matching with similarity threshold
        best_match = None
        best_ratio = 0
        threshold = 0.8  # 80% similarity required
        
        for dp_name, value in dp_values.items():
            ratio = SequenceMatcher(None, reference_lower, dp_name.lower()).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = (value, dp_name)
        
        if best_match:
            return best_match
        
        # Try matching by abbreviations (e.g., "EV" matches "Earned Value")
        for dp_name, value in dp_values.items():
            # Create abbreviation from dp_name
            abbrev = ''.join(word[0] for word in dp_name.split() if word[0].isupper())
            if abbrev.lower() == reference_lower:
                return value, dp_name
        
        return None, None
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression using AST"""
        try:
            # Clean the expression
            expression = expression.strip()
            
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate the AST
            return self._eval_node(tree.body)
            
        except:
            raise ValueError(f"Cannot evaluate expression: {expression}")
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # For older Python versions
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
        else:
            raise ValueError(f"Unsupported node type: {type(node)}")
    
    def _evaluate_conditional(self, formula: str, dp_values: Dict[str, Any]) -> Tuple[Any, str]:
        """Evaluate conditional formulas (IF-THEN-ELSE style)"""
        # Simple implementation for now
        # Can be enhanced with more complex logic
        
        # Check if any DP has a value
        if any(dp_values.values()):
            return 'Yes', 'calculated'
        else:
            return 'No', 'calculated'


class MainAGModule:
    """Main Assessment Guide Module for data input and calculation"""
    
    def __init__(self):
        from database.json_db import JsonDatabase
        self.db = JsonDatabase()
        self.formula_engine = FormulaEngine(self.db)
        
        # Initialize session state
        if 'current_assessment' not in st.session_state:
            st.session_state.current_assessment = None
        if 'dp_values' not in st.session_state:
            st.session_state.dp_values = {}
        if 'calculation_results' not in st.session_state:
            st.session_state.calculation_results = {}
        if 'auto_calculate' not in st.session_state:
            st.session_state.auto_calculate = False

    def diagnose_hierarchy_issue(self):
        """Diagnose what's actually wrong with the hierarchy"""
        data = self.db.load_database()
        st.write("### DIAGNOSTIC REPORT ###")
        
        # Check Key Topics
        st.write("\n**KEY TOPICS:**")
        for kt_name, kt in list(data.get('key_topics', {}).items())[:3]:
            st.write(f"- {kt_name}: pillar = {kt.get('pillar', 'MISSING')}")
        
        # Check Performance Signals
        st.write("\n**PERFORMANCE SIGNALS:**")
        for ps_name, ps in list(data.get('performance_signals', {}).items())[:3]:
            st.write(f"- {ps_name}: key_topic = {ps.get('key_topic', 'MISSING')}")
        
        # Check Assessment Criteria
        st.write("\n**ASSESSMENT CRITERIA:**")
        for ac_name, ac in list(data.get('assessment_criteria', {}).items())[:3]:
            st.write(f"- {ac_name}: performance_signal = {ac.get('performance_signal', 'MISSING')}")
        
        # Check the full chain for one example
        st.write("\n**TRACING ONE COMPLETE CHAIN:**")
        first_dp = list(data.get('data_points', {}).items())[0]
        st.write(f"DP: {first_dp[0]} → pillar: {first_dp[1].get('pillar')}")
        
        # Find an AC that might use this DP
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            if first_dp[0].lower() in ac.get('formula', '').lower():
                st.write(f"AC: {ac_name} → PS: {ac.get('performance_signal')}")
                ps_name = ac.get('performance_signal')
                if ps_name:
                    ps = data.get('performance_signals', {}).get(ps_name, {})
                    st.write(f"PS: {ps_name} → KT: {ps.get('key_topic')}")
                    kt_name = ps.get('key_topic')
                    if kt_name:
                        kt = data.get('key_topics', {}).get(kt_name, {})
                        st.write(f"KT: {kt_name} → pillar: {kt.get('pillar', 'MISSING!')}")
                break
    
    def render(self):
        """Main render function"""
        st.title("Main AG - Assessment Input & Calculation")
        
        # Top section: Assessment management
        self._render_assessment_selector()
        
        if st.session_state.current_assessment:
            # Calculation mode selector
            self._render_calculation_mode()
            
            # Get actual pillars from database
            data = self.db.load_database()
            actual_pillars = []
            pillar_set = set()
            
            for dp in data.get('data_points', {}).values():
                pillar = dp.get('pillar')
                if pillar and pillar not in pillar_set:
                    pillar_set.add(pillar)
                    actual_pillars.append(pillar)
            
            actual_pillars.sort()  # Sort alphabetically
            
            # Create tabs with actual pillar names
            tab_names = actual_pillars + ["Summary", "Reports"]
            tabs = st.tabs(tab_names)
            
            # Render each pillar tab
            for i, pillar in enumerate(actual_pillars):
                with tabs[i]:
                    self._render_pillar_tab(pillar)
            
            # Summary tab
            with tabs[len(actual_pillars)]:
                self._render_summary_tab()
            
            # Reports tab
            with tabs[len(actual_pillars) + 1]:
                self._render_reports_tab()
    
    def _render_assessment_selector(self):
        """Render assessment selection and management"""
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            # Get existing assessments
            data = self.db.load_database()
            assessments = data.get('assessments', {})
            
            if assessments:
                assessment_names = list(assessments.keys())
                
                # Maintain selection
                if st.session_state.current_assessment in assessment_names:
                    current_index = assessment_names.index(st.session_state.current_assessment)
                else:
                    current_index = 0
                    
                selected = st.selectbox(
                    "Select Assessment",
                    ['New Assessment...'] + assessment_names,
                    index=current_index + 1 if st.session_state.current_assessment else 0
                )
                
                if selected != 'New Assessment...' and selected != st.session_state.current_assessment:
                    st.session_state.current_assessment = selected
                    self._load_assessment(selected)
            else:
                st.info("No assessments found. Create a new one to begin.")
        
        with col2:
            project_name = st.text_input("Project Name", key="project_name")
        
        with col3:
            if st.button("Save Assessment", type="secondary"):
                if st.session_state.current_assessment:
                    self._save_assessment()
                    st.success("Assessment saved!")
        
        with col4:
            if st.button("New Assessment", type="primary"):
                if project_name:
                    self._create_new_assessment(project_name)
                else:
                    st.error("Please enter a project name")
    
    def _render_calculation_mode(self):
        """Render calculation mode selector"""
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 3])
        
        with col1:
            st.session_state.auto_calculate = st.checkbox(
                "Auto-Calculate",
                value=st.session_state.auto_calculate,
                help="Automatically calculate scores as you enter values"
            )
        
        with col2:
            if st.button("Calculate All", type="primary", disabled=st.session_state.auto_calculate):
                self._calculate_all_scores()
                st.success("All calculations completed!")
        
        with col3:
            # Display calculation status
            if st.session_state.calculation_results:
                complete = sum(1 for r in st.session_state.calculation_results.values() 
                             if r.get('status') == 'calculated')
                total = len(st.session_state.calculation_results)
                st.progress(complete / total if total > 0 else 0)
                st.caption(f"Calculated: {complete}/{total}")
    
    def _render_pillar_tab(self, pillar: str):
        """Render a single pillar tab with DP inputs"""
        data = self.db.load_database()

        # Get DPs for this pillar
        pillar_dps = {
            name: dp for name, dp in data.get('data_points', {}).items()
            if dp.get('pillar') == pillar
        }
        
        if not pillar_dps:
            st.warning(f"No data points found for {pillar}")
            return
        
        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total DPs", len(pillar_dps))
        with col2:
            filled = sum(1 for dp_name in pillar_dps if dp_name in st.session_state.dp_values)
            st.metric("Filled", filled)
        with col3:
            if len(pillar_dps) > 0:
                st.metric("Completion", f"{(filled/len(pillar_dps)*100):.1f}%")
        
        # Add test data button for easy testing
        col4 = st.columns([3, 1])[1]
        with col4:
            self._render_test_data_button(pillar, pillar_dps)

        st.divider()
        
        # Group DPs by Performance Signal for better organization
        ps_groups = {}
        for dp_name, dp in pillar_dps.items():
            ps_name = self._find_dp_performance_signal(dp_name)
            if ps_name is None or ps_name == 'Uncategorized':
                ps_name = 'Direct Input Data Points'  # Better label
            if ps_name not in ps_groups:
                ps_groups[ps_name] = []
            ps_groups[ps_name].append((dp_name, dp))
        
        # Sort groups - put Direct Input last
        sorted_groups = sorted(ps_groups.items(), 
                            key=lambda x: (x[0] == 'Direct Input Data Points', x[0]))
        
        # Render DPs grouped by Performance Signal
        for ps_name, dps in sorted_groups:
            st.subheader(f"📊 {ps_name}")
            
            # Create columns for better layout
            cols = st.columns(2)
            
            for idx, (dp_name, dp) in enumerate(dps):
                with cols[idx % 2]:
                    self._render_dp_input(dp_name, dp)
        
        # Calculate button for this pillar
        if not st.session_state.auto_calculate:
            if st.button(f"Calculate {pillar} Scores", type="primary", key=f"calc_{pillar}"):
                self._calculate_pillar_scores(pillar)
                st.success(f"{pillar} calculations completed!")
    
    def _render_dp_input(self, dp_name: str, dp: dict):
        """Render a single DP input field based on its type"""
        data_type = dp.get('data_type', 'text')
        current_value = st.session_state.dp_values.get(dp_name)
        
        # Create unique key for this input
        input_key = f"dp_input_{dp_name}"
        
        if data_type == 'number':
            value = st.number_input(
                dp_name,
                value=float(current_value) if current_value is not None else 0.0,
                key=input_key,
                format="%.2f"
            )
        elif data_type == 'percentage':
            value = st.slider(
                dp_name,
                min_value=0,
                max_value=100,
                value=int(current_value) if current_value is not None else 0,
                key=input_key,
                format="%d%%"
            )
        elif data_type == 'boolean':
            options = ['Not Set', 'Yes', 'No', 'N/A']
            current_idx = 0
            if current_value in options:
                current_idx = options.index(current_value)
            value = st.selectbox(
                dp_name,
                options,
                index=current_idx,
                key=input_key
            )
            if value == 'Not Set':
                value = None
        elif data_type == 'date':
            value = st.date_input(
                dp_name,
                value=current_value if current_value else None,
                key=input_key
            )
            if value:
                value = value.isoformat()
        else:  # text
            value = st.text_input(
                dp_name,
                value=current_value if current_value else "",
                key=input_key
            )
            if not value:
                value = None
        
        # Update value in session state
        if value is not None and value != current_value:
            st.session_state.dp_values[dp_name] = value
            
            # Auto-calculate if enabled
            if st.session_state.auto_calculate:
                self._calculate_affected_scores(dp_name)

    def _render_test_data_button(self, pillar: str, pillar_dps: dict):
        """Add a button to fill in test data for quick testing"""
        if st.button(f"Fill Test Data for {pillar}", key=f"test_data_{pillar}"):
            import random
            
            for dp_name, dp in pillar_dps.items():
                data_type = dp.get('data_type', 'text')
                
                # Generate appropriate test values
                if data_type == 'number':
                    # Generate reasonable numbers based on DP name
                    if 'value' in dp_name.lower() or 'cost' in dp_name.lower():
                        value = round(random.uniform(1000, 10000), 2)
                    elif 'number' in dp_name.lower() or 'count' in dp_name.lower():
                        value = random.randint(5, 50)
                    else:
                        value = round(random.uniform(50, 100), 2)
                elif data_type == 'percentage':
                    value = random.randint(60, 95)
                elif data_type == 'boolean':
                    value = random.choice(['Yes', 'Yes', 'No'])  # Favor Yes
                elif data_type == 'date':
                    value = '2024-01-15'
                else:  # text
                    value = random.choice(['Completed', 'Done', 'Approved'])
                
                st.session_state.dp_values[dp_name] = value
            
            # Auto-calculate if we just filled data
            self._calculate_pillar_scores(pillar)
            st.success(f"Test data filled and calculated for {pillar}")
            st.rerun()

    def _render_summary_tab(self):
        """Render professional assessment results dashboard"""
        st.subheader("Assessment Results Dashboard")
        
        if not st.session_state.calculation_results:
            st.info("No calculations performed yet. Enter DP values and calculate scores.")
            return
        
        data = self.db.load_database()
        
        # Executive Summary Section
        st.markdown("## Executive Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate overall statistics
        total_calculated = sum(1 for r in st.session_state.calculation_results.values() 
                            if r.get('status') == 'calculated')
        total_items = len(st.session_state.calculation_results)
        
        good_count = sum(1 for r in st.session_state.calculation_results.values() 
                        if r.get('rating') == 'Good')
        needs_improvement = sum(1 for r in st.session_state.calculation_results.values() 
                            if r.get('rating') == 'Needs Improvement')
        
        with col1:
            st.metric("Overall Completion", f"{(total_calculated/total_items*100 if total_items > 0 else 0):.1f}%")
        with col2:
            st.metric("Good Ratings", good_count)
        with col3:
            st.metric("Needs Improvement", needs_improvement)
        with col4:
            overall_score = self._calculate_overall_score()
            st.metric("Overall Score", f"{overall_score:.1f}%")
        
        st.divider()
        
        # Create tabs for different views
        view_tabs = st.tabs(["Hierarchy View", "Detailed Analysis", "Calculation Details", "Performance Matrix"])
        
        with view_tabs[0]:
            self._render_hierarchy_view(data)
        
        with view_tabs[1]:
            self._render_detailed_analysis(data)
        
        with view_tabs[2]:
            self._render_calculation_details(data)
        
        with view_tabs[3]:
            self._render_performance_matrix(data)

    def _render_hierarchy_view(self, data):
        """Render interactive hierarchical view of results"""
        st.markdown("### Performance Hierarchy")
        
        # Key Topics Level
        for kt_name, kt in data.get('key_topics', {}).items():
            kt_key = f"kt_{kt_name}"
            kt_result = st.session_state.calculation_results.get(kt_key, {})
            
            if kt_result.get('status') == 'calculated':
                kt_score = kt_result.get('value', 0)
                kt_rating = kt_result.get('rating', 'N/A')
                
                with st.expander(f"**{kt_name}** - Score: {kt_score:.1f}% - {kt_rating}"):
                    # KT Details
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.progress(kt_score/100 if kt_score else 0)
                    with col2:
                        st.write(f"**Score:** {kt_score:.1f}%")
                    with col3:
                        st.write(f"**Rating:** {kt_rating}")
                    
                    # Show thresholds
                    st.markdown("**Rating Thresholds:**")
                    threshold_cols = st.columns(3)
                    with threshold_cols[0]:
                        st.success("Good: >= 90%")
                    with threshold_cols[1]:
                        st.warning("Satisfactory: >= 70%")
                    with threshold_cols[2]:
                        st.error("Needs Improvement: < 70%")
                    
                    st.divider()
                    
                    # Show Performance Signals under this KT
                    st.markdown("#### Performance Signals")
                    for ps_name, ps in data.get('performance_signals', {}).items():
                        if ps.get('key_topic') == kt_name or ps.get('key_topic_name') == kt_name:
                            self._render_ps_in_hierarchy(ps_name, ps, data)

    def _render_ps_in_hierarchy(self, ps_name, ps, data):
        """Render PS details within hierarchy"""
        ps_key = f"ps_{ps_name}"
        ps_result = st.session_state.calculation_results.get(ps_key, {})
        
        if ps_result.get('status') == 'calculated':
            ps_score = ps_result.get('value', 0)
            ps_rating = ps_result.get('rating', 'N/A')
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write(f"**{ps_name}**")
                st.progress(ps_score/100 if ps_score else 0)
            with col2:
                st.write(f"Score: {ps_score:.1f}%")
            with col3:
                st.write(f"Weight: {ps.get('weight', 0)}%")
            with col4:
                st.write(f"Rating: {ps_rating}")
            
            # Show ACs if requested
            if st.checkbox(f"Show Assessment Criteria", key=f"show_ac_{ps_name}"):
                self._render_ac_table_for_ps(ps_name, data)

    def _render_ac_table_for_ps(self, ps_name, data):
        """Render AC table for a specific PS"""
        ac_data = []
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            if ac.get('performance_signal') == ps_name:
                ac_key = f"ac_{ac_name}"
                result = st.session_state.calculation_results.get(ac_key, {})
                
                if result.get('status') == 'calculated':
                    ac_data.append({
                        'Assessment Criteria': ac_name[:50] + '...' if len(ac_name) > 50 else ac_name,
                        'Value': self._format_score_value(result),
                        'Weight': f"{ac.get('weight', 0)}%",
                        'Rating': result.get('rating', 'N/A')
                    })
        
        if ac_data:
            st.dataframe(pd.DataFrame(ac_data), use_container_width=True, height=200)

    def _render_calculation_details(self, data):
        """Show detailed calculation breakdown"""
        st.markdown("### Calculation Transparency")
        
        # Select an AC to see details
        ac_options = [name for name in data.get('assessment_criteria', {}).keys()]
        if ac_options:
            selected_ac = st.selectbox("Select Assessment Criteria for detailed view:", ac_options[:50])
            
            if selected_ac:
                ac = data.get('assessment_criteria', {}).get(selected_ac)
                ac_key = f"ac_{selected_ac}"
                result = st.session_state.calculation_results.get(ac_key, {})
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Configuration:**")
                    st.code(f"Formula: {ac.get('formula', 'N/A')}")
                    st.write(f"Type: {ac.get('formula_type', 'Unknown')}")
                    st.write(f"Weight: {ac.get('weight', 0)}%")
                    
                    # Show thresholds
                    thresholds = ac.get('thresholds', {})
                    if thresholds:
                        st.markdown("**Thresholds:**")
                        st.write(f"Good: {thresholds.get('good', '90')}%")
                        st.write(f"Satisfactory: {thresholds.get('satisfactory', '70')}%")
                
                with col2:
                    st.markdown("**Results:**")
                    st.write(f"Calculated Value: {self._format_score_value(result)}")
                    st.write(f"Status: {result.get('status', 'Not calculated')}")
                    st.write(f"Rating: {result.get('rating', 'N/A')}")
                    
                    # Show DPs used
                    dp_refs = self.formula_engine._extract_dp_references(ac.get('formula', ''))
                    if dp_refs:
                        st.markdown("**Data Points Used:**")
                        for dp_ref in dp_refs[:5]:
                            value = st.session_state.dp_values.get(dp_ref, 'Not entered')
                            st.write(f"- {dp_ref}: {value}")

    def _render_performance_matrix(self, data):
        """Render performance matrix view"""
        st.markdown("### Performance Matrix")
        
        # Create matrix data
        matrix_data = []
        
        for kt_name, kt in data.get('key_topics', {}).items():
            kt_key = f"kt_{kt_name}"
            kt_result = st.session_state.calculation_results.get(kt_key, {})
            
            row = {
                'Key Topic': kt_name,
                'Score': f"{kt_result.get('value', 0):.1f}" if kt_result.get('status') == 'calculated' else 'N/A',
                'Rating': kt_result.get('rating', 'N/A'),
                'Pillar': kt.get('pillar', 'Unknown')
            }
            matrix_data.append(row)
        
        if matrix_data:
            matrix_df = pd.DataFrame(matrix_data)
            st.dataframe(matrix_df, use_container_width=True)
        
        # Rating distribution chart
        st.markdown("### Rating Distribution")
        rating_counts = {'Good': 0, 'Satisfactory': 0, 'Needs Improvement': 0}
        for result in st.session_state.calculation_results.values():
            if result.get('status') == 'calculated':
                rating = result.get('rating', 'N/A')
                if rating in rating_counts:
                    rating_counts[rating] += 1
        
        if any(rating_counts.values()):
            rating_df = pd.DataFrame(list(rating_counts.items()), columns=['Rating', 'Count'])
            st.bar_chart(rating_df.set_index('Rating'))

    def _render_detailed_analysis(self, data):
        """Render detailed analysis with insights"""
        st.markdown("### Performance Analysis")
        
        # Areas needing improvement
        needs_improvement = []
        good_performers = []
        
        for key, result in st.session_state.calculation_results.items():
            if result.get('status') == 'calculated':
                item_type = key.split('_')[0].upper()
                item_name = key[len(item_type)+1:]
                
                # Get the score value
                score_value = result.get('value', 0)
                
                # Format score based on type
                if isinstance(score_value, str):
                    score_display = score_value
                else:
                    score_display = f"{score_value:.1f}"
                
                if result.get('rating') == 'Needs Improvement':
                    needs_improvement.append({
                        'Type': item_type, 
                        'Name': item_name,
                        'Score': score_display
                    })
                elif result.get('rating') == 'Good':
                    good_performers.append({
                        'Type': item_type,
                        'Name': item_name,
                        'Score': score_display
                    })
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.error(f"**Areas Needing Improvement ({len(needs_improvement)})**")
            for item in needs_improvement[:5]:
                st.write(f"- {item['Type']}: {item['Name'][:30]}... ({item['Score']})")
        
        with col2:
            st.success(f"**Top Performers ({len(good_performers)})**")
            for item in good_performers[:5]:
                st.write(f"- {item['Type']}: {item['Name'][:30]}... ({item['Score']})")

    def _calculate_overall_score(self):
        """Calculate overall assessment score"""
        scores = []
        for kt_name in self.db.load_database().get('key_topics', {}).keys():
            kt_key = f"kt_{kt_name}"
            if kt_key in st.session_state.calculation_results:
                result = st.session_state.calculation_results[kt_key]
                if result.get('status') == 'calculated' and result.get('value'):
                    scores.append(result['value'])
        
        return sum(scores) / len(scores) if scores else 0

    def _render_debug_info(self):
        """Show debug information about calculations"""
        with st.expander("🔍 Debug: Calculation Hierarchy"):
            data = self.db.load_database()
            
            # Show a sample AC with its formula
            st.markdown("### Sample Assessment Criteria")
            sample_ac = list(data.get('assessment_criteria', {}).items())[0] if data.get('assessment_criteria') else None
            if sample_ac:
                ac_name, ac = sample_ac
                st.write(f"**AC Name:** {ac_name}")
                st.write(f"**Formula:** {ac.get('formula', 'No formula')}")
                st.write(f"**Formula Type:** {ac.get('formula_type', 'Unknown')}")
                st.write(f"**Performance Signal:** {ac.get('performance_signal', 'None')}")
                
                # Show calculation status
                ac_key = f"ac_{ac_name}"
                if ac_key in st.session_state.calculation_results:
                    result = st.session_state.calculation_results[ac_key]
                    st.write(f"**Calculated Value:** {result.get('value', 'None')}")
                    st.write(f"**Status:** {result.get('status', 'Not calculated')}")
                    st.write(f"**Rating:** {result.get('rating', 'N/A')}")
    
    def _render_reports_tab(self):
        """Render reports and export options"""
        st.subheader("Reports & Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Export Options")
            
            if st.button("Export to Excel", type="primary"):
                self._export_to_excel()
            
            if st.button("Export to JSON"):
                self._export_to_json()
            
            if st.button("Generate PDF Report"):
                st.info("PDF generation will be implemented in Phase 4")
        
        with col2:
            st.markdown("### Assessment Comparison")
            
            data = self.db.load_database()
            assessments = list(data.get('assessments', {}).keys())
            
            if len(assessments) >= 2:
                compare1 = st.selectbox("Assessment 1", assessments, key="compare1")
                compare2 = st.selectbox("Assessment 2", assessments, key="compare2")
                
                if st.button("Compare Assessments"):
                    self._compare_assessments(compare1, compare2)
            else:
                st.info("Need at least 2 assessments for comparison")
    
    def _create_new_assessment(self, project_name: str):
        """Create a new assessment"""
        data = self.db.load_database()
        
        # Generate assessment ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        assessment_id = f"{project_name}_{timestamp}"
        
        # Create assessment entry
        if 'assessments' not in data:
            data['assessments'] = {}
        
        data['assessments'][assessment_id] = {
            'project_name': project_name,
            'created_date': datetime.now().isoformat(),
            'created_by': 'User',
            'status': 'draft',
            'version': 1
        }
        
        # Initialize empty values
        if 'assessment_values' not in data:
            data['assessment_values'] = {}
        data['assessment_values'][assessment_id] = {}
        
        if 'assessment_results' not in data:
            data['assessment_results'] = {}
        data['assessment_results'][assessment_id] = {
            'ac_scores': {},
            'ps_scores': {},
            'kt_scores': {}
        }
        
        self.db.save_database(data)
        
        # Set as current assessment
        st.session_state.current_assessment = assessment_id
        st.session_state.dp_values = {}
        st.session_state.calculation_results = {}
        
        st.success(f"Created new assessment: {assessment_id}")
        st.rerun()
    
    def _load_assessment(self, assessment_id: str):
        """Load an existing assessment"""
        data = self.db.load_database()
        
        # Load DP values
        values = data.get('assessment_values', {}).get(assessment_id, {})
        st.session_state.dp_values = values.copy()
        
        # Load calculation results
        results = data.get('assessment_results', {}).get(assessment_id, {})
        st.session_state.calculation_results = {}
        
        # Convert stored results to session format
        for ac_name, score_data in results.get('ac_scores', {}).items():
            st.session_state.calculation_results[f"ac_{ac_name}"] = score_data
        
        for ps_name, score_data in results.get('ps_scores', {}).items():
            st.session_state.calculation_results[f"ps_{ps_name}"] = score_data
        
        for kt_name, score_data in results.get('kt_scores', {}).items():
            st.session_state.calculation_results[f"kt_{kt_name}"] = score_data
    
    def _save_assessment(self):
        """Save current assessment to database"""
        if not st.session_state.current_assessment:
            return
        
        data = self.db.load_database()
        assessment_id = st.session_state.current_assessment
        
        # Save DP values
        if 'assessment_values' not in data:
            data['assessment_values'] = {}
        data['assessment_values'][assessment_id] = st.session_state.dp_values.copy()
        
        # Save calculation results
        if 'assessment_results' not in data:
            data['assessment_results'] = {}
        
        results = {
            'ac_scores': {},
            'ps_scores': {},
            'kt_scores': {}
        }
        
        for key, value in st.session_state.calculation_results.items():
            if key.startswith('ac_'):
                ac_name = key[3:]
                results['ac_scores'][ac_name] = value
            elif key.startswith('ps_'):
                ps_name = key[3:]
                results['ps_scores'][ps_name] = value
            elif key.startswith('kt_'):
                kt_name = key[3:]
                results['kt_scores'][kt_name] = value
        
        data['assessment_results'][assessment_id] = results
        
        # Update assessment metadata
        if assessment_id in data.get('assessments', {}):
            data['assessments'][assessment_id]['updated_date'] = datetime.now().isoformat()
        
        self.db.save_database(data)
    
    def _calculate_all_scores(self):
        """Calculate all scores for the current assessment"""
        data = self.db.load_database()
        
        # Get actual pillars from database
        actual_pillars = set()
        for dp in data.get('data_points', {}).values():
            pillar = dp.get('pillar')
            if pillar:
                actual_pillars.add(pillar)
        
        for pillar in actual_pillars:
            self._calculate_pillar_scores(pillar)
    
    def _calculate_pillar_scores(self, pillar: str):
        """Calculate all scores for a specific pillar"""
        data = self.db.load_database()
        
        # Check how many ACs belong to this pillar
        pillar_acs = []
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            ac_pillar = self._get_ac_pillar(ac_name)
            if ac_pillar == pillar:
                pillar_acs.append(ac_name)
        
        if len(pillar_acs) == 0:
            st.warning("No ACs found! The pillar names don't match between DPs and KTs")
            # Show what pillars the ACs think they belong to
            all_ac_pillars = set()
            for ac_name in data.get('assessment_criteria', {}).keys():
                all_ac_pillars.add(self._get_ac_pillar(ac_name))
            st.write(f"ACs belong to these pillars: {all_ac_pillars}")

        # DEBUG: Let's see what's actually happening
        with st.expander("🔍 Debug: Why Calculations Aren't Working"):
            # Check a few ACs for this pillar
            st.write("**Checking Assessment Criteria formulas:**")
            checked = 0
            for ac_name, ac in data.get('assessment_criteria', {}).items():
                if self._get_ac_pillar(ac_name) == pillar and checked < 3:
                    st.write(f"\n**AC:** {ac_name}")
                    st.write(f"**Formula:** `{ac.get('formula')}`")
                    
                    # What DPs does the formula reference?
                    dp_refs = self.formula_engine._extract_dp_references(ac.get('formula', ''))
                    st.write(f"**Formula references these DPs:** {dp_refs}")
                    
                    # Do we have values for them?
                    matched = []
                    unmatched = []
                    for ref in dp_refs:
                        found = False
                        for dp_name in st.session_state.dp_values.keys():
                            if ref.lower() in dp_name.lower() or dp_name.lower() in ref.lower():
                                matched.append(f"{ref} → {dp_name}")
                                found = True
                                break
                        if not found:
                            unmatched.append(ref)
                    
                    if matched:
                        st.success(f"✅ Matched: {matched}")
                    if unmatched:
                        st.error(f"❌ NOT FOUND: {unmatched}")
                        
                        # Show available DP names that might match
                        st.write("**Available DP names in this pillar:**")
                        pillar_dps = [name for name, dp in data.get('data_points', {}).items() 
                                    if dp.get('pillar') == pillar]
                        for dp in pillar_dps[:5]:
                            st.write(f"  - {dp}")
                    
                    checked += 1
                    st.write("---")

        # Step 1: Calculate all AC scores for this pillar
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            # Check if AC belongs to this pillar
            if self._get_ac_pillar(ac_name) == pillar:
                self._calculate_ac_score(ac_name, ac)
        
        # Step 2: Calculate PS scores for this pillar
        for ps_name, ps in data.get('performance_signals', {}).items():
            if self._get_ps_pillar(ps_name) == pillar:
                self._calculate_ps_score(ps_name, ps)
        
        # Step 3: Calculate KT scores for this pillar
        for kt_name, kt in data.get('key_topics', {}).items():
            if kt.get('pillar') == pillar:
                self._calculate_kt_score(kt_name, kt)
    
    def _calculate_ac_score(self, ac_name: str, ac: dict):
        """Calculate a single AC score"""
        formula = ac.get('formula', '')
        formula_type = ac.get('formula_type', 'quantitative')
        
        # Get DP values needed for this AC
        dp_values = {}
        dp_refs = self.formula_engine._extract_dp_references(formula)
        
        for dp_ref in dp_refs:
            # Find matching DP value
            for dp_name, value in st.session_state.dp_values.items():
                if dp_ref.lower() in dp_name.lower() or dp_name.lower() in dp_ref.lower():
                    dp_values[dp_name] = value
                    break
        
        # Evaluate formula
        result, status = self.formula_engine.evaluate(formula, dp_values, formula_type)
        
        # Get rating based on thresholds
        rating = 'N/A'
        if status == 'calculated' and result is not None:
            rating = self._get_ac_rating(result, ac)
        
        # Store result
        st.session_state.calculation_results[f"ac_{ac_name}"] = {
            'value': result,
            'status': status,
            'rating': rating,
            'formula': formula,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_ps_score(self, ps_name: str, ps: dict):
        """Calculate PS score from weighted AC scores"""
        data = self.db.load_database()
        
        # Get all ACs for this PS
        ac_scores = []
        ac_weights = []
        
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            if ac.get('performance_signal') == ps_name:
                ac_key = f"ac_{ac_name}"
                if ac_key in st.session_state.calculation_results:
                    result = st.session_state.calculation_results[ac_key]
                    if result.get('status') == 'calculated' and result.get('value') is not None:
                        # Convert qualitative values to scores
                        value = result['value']
                        if isinstance(value, str):
                            value = self._qualitative_to_score(value)
                        
                        if value is not None:
                            ac_scores.append(value)
                            ac_weights.append(ac.get('weight', 0))
        
        # Calculate weighted average
        if ac_scores and ac_weights:
            total_weight = sum(ac_weights)
            if total_weight > 0:
                ps_score = sum(s * w for s, w in zip(ac_scores, ac_weights)) / total_weight
                rating = self._get_rating(ps_score, 'ps')
                
                st.session_state.calculation_results[f"ps_{ps_name}"] = {
                    'value': ps_score,
                    'status': 'calculated',
                    'rating': rating,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                st.session_state.calculation_results[f"ps_{ps_name}"] = {
                    'value': None,
                    'status': 'error',
                    'rating': 'N/A',
                    'error': 'Total weight is zero'
                }
        else:
            st.session_state.calculation_results[f"ps_{ps_name}"] = {
                'value': None,
                'status': 'incomplete',
                'rating': 'N/A'
            }
    
    def _calculate_kt_score(self, kt_name: str, kt: dict):
        """Calculate KT score from weighted PS scores"""
        data = self.db.load_database()
        
        # Get all PS for this KT
        ps_scores = []
        ps_weights = []
        
        for ps_name, ps in data.get('performance_signals', {}).items():
            if ps.get('key_topic') == kt_name:
                ps_key = f"ps_{ps_name}"
                if ps_key in st.session_state.calculation_results:
                    result = st.session_state.calculation_results[ps_key]
                    if result.get('status') == 'calculated' and result.get('value') is not None:
                        ps_scores.append(result['value'])
                        ps_weights.append(ps.get('weight', 0))
        
        # Calculate weighted average
        if ps_scores and ps_weights:
            total_weight = sum(ps_weights)
            if total_weight > 0:
                kt_score = sum(s * w for s, w in zip(ps_scores, ps_weights)) / total_weight
                rating = self._get_rating(kt_score, 'kt')
                
                st.session_state.calculation_results[f"kt_{kt_name}"] = {
                    'value': kt_score,
                    'status': 'calculated',
                    'rating': rating,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                st.session_state.calculation_results[f"kt_{kt_name}"] = {
                    'value': None,
                    'status': 'error',
                    'rating': 'N/A',
                    'error': 'Total weight is zero'
                }
        else:
            st.session_state.calculation_results[f"kt_{kt_name}"] = {
                'value': None,
                'status': 'incomplete',
                'rating': 'N/A'
            }
    
    def _calculate_affected_scores(self, dp_name: str):
        """Calculate scores affected by a DP value change"""
        data = self.db.load_database()
        
        # Find all ACs that use this DP
        affected_acs = []
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            formula = ac.get('formula', '')
            if dp_name.lower() in formula.lower():
                affected_acs.append(ac_name)
                self._calculate_ac_score(ac_name, ac)
        
        # Find affected PS (those containing affected ACs)
        affected_ps = set()
        for ac_name in affected_acs:
            ac = data.get('assessment_criteria', {}).get(ac_name, {})
            ps_name = ac.get('performance_signal')
            if ps_name:
                affected_ps.add(ps_name)
        
        # Calculate affected PS
        for ps_name in affected_ps:
            ps = data.get('performance_signals', {}).get(ps_name, {})
            if ps:
                self._calculate_ps_score(ps_name, ps)
        
        # Find affected KT
        affected_kt = set()
        for ps_name in affected_ps:
            ps = data.get('performance_signals', {}).get(ps_name, {})
            kt_name = ps.get('key_topic')
            if kt_name:
                affected_kt.add(kt_name)
        
        # Calculate affected KT
        for kt_name in affected_kt:
            kt = data.get('key_topics', {}).get(kt_name, {})
            if kt:
                self._calculate_kt_score(kt_name, kt)
    
    def _get_ac_rating(self, value: Any, ac: dict) -> str:
        """Get rating for AC based on value and thresholds"""
        thresholds = ac.get('thresholds', {})
        
        if ac.get('formula_type') == 'qualitative':
            # Qualitative rating
            if isinstance(value, str):
                value_lower = value.lower()
                if value_lower in ['yes', 'completed', 'done']:
                    return 'Good'
                elif value_lower in ['partially', 'partially applied', 'in progress']:
                    return 'Satisfactory'
                else:
                    return 'Needs Improvement'
        else:
            # Quantitative rating
            try:
                value_float = float(value)
                
                # Default thresholds if not specified
                good_threshold = float(thresholds.get('good', 90))
                sat_threshold = float(thresholds.get('satisfactory', 70))
                
                if value_float >= good_threshold:
                    return 'Good'
                elif value_float >= sat_threshold:
                    return 'Satisfactory'
                else:
                    return 'Needs Improvement'
            except:
                return 'N/A'
        
        return 'N/A'
    
    def _get_rating(self, score: float, level: str) -> str:
        """Get rating based on score and level (ps/kt)"""
        if score >= 90:
            return 'Good'
        elif score >= 70:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'
    
    def _get_rating_color(self, rating: str) -> str:
        """Get color for rating"""
        colors = {
            'Good': 'green',
            'Satisfactory': 'yellow',
            'Needs Improvement': 'red',
            'N/A': 'gray'
        }
        return colors.get(rating, 'gray')
    
    def _format_score_value(self, result: dict) -> str:
        """Format score value based on its type"""
        value = result.get('value', 0)
        if isinstance(value, str):
            return value  # Return as-is for qualitative values
        elif isinstance(value, (int, float)):
            return f"{value:.2f}"
        else:
            return str(value)
    
    def _qualitative_to_score(self, value: str) -> float:
        """Convert qualitative value to numeric score"""
        value_lower = str(value).lower()
        
        if value_lower in ['yes', 'completed', 'done', 'good']:
            return 100
        elif value_lower in ['partially', 'partially applied', 'in progress', 'satisfactory']:
            return 75
        elif value_lower in ['no', 'not completed', 'pending', 'needs improvement']:
            return 25
        else:
            return None
    
    def _find_dp_performance_signal(self, dp_name: str) -> str:
        """Find which PS a DP belongs to through AC relationship"""
        data = self.db.load_database()
        
        # Find AC that uses this DP
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            formula = ac.get('formula', '')
            if dp_name.lower() in formula.lower():
                return ac.get('performance_signal', 'Uncategorized')
        
        return 'Uncategorized'
    
    def _get_ac_pillar(self, ac_name: str) -> str:
        """Get pillar for an AC by finding which PS contains it"""
        data = self.db.load_database()
        
        # Find which PS contains this AC
        for ps_name, ps in data.get('performance_signals', {}).items():
            if 'assessment_criteria' in ps:
                # Check if this AC is in the PS's assessment_criteria array
                for ac in ps['assessment_criteria']:
                    if isinstance(ac, dict) and ac.get('name') == ac_name:
                        # Found it! Now get the KT's pillar
                        kt_name = ps.get('key_topic_name')
                        if kt_name:
                            for kt in data.get('key_topics', {}).values():
                                if kt.get('name') == kt_name:
                                    return kt.get('pillar', 'Unknown')
                    elif isinstance(ac, str) and ac == ac_name:
                        # Found it! Now get the KT's pillar
                        kt_name = ps.get('key_topic_name')
                        if kt_name:
                            for kt in data.get('key_topics', {}).values():
                                if kt.get('name') == kt_name:
                                    return kt.get('pillar', 'Unknown')
        
        return 'Unknown'
    
    def _get_ps_pillar(self, ps_name: str) -> str:
        """Get pillar for a PS based on its ACs"""
        data = self.db.load_database()
        
        # Find first AC that belongs to this PS and get its pillar
        for ac_name, ac in data.get('assessment_criteria', {}).items():
            if ac.get('performance_signal') == ps_name:
                return self._get_ac_pillar(ac_name)
        
        return 'Unknown'
    
    def _export_to_excel(self):
        """Export assessment to Excel"""
        import io
        
        # Create Excel writer
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Export DP values
            dp_data = []
            for dp_name, value in st.session_state.dp_values.items():
                dp_data.append({'Data Point': dp_name, 'Value': value})
            
            if dp_data:
                dp_df = pd.DataFrame(dp_data)
                dp_df.to_excel(writer, sheet_name='DP Values', index=False)
            
            # Export calculation results
            results_data = []
            for key, result in st.session_state.calculation_results.items():
                if result.get('status') == 'calculated':
                    results_data.append({
                        'Item': key.replace('ac_', '').replace('ps_', '').replace('kt_', ''),
                        'Type': key.split('_')[0].upper(),
                        'Value': result.get('value'),
                        'Rating': result.get('rating')
                    })
            
            if results_data:
                results_df = pd.DataFrame(results_data)
                results_df.to_excel(writer, sheet_name='Results', index=False)
        
        # Download
        st.download_button(
            label="Download Excel Report",
            data=output.getvalue(),
            file_name=f"assessment_{st.session_state.current_assessment}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    def _export_to_json(self):
        """Export assessment to JSON"""
        export_data = {
            'assessment_id': st.session_state.current_assessment,
            'dp_values': st.session_state.dp_values,
            'calculation_results': st.session_state.calculation_results,
            'export_date': datetime.now().isoformat()
        }
        
        json_str = json.dumps(export_data, indent=2)
        
        st.download_button(
            label="Download JSON Report",
            data=json_str,
            file_name=f"assessment_{st.session_state.current_assessment}.json",
            mime="application/json"
        )
    
    def _compare_assessments(self, assess1: str, assess2: str):
        """Compare two assessments"""
        st.info("Assessment comparison will show differences in scores and ratings")
        # This would show a detailed comparison - implement in Phase 4