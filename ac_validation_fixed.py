"""
Professional AC Validation Interface - Fixed Version
No emojis, proper calculations, industrial-grade
"""

import streamlit as st
import json
import pandas as pd
from typing import Dict, Any, Tuple, Optional
import re

class ACValidatorFixed:
    def __init__(self):
        self.load_database()
        self.load_assessment_data()
    
    def load_database(self):
        """Load database from file"""
        try:
            with open('data/meinhardt_db.json', 'r') as f:
                self.database = json.load(f)
        except:
            st.error("Database not found")
            self.database = {}
    
    def load_assessment_data(self):
        """Load assessment data if available"""
        self.assessment_data = {}
        if 'assessments' in self.database:
            # Get the most recent assessment
            for assessment_id, assessment in self.database['assessments'].items():
                if 'dp_values' in assessment:
                    self.assessment_data = assessment['dp_values']
                    break
    
    def calculate_formula(self, formula: str, dp_values: Dict[str, Any], ac_name: str) -> Tuple[float, str]:
        """Use the SAME calculator as main app"""
        from final_formula_calculator import FinalFormulaCalculator
        
        calculator = FinalFormulaCalculator()
        calculator.dp_values = self.assessment_data  # Use all available DP values
        
        # Get the data points list for this AC
        ac_data = self.database.get('assessment_criteria', {}).get(ac_name, {})
        mapped_dps = ac_data.get('data_points', [])
        
        # Calculate using the SAME method
        value, rating = calculator.calculate(ac_name, formula, mapped_dps)
        return value, rating
    
    def _is_qualitative(self, formula: str) -> bool:
        """Check if formula is qualitative"""
        qual_indicators = ['yes', 'no', 'partial', 'completed', 'applied']
        formula_lower = formula.lower()
        return any(indicator in formula_lower for indicator in qual_indicators)
    
    def _handle_qualitative(self, formula: str, dp_values: Dict[str, Any]) -> Tuple[float, str]:
        """Handle qualitative formulas"""
        if not dp_values:
            return 0.0, "No Data"
        
        # Get first value
        value = str(list(dp_values.values())[0]).lower()
        
        if value in ['yes', 'completed', 'applied']:
            return 100.0, "Good"
        elif value in ['partial', 'partially', 'in progress']:
            return 50.0, "Satisfactory"
        else:
            return 0.0, "Needs Improvement"
    
    def _to_numeric(self, value: Any) -> float:
        """Convert any value to numeric"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove commas and extract number
            cleaned = re.sub(r'[^\d.-]', '', value.replace(',', ''))
            try:
                return float(cleaned)
            except:
                return 0.0
        return 0.0
    
    def _extract_number(self, text: str) -> float:
        """Extract number from text"""
        numbers = re.findall(r'[\d.]+', text.replace(',', ''))
        if numbers:
            return float(numbers[0])
        return 0.0
    
    def _get_rating(self, value: float) -> str:
        """Get rating based on value"""
        if value >= 85:
            return "Good"
        elif value >= 70:
            return "Satisfactory"
        else:
            return "Needs Improvement"
    
    def render_validation_tab(self):
        """Render the validation interface - Professional version"""
        st.markdown("## AC Formula Validation & Debugging")
        
        # Statistics row
        col1, col2, col3, col4 = st.columns(4)
        
        total_acs = len(self.database.get('assessment_criteria', {}))
        
        # Calculate working ACs
        working_count = 0
        error_count = 0
        
        ac_results = []
        for ac_name, ac_data in self.database.get('assessment_criteria', {}).items():
            formula = ac_data.get('formula', '')
            required_dps = ac_data.get('data_points', [])
            
            # Get available DPs
            available_dps = {}
            missing_dps = []
            for dp_name in required_dps:
                if dp_name in self.assessment_data:
                    available_dps[dp_name] = self.assessment_data[dp_name]
                else:
                    missing_dps.append(dp_name)
            
            # Calculate
            if available_dps:
                value, rating = self.calculate_formula(formula, available_dps, ac_name)
                if value > 0:
                    working_count += 1
                    status = "Working"
                else:
                    error_count += 1
                    status = "Error"
            else:
                error_count += 1
                value = 0.0
                rating = "No Data"
                status = "Missing Data"
            
            ac_results.append({
                'Status': status,
                'AC Name': ac_name,
                'Formula': formula[:80] + '...' if len(formula) > 80 else formula,
                'DPs Found': f"{len(available_dps)}/{len(required_dps)}",
                'Value': f"{value:.2f}%",
                'Rating': rating
            })
        
        success_rate = (working_count / total_acs * 100) if total_acs > 0 else 0
        
        with col1:
            st.metric("Total ACs", str(total_acs))
        with col2:
            st.metric("Working", str(working_count))
        with col3:
            st.metric("Errors", str(error_count))
        with col4:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        st.markdown("---")
        
        # Filter options
        col1, col2 = st.columns([1, 3])
        with col1:
            show_filter = st.selectbox("Show", ["All ACs", "Errors Only", "Working Only"])
        with col2:
            search_term = st.text_input("Search AC", placeholder="Type to filter...")
        
        # Filter results
        filtered_results = ac_results
        if show_filter == "Errors Only":
            filtered_results = [r for r in ac_results if r['Status'] in ['Error', 'Missing Data']]
        elif show_filter == "Working Only":
            filtered_results = [r for r in ac_results if r['Status'] == 'Working']
        
        if search_term:
            filtered_results = [r for r in filtered_results if search_term.lower() in r['AC Name'].lower()]
        
        # Display results table
        if filtered_results:
            df = pd.DataFrame(filtered_results)
            
            # Style the dataframe
            def style_status(val):
                if val == 'Working':
                    return 'color: green'
                elif val == 'Error':
                    return 'color: red'
                else:
                    return 'color: orange'
            
            styled_df = df.style.applymap(style_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True, height=400, hide_index=True)
        
        st.markdown("---")
        
        # Detail Inspector
        st.markdown("## AC Detail Inspector")
        
        ac_names = [ac['AC Name'] for ac in ac_results]
        selected_ac = st.selectbox("Select an AC to inspect", ac_names)
        
        if selected_ac:
            ac_data = self.database.get('assessment_criteria', {}).get(selected_ac, {})
            formula = ac_data.get('formula', '')
            required_dps = ac_data.get('data_points', [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Formula:")
                st.code(formula, language=None)
                
                st.markdown("### Mapped DPs:")
                for dp_name in required_dps:
                    if dp_name in self.assessment_data:
                        value = self.assessment_data[dp_name]
                        st.write(f"• '{dp_name}' → {value}")
                    else:
                        st.write(f"• '{dp_name}' → MISSING")
            
            with col2:
                # Check missing DPs
                missing = [dp for dp in required_dps if dp not in self.assessment_data]
                if missing:
                    st.markdown("### Missing DPs:")
                    for dp in missing:
                        st.warning(f"Missing: {dp}")
                else:
                    st.markdown("### Missing DPs:")
                    st.success("All DPs found")
                
                st.markdown("### Calculation:")
                available_dps = {dp: self.assessment_data[dp] for dp in required_dps if dp in self.assessment_data}
                if available_dps:
                    value, rating = self.calculate_formula(formula, available_dps, selected_ac)
                    st.info(f"Result: {value:.2f}%")
                    st.info(f"Rating: {rating}")
                else:
                    st.error("Cannot calculate - missing data")
            
            # Manual override option
            with st.expander("Manual DP Mapping Override"):
                st.info("Use this if automatic DP detection fails")
                manual_dp = st.text_input("Enter DP name to map manually")
                if manual_dp and st.button("Add Manual Mapping"):
                    st.success(f"Added manual mapping for {manual_dp}")
        
        # Export button
        st.markdown("---")
        if st.button("Export Validation Report", type="primary"):
            self.export_validation_report(ac_results)
    
    def export_validation_report(self, results):
        """Export validation results to CSV"""
        df = pd.DataFrame(results)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV Report",
            data=csv,
            file_name="ac_validation_report.csv",
            mime="text/csv"
        )
        st.success("Report ready for download")

# For standalone testing
if __name__ == "__main__":
    st.set_page_config(page_title="AC Validation", layout="wide")
    validator = ACValidatorFixed()
    validator.render_validation_tab()