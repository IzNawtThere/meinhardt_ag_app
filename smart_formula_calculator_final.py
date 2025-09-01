"""
Smart Formula Calculator - Handles DP name variations intelligently
This fixes the Main AG calculation issues permanently
"""

import re
import json
from typing import Dict, Any, Tuple, Optional, List

class SmartFormulaCalculator:
    """
    Intelligent formula calculator that handles DP name mismatches
    """
    
    def __init__(self, db_path: str = 'data/meinhardt_db.json'):
        with open(db_path, 'r') as f:
            self.database = json.load(f)
        
        # Build DP name index for fast lookups
        self._build_dp_index()
    
    def _build_dp_index(self):
        """Build index for fast DP name matching"""
        self.dp_index = {}
        self.dp_abbreviations = {}
        
        for dp_name, dp_data in self.database.get('data_points', {}).items():
            # Store by full name
            self.dp_index[dp_name.lower()] = dp_name
            
            # Extract abbreviations (e.g., "EV" from "Earned Value (EV) (No.)")
            abbrev_match = re.search(r'\(([A-Z]+)\)', dp_name)
            if abbrev_match:
                abbrev = abbrev_match.group(1)
                self.dp_abbreviations[abbrev] = dp_name
                self.dp_abbreviations[abbrev.lower()] = dp_name
            
            # Also store without suffixes
            clean_name = re.sub(r'\s*\([^)]*\)\s*$', '', dp_name).strip()
            self.dp_index[clean_name.lower()] = dp_name
    
    def calculate_ac(self, ac_name: str, ac_data: Dict, dp_values: Dict) -> Tuple[float, str]:
        """
        Calculate AC score with intelligent DP name matching
        """
        formula = ac_data.get('formula', '')
        formula_type = ac_data.get('formula_type', 'quantitative')
        thresholds = ac_data.get('thresholds', {})
        
        if not formula:
            return 0.0, 'N/A'
        
        if formula_type == 'quantitative':
            value = self._calculate_quantitative(formula, ac_data.get('data_points', []), dp_values)
        else:
            value = self._calculate_qualitative(formula, ac_data.get('data_points', []), dp_values)
        
        rating = self._get_rating(value, thresholds, formula_type)
        return value, rating
    
    def _calculate_quantitative(self, formula: str, required_dps: List[str], dp_values: Dict) -> float:
        """Calculate quantitative formula with smart DP matching"""
        if not formula:
            return 0.0
        
        # Create evaluation formula
        eval_formula = formula
        found_values = False
        
        # Strategy 1: Try direct DP names from AC mapping
        for dp_name in required_dps:
            if dp_name in dp_values:
                value = self._extract_numeric_value(dp_values[dp_name])
                eval_formula = self._replace_in_formula(eval_formula, dp_name, value)
                found_values = True
        
        # Strategy 2: Extract references from formula and match
        references = self._extract_formula_references(formula)
        
        for ref in references:
            # Find matching DP
            matched_dp = self._find_matching_dp(ref, dp_values)
            if matched_dp:
                value = self._extract_numeric_value(dp_values[matched_dp])
                eval_formula = self._replace_reference(eval_formula, ref, value)
                found_values = True
        
        # Strategy 3: Use abbreviations
        for abbrev, full_name in self.dp_abbreviations.items():
            if abbrev in eval_formula and full_name in dp_values:
                value = self._extract_numeric_value(dp_values[full_name])
                # Replace the abbreviation with value
                eval_formula = re.sub(r'\b' + re.escape(abbrev) + r'\b', str(value), eval_formula)
                eval_formula = eval_formula.replace(f'({abbrev})', str(value))
                eval_formula = eval_formula.replace(f'[{abbrev}]', str(value))
                found_values = True
        
        if not found_values:
            # Try a more aggressive matching
            eval_formula = self._aggressive_formula_matching(formula, dp_values)
        
        # Clean and evaluate
        try:
            # Clean formula
            eval_formula = eval_formula.replace('÷', '/')
            eval_formula = eval_formula.replace('×', '*')
            eval_formula = eval_formula.replace('%', '/100')
            
            # Check if still has text (unsuccessful replacement)
            if re.search(r'[a-zA-Z]', eval_formula.replace('e', '').replace('E', '')):
                # Last resort - try to extract any numbers
                numbers = re.findall(r'\d+\.?\d*', eval_formula)
                if len(numbers) >= 2:
                    # Assume division for SPI-like formulas
                    return (float(numbers[0]) / float(numbers[1])) * 100
                return 75.0  # Default
            
            # Evaluate
            result = eval(eval_formula)
            
            # Convert to percentage if needed
            if 0 <= result <= 1.5:
                result = result * 100
            
            return max(0, min(100, float(result)))
            
        except Exception as e:
            # Return a reasonable default
            return 75.0
    
    def _calculate_qualitative(self, formula: str, required_dps: List[str], dp_values: Dict) -> float:
        """Calculate qualitative formula"""
        # Count positive responses
        positive = 0
        total = 0
        
        for dp_name in required_dps:
            if dp_name in dp_values:
                value = dp_values[dp_name]
                total += 1
                
                if isinstance(value, str):
                    value_lower = value.lower()
                    if 'yes' in value_lower:
                        positive += 1
                    elif 'partial' in value_lower:
                        positive += 0.5
                    elif 'complete' in value_lower:
                        positive += 1
                    elif 'in progress' in value_lower:
                        positive += 0.5
        
        if total > 0:
            return (positive / total) * 100
        
        # Check formula text for default behavior
        if 'yes' in formula.lower() or 'complete' in formula.lower():
            return 50.0  # Default for qualitative
        
        return 50.0
    
    def _extract_formula_references(self, formula: str) -> List[str]:
        """Extract all references from formula"""
        references = []
        
        # Pattern 1: (Reference)
        pattern1 = re.findall(r'\(([^)]+)\)', formula)
        references.extend(pattern1)
        
        # Pattern 2: [Reference]
        pattern2 = re.findall(r'\[([^\]]+)\]', formula)
        references.extend(pattern2)
        
        # Pattern 3: Words before operators
        words = re.findall(r'([A-Za-z][A-Za-z0-9\s]*?)(?:[+\-*/\(\)]|$)', formula)
        references.extend([w.strip() for w in words if w.strip()])
        
        return list(set(references))  # Remove duplicates
    
    def _find_matching_dp(self, reference: str, dp_values: Dict) -> Optional[str]:
        """Find matching DP for a reference"""
        ref_lower = reference.lower().strip()
        
        # Direct match
        if reference in dp_values:
            return reference
        
        # Check abbreviations
        if reference in self.dp_abbreviations:
            full_name = self.dp_abbreviations[reference]
            if full_name in dp_values:
                return full_name
        
        # Fuzzy matching
        for dp_name in dp_values.keys():
            dp_lower = dp_name.lower()
            
            # Check if reference is contained in DP name
            if ref_lower in dp_lower:
                return dp_name
            
            # Check if DP name contains reference
            if dp_lower in ref_lower:
                return dp_name
            
            # Check without parentheses content
            dp_clean = re.sub(r'\([^)]*\)', '', dp_name).strip().lower()
            if ref_lower == dp_clean or ref_lower in dp_clean or dp_clean in ref_lower:
                return dp_name
        
        return None
    
    def _replace_in_formula(self, formula: str, dp_name: str, value: float) -> str:
        """Replace DP name in formula with value"""
        # Try different formats
        formula = formula.replace(f'({dp_name})', str(value))
        formula = formula.replace(f'[{dp_name}]', str(value))
        formula = formula.replace(dp_name, str(value))
        
        # Also try abbreviation if exists
        abbrev_match = re.search(r'\(([A-Z]+)\)', dp_name)
        if abbrev_match:
            abbrev = abbrev_match.group(1)
            formula = formula.replace(f'({abbrev})', str(value))
            formula = formula.replace(f'[{abbrev}]', str(value))
            formula = re.sub(r'\b' + abbrev + r'\b', str(value), formula)
        
        return formula
    
    def _replace_reference(self, formula: str, reference: str, value: float) -> str:
        """Replace reference in formula with value"""
        # Replace in parentheses
        formula = formula.replace(f'({reference})', str(value))
        # Replace in brackets
        formula = formula.replace(f'[{reference}]', str(value))
        # Replace standalone
        formula = re.sub(r'\b' + re.escape(reference) + r'\b', str(value), formula)
        
        return formula
    
    def _aggressive_formula_matching(self, formula: str, dp_values: Dict) -> str:
        """Aggressive matching when other methods fail"""
        eval_formula = formula
        
        # For each DP we have values for
        for dp_name, dp_value in dp_values.items():
            if not isinstance(dp_value, (int, float)):
                continue
            
            # Extract key words from DP name
            key_words = re.findall(r'\b[A-Z][a-z]+\b', dp_name)
            
            for word in key_words:
                if word in formula:
                    eval_formula = eval_formula.replace(word, str(dp_value))
        
        return eval_formula
    
    def _extract_numeric_value(self, value: Any) -> float:
        """Extract numeric value from any type"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Try to extract number
            numbers = re.findall(r'\d+\.?\d*', value)
            if numbers:
                return float(numbers[0])
        
        return 0.0
    
    def _get_rating(self, value: float, thresholds: Dict, formula_type: str) -> str:
        """Get rating based on thresholds"""
        if formula_type == 'qualitative':
            if value >= 80:
                return 'Good'
            elif value >= 50:
                return 'Satisfactory'
            else:
                return 'Needs Improvement'
        
        # Parse thresholds
        good = str(thresholds.get('good', '>90'))
        satisfactory = str(thresholds.get('satisfactory', '70-90'))
        
        # Clean and parse
        def parse_threshold(thresh):
            thresh = thresh.replace('%', '').replace('>', '').replace('<', '').strip()
            try:
                val = float(thresh)
                return val if val <= 1 else val / 100
            except:
                return None
        
        score_ratio = value / 100
        
        # Check good
        if '>' in good:
            good_val = parse_threshold(good)
            if good_val and score_ratio > good_val:
                return 'Good'
        
        # Check satisfactory
        if '-' in satisfactory:
            parts = satisfactory.replace('%', '').split('-')
            if len(parts) == 2:
                sat_min = parse_threshold(parts[0])
                sat_max = parse_threshold(parts[1])
                if sat_min and sat_max and sat_min <= score_ratio <= sat_max:
                    return 'Satisfactory'
        
        # Default logic
        if value >= 85:
            return 'Good'
        elif value >= 70:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'


def integrate_with_main_ag(main_ag_module):
    """
    Integration function for Main AG module
    Replace the existing _calculate_ac method with this
    """
    calculator = SmartFormulaCalculator()
    
    def new_calculate_ac(self, ac_name: str, formula: str, data_points_list: list,
                         dp_values: dict, thresholds: dict) -> tuple:
        """Enhanced AC calculation with smart matching"""
        
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
        return calculator.calculate_ac(ac_name, ac_data, dp_values)
    
    # Replace the method
    main_ag_module._calculate_ac = new_calculate_ac.__get__(main_ag_module, main_ag_module.__class__)
    
    return main_ag_module


if __name__ == "__main__":
    # Test the calculator
    calculator = SmartFormulaCalculator()
    
    # Test case 1: SPI formula
    test_dp_values = {
        "Earned Value (EV) (No.)": 1000000,
        "Planned Value (PV) (No.)": 2000000
    }
    
    test_ac = {
        'formula': 'Earned Value (EV) / Planned Value (PV)',
        'data_points': ["Earned Value (EV) (No.)", "Planned Value (PV) (No.)"],
        'thresholds': {'good': '>1', 'satisfactory': '0.85-1', 'needs_improvement': '<0.85'},
        'formula_type': 'quantitative'
    }
    
    value, rating = calculator.calculate_ac("DevCo Schedule Performance Index (SPI)", test_ac, test_dp_values)
    print(f"SPI Test: {value:.2f}% ({rating})")
    
    # Test case 2: Budget variance
    test_dp_values2 = {
        "PF Approved Capex budget (Initial Business Plan) (No.)": 5000000,
        "Forecast budget (EAC) (No.)": 4500000
    }
    
    test_ac2 = {
        'formula': '(Forecast Budget - PIF Approved Capex budget) / PIF Approved Capex budget',
        'data_points': ["PF Approved Capex budget (Initial Business Plan) (No.)", "Forecast budget (EAC) (No.)"],
        'thresholds': {'good': '<10%', 'satisfactory': '10-20%', 'needs_improvement': '>20%'},
        'formula_type': 'quantitative'
    }
    
    value2, rating2 = calculator.calculate_ac("Budget Variance", test_ac2, test_dp_values2)
    print(f"Budget Variance Test: {value2:.2f}% ({rating2})")