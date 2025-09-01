"""
Robust Formula Parser for Meinhardt WebApp
More accurate DP detection and formula evaluation
"""

import re
import ast
import operator
from typing import Dict, Any, Optional, Union, List, Tuple
import json

class FormulaParser:
    """Parse and evaluate formulas with robust detection"""
    
    def __init__(self):
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow
        }
        
        # Load database for thresholds
        try:
            with open('data/meinhardt_db.json', 'r') as f:
                self.database = json.load(f)
        except:
            self.database = {}
            
        # Debug mode
        self.debug = True
    
    def evaluate(self, formula: Optional[str], variables: Dict[str, Any], ac_name: str = None) -> Union[float, str]:
        """Main evaluation method with AC context"""
        if formula is None or formula == '' or not formula:
            return 0.0
            
        formula = str(formula).strip()
        
        if not formula:
            return 0.0
        
        if self.debug:
            print(f"\n=== Evaluating AC: {ac_name} ===")
            print(f"Formula: {formula}")
            print(f"Available variables: {list(variables.keys())[:5]}...")  # Show first 5
        
        if self._is_qualitative(formula):
            return self._evaluate_qualitative(formula, variables)
        else:
            return self._evaluate_quantitative(formula, variables)
    
    def _is_qualitative(self, formula: Optional[str]) -> bool:
        """Check if formula is qualitative"""
        if formula is None or not isinstance(formula, str) or not formula:
            return False
            
        formula_lower = formula.lower()
        
        # Mathematical operators strongly indicate quantitative
        math_operators = ['/', '*', '+', '-', '(', ')']
        has_math = any(op in formula for op in math_operators)
        
        # But some qualitative formulas might have these in their description
        # So check for strong qualitative indicators
        qual_keywords = [
            'compliance', 'status', 'applied', 'completed', 'implemented',
            'yes', 'no', 'partial', 'assessment', 'conducted', 'approved',
            'documented', 'established', 'defined', 'available', 'if', 'whether',
            'exists', 'review', 'robust', 'alignment', 'satisfactory score'
        ]
        
        has_qual = any(kw in formula_lower for kw in qual_keywords)
        
        # If it has math and no qual keywords, it's quantitative
        if has_math and not has_qual:
            return False
        
        # If it has qual keywords and no math, it's qualitative
        if has_qual and not has_math:
            return True
            
        # If both, lean towards quantitative unless strong qual indicators
        return has_qual and 'satisfactory score' in formula_lower
    
    def _evaluate_quantitative(self, formula: str, variables: Dict[str, Any]) -> float:
        """Evaluate mathematical formulas with improved matching"""
        try:
            # Step 1: Extract the actual variables needed from the formula
            needed_vars = self._extract_needed_variables(formula)
            
            if self.debug:
                print(f"Variables needed from formula: {needed_vars}")
            
            # Step 2: Map formula variables to actual DP names
            var_mapping = self._map_formula_to_dps(needed_vars, variables)
            
            if self.debug:
                print(f"Variable mapping: {var_mapping}")
            
            # Step 3: Replace variables in formula with values
            eval_formula = formula
            for formula_var, (dp_name, value) in var_mapping.items():
                numeric_value = self._to_numeric(value)
                # Replace the formula variable with the numeric value
                eval_formula = eval_formula.replace(formula_var, str(numeric_value))
                
            if self.debug:
                print(f"Formula after replacement: {eval_formula}")
            
            # Step 4: Clean and evaluate
            eval_formula = self._clean_for_eval(eval_formula)
            
            if self.debug:
                print(f"Clean formula: {eval_formula}")
            
            result = self._safe_eval(eval_formula)
            
            # Handle percentage conversion for ratios
            if '/' in formula and 0 < result <= 1:
                if any(x in formula.lower() for x in ['%', 'percent', 'index', 'rate']):
                    result = result * 100
            
            if self.debug:
                print(f"Result: {result}")
            
            return float(result)
            
        except Exception as e:
            if self.debug:
                print(f"Error evaluating formula: {e}")
            return 0.0
    
    def _extract_needed_variables(self, formula: str) -> List[str]:
        """Extract variable names that are actually in the formula"""
        needed = []
        
        # Pattern 1: Variables in parentheses like (EV), (PV)
        paren_pattern = r'\(([^)]+)\)'
        paren_matches = re.findall(paren_pattern, formula)
        needed.extend(paren_matches)
        
        # Pattern 2: Common variable patterns
        # Look for "Earned Value", "Planned Value", etc.
        common_vars = [
            'Earned Value', 'Planned Value',
            'Total number of projects',
            'Number of projects with approved change requests',
            'Total number of projects in design phase',
            'Total number of projects in construction phase',
            'Number of projects with forecast completion date',
            'milestones achieved on time',
            'planned milestones'
        ]
        
        for var in common_vars:
            if var in formula:
                needed.append(var)
        
        return needed
    
    def _map_formula_to_dps(self, needed_vars: List[str], available_dps: Dict[str, Any]) -> Dict[str, Tuple[str, Any]]:
        """Map formula variables to actual DP names"""
        mapping = {}
        
        for needed in needed_vars:
            needed_lower = needed.lower()
            
            # Try to find the best matching DP
            best_match = None
            best_score = 0
            
            for dp_name, dp_value in available_dps.items():
                dp_clean = dp_name.replace('(No.)', '').replace('(%)', '').strip()
                dp_lower = dp_clean.lower()
                
                # Exact match
                if needed_lower == dp_lower:
                    mapping[needed] = (dp_name, dp_value)
                    break
                
                # Check if needed is an abbreviation
                if len(needed) <= 3:  # Likely an abbreviation like EV, PV
                    # Check if DP contains this abbreviation
                    if f'({needed})' in dp_name or f' {needed} ' in dp_name:
                        mapping[needed] = (dp_name, dp_value)
                        break
                
                # Partial match scoring
                score = 0
                if needed_lower in dp_lower:
                    score = len(needed_lower) / len(dp_lower)
                elif dp_lower in needed_lower:
                    score = len(dp_lower) / len(needed_lower)
                
                # Check word overlap
                needed_words = set(needed_lower.split())
                dp_words = set(dp_lower.split())
                if needed_words & dp_words:
                    overlap = len(needed_words & dp_words) / max(len(needed_words), len(dp_words))
                    score = max(score, overlap)
                
                if score > best_score:
                    best_score = score
                    best_match = (dp_name, dp_value)
            
            # Use best match if good enough
            if best_match and best_score > 0.5:
                mapping[needed] = best_match
        
        return mapping
    
    def _clean_for_eval(self, formula: str) -> str:
        """Clean formula for evaluation"""
        cleaned = formula
        
        # Remove text that's definitely not part of the calculation
        text_to_remove = [
            'Number of', 'No. of', 'Total', 'with', 'since', 'phase',
            'inception', 'time', 'impact', 'more than', 'less than',
            'month', 'months', 'in accordance', 'approved', 'latest',
            'projects', 'milestones', 'achieved', 'planned', 'beyond',
            'forecast', 'completion', 'date', 'schedule'
        ]
        
        for text in text_to_remove:
            cleaned = re.sub(r'\b' + re.escape(text) + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        # Remove any remaining text (keep only numbers and operators)
        cleaned = re.sub(r'[^\d\s+\-*/().]', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        # Handle division by zero
        if '/' in cleaned:
            parts = cleaned.split('/')
            if len(parts) == 2:
                try:
                    denominator = float(parts[1].strip())
                    if denominator == 0:
                        return '0'
                except:
                    pass
        
        return cleaned
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        try:
            if not expression or expression.strip() == '':
                return 0.0
            
            # Try direct evaluation first
            tree = ast.parse(expression, mode='eval')
            result = self._eval_node(tree.body)
            return float(result)
        except:
            # Try simpler evaluation
            try:
                # Handle simple division
                if '/' in expression and expression.count('/') == 1:
                    parts = expression.split('/')
                    numerator = float(parts[0].strip()) if parts[0].strip() else 0
                    denominator = float(parts[1].strip()) if parts[1].strip() else 1
                    if denominator != 0:
                        return numerator / denominator
                    return 0.0
                
                # Try direct float conversion
                return float(expression)
            except:
                return 0.0
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes"""
        if isinstance(node, (ast.Constant, ast.Num)):
            return node.value if hasattr(node, 'value') else node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                return 0
            return self.operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            elif isinstance(node.op, ast.USub):
                return -operand
        else:
            return 0.0
    
    def _to_numeric(self, value: Any) -> float:
        """Convert value to numeric"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Handle percentage strings
            if '%' in value:
                cleaned = value.replace('%', '').replace(',', '').strip()
                try:
                    return float(cleaned)
                except:
                    return 0.0
            else:
                cleaned = value.replace(',', '').strip()
                try:
                    return float(cleaned)
                except:
                    return 0.0
        return 0.0
    
    def _evaluate_qualitative(self, formula: str, variables: Dict[str, Any]) -> str:
        """Evaluate text-based formulas"""
        if variables:
            # For qualitative, we typically just need the first relevant value
            value = list(variables.values())[0] if variables else "N/A"
            
            if isinstance(value, str):
                value_lower = value.lower()
                
                # Map various inputs to standard outputs
                if value_lower in ['yes', 'true', 'completed', 'applied', 'full', 'fully']:
                    return 'Yes'
                elif value_lower in ['no', 'false', 'not completed', 'not applied', 'none']:
                    return 'No'
                elif value_lower in ['partial', 'partially', 'in progress', 'some', 'partly']:
                    return 'Partially Applied'
                
                # Return original if no mapping
                return value
        
        return "N/A"
    
    def extract_variables_for_formula(self, formula: str, all_variables: Dict[str, Any]) -> List[str]:
        """Extract which variables are actually used in a formula - for display purposes"""
        if not formula:
            return []
        
        # Get the variables we think are needed
        needed_vars = self._extract_needed_variables(formula)
        
        # Map them to actual DP names
        var_mapping = self._map_formula_to_dps(needed_vars, all_variables)
        
        # Return the actual DP names that were matched
        used_dps = []
        for formula_var, (dp_name, _) in var_mapping.items():
            if dp_name not in used_dps:
                used_dps.append(dp_name)
        
        return used_dps
    
    def get_rating_for_ac(self, ac_name: str, value: float, is_qualitative: bool = False) -> str:
        """Get rating based on AC-specific thresholds"""
        if is_qualitative:
            if value >= 100:
                return 'Good'
            elif value >= 50:
                return 'Satisfactory'
            else:
                return 'Needs Improvement'
        
        # Try to get AC-specific thresholds from database
        ac_data = self.database.get('assessment_criteria', {}).get(ac_name, {})
        thresholds = ac_data.get('thresholds', {})
        
        if thresholds:
            # Parse thresholds (they might be in various formats)
            good = thresholds.get('good', '')
            satisfactory = thresholds.get('satisfactory', '')
            needs = thresholds.get('needs_improvement', '')
            
            # Try to extract numeric thresholds
            try:
                # Handle different threshold formats
                if '>' in str(good):
                    good_val = float(re.findall(r'[\d.]+', str(good))[0])
                    if value > good_val:
                        return 'Good'
                elif good and isinstance(good, (int, float)):
                    if value >= float(good):
                        return 'Good'
                
                if satisfactory:
                    if '-' in str(satisfactory):
                        parts = re.findall(r'[\d.]+', str(satisfactory))
                        if len(parts) == 2:
                            if float(parts[0]) <= value <= float(parts[1]):
                                return 'Satisfactory'
                    elif isinstance(satisfactory, (int, float)):
                        if value >= float(satisfactory):
                            return 'Satisfactory'
                
                # If we get here, it's Needs Improvement
                return 'Needs Improvement'
                
            except:
                # Fall back to default thresholds
                pass
        
        # Default thresholds
        if value >= 85:
            return 'Good'
        elif value >= 70:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'


class QualitativeDropdownHandler:
    """Handle qualitative assessments with smart dropdowns"""
    
    def __init__(self):
        self.qualitative_mappings = {
            'compliance': {
                'options': ['Fully Compliant', 'Partially Compliant', 'Non-Compliant'],
                'scores': {'Fully Compliant': 100, 'Partially Compliant': 50, 'Non-Compliant': 0}
            },
            'status': {
                'options': ['Completed', 'In Progress', 'Not Started'],
                'scores': {'Completed': 100, 'In Progress': 50, 'Not Started': 0}
            },
            'applied': {
                'options': ['Yes', 'Partially Applied', 'No'],
                'scores': {'Yes': 100, 'Partially Applied': 50, 'No': 0}
            },
            'assessment': {
                'options': ['Conducted', 'Partially Conducted', 'Not Conducted'],
                'scores': {'Conducted': 100, 'Partially Conducted': 50, 'Not Conducted': 0}
            },
            'documented': {
                'options': ['Fully Documented', 'Partially Documented', 'Not Documented'],
                'scores': {'Fully Documented': 100, 'Partially Documented': 50, 'Not Documented': 0}
            },
            'default': {
                'options': ['Yes', 'Partial', 'No'],
                'scores': {'Yes': 100, 'Partial': 50, 'No': 0}
            }
        }
    
    def get_dropdown_options(self, formula: str, thresholds: Dict = None) -> Tuple[List[str], Dict[str, float]]:
        """Get appropriate dropdown options based on formula"""
        formula_lower = formula.lower() if formula else ''
        
        # Check for specific keywords to determine type
        for keyword, mapping in self.qualitative_mappings.items():
            if keyword in formula_lower and keyword != 'default':
                return mapping['options'], mapping['scores']
        
        # Check thresholds for custom options
        if thresholds:
            good = thresholds.get('good', '')
            sat = thresholds.get('satisfactory', '')
            needs = thresholds.get('needs_improvement', '')
            
            # If thresholds contain text options, use them
            if isinstance(good, str) and not any(c in good for c in ['>', '<', '%', '.']):
                options = [good, sat, needs]
                scores = {good: 100, sat: 50, needs: 0}
                return options, scores
        
        # Default
        return self.qualitative_mappings['default']['options'], self.qualitative_mappings['default']['scores']
    
    def evaluate_selection(self, selection: str, score_mapping: Dict[str, float]) -> Tuple[float, str]:
        """Evaluate a dropdown selection to get score and rating"""
        score = score_mapping.get(selection, 0)
        
        if score >= 85:
            rating = 'Good'
        elif score >= 50:
            rating = 'Satisfactory'
        else:
            rating = 'Needs Improvement'
        
        return score, rating


class WeightedAggregator:
    """Fixed aggregator that properly calculates weighted averages"""
    
    def aggregate_to_ps(self, ps_data: Dict[str, Any], ac_results: Dict[str, Any], 
                   all_acs: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate AC results to PS level with proper weighted average"""
        
        # The PS name is in ps_data
        ps_name = ps_data.get('name', '')
        
        # Find weights from all_acs for each AC in ac_results
        weighted_sum = 0
        total_weight = 0
        
        for ac_name, ac_result in ac_results.items():
            # Get the AC's metadata
            ac_metadata = all_acs.get(ac_name, {})
            ac_weight = ac_metadata.get('weight', 0)
            ac_value = ac_result.get('value', 0)
            
            # Cap at 100 and calculate
            ac_value = min(float(ac_value), 100)
            if ac_weight > 0:
                weighted_sum += ac_value * (ac_weight / 100)
                total_weight += ac_weight / 100
        
        # Calculate final PS value
        if total_weight > 0:
            ps_value = weighted_sum / total_weight
        else:
            # Simple average if no weights
            values = [r.get('value', 0) for r in ac_results.values()]
            ps_value = sum(values) / len(values) if values else 0
        
        ps_value = min(ps_value, 100)
        
        return {
            'value': ps_value,
            'display_value': f"{ps_value:.2f}%",
            'rating': self._get_rating(ps_value),
            'ac_count': len(ac_results),
            'status': 'calculated'
        }
    
    def aggregate_to_kt(self, kt_data: Dict[str, Any], ps_results: Dict[str, Any],
                   all_pss: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate PS results to KT level with proper weighted average"""
        
        weighted_sum = 0
        total_weight = 0
        
        for ps_name, ps_result in ps_results.items():
            # Get the PS's metadata
            ps_metadata = all_pss.get(ps_name, {})
            ps_weight = ps_metadata.get('weight', 0)
            ps_value = ps_result.get('value', 0)
            
            # Cap at 100 and calculate
            ps_value = min(float(ps_value), 100)
            if ps_weight > 0:
                weighted_sum += ps_value * (ps_weight / 100)
                total_weight += ps_weight / 100
        
        # Calculate final KT value
        if total_weight > 0:
            kt_value = weighted_sum / total_weight
        else:
            # Simple average if no weights
            values = [r.get('value', 0) for r in ps_results.values()]
            kt_value = sum(values) / len(values) if values else 0
        
        kt_value = min(kt_value, 100)
        
        return {
            'value': kt_value,
            'display_value': f"{kt_value:.2f}%",
            'rating': self._get_rating(kt_value),
            'ps_count': len(ps_results),
            'status': 'calculated'
        }
    
    def calculate_overall(self, kt_results: Dict[str, Any]) -> float:
        """Calculate overall score as simple average of KT values"""
        if not kt_results:
            return 0
        
        values = []
        for kt_result in kt_results.values():
            if isinstance(kt_result, dict) and 'value' in kt_result:
                value = kt_result['value']
                if isinstance(value, (int, float)):
                    values.append(min(value, 100))  # Cap at 100
        
        return sum(values) / len(values) if values else 0
    
    def _get_rating(self, value: float) -> str:
        """Get rating based on value"""
        if value >= 85:
            return "Good"
        elif value >= 70:
            return "Satisfactory"
        else:
            return "Needs Improvement"