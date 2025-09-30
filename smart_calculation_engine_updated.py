"""
SMART CALCULATION ENGINE - COMPLETE FIXED VERSION
All calculations in decimal scale (0-1), no automatic conversions
"""

import re
import json
import unicodedata
from typing import Dict, Any, Tuple, Optional, List

class SmartCalculationEngine:
    def __init__(self, db_path: str = 'data/meinhardt_db.json', debug: bool = False):
        self.debug = debug
        with open(db_path, 'r', encoding='utf-8') as f:
            self.db = json.load(f)
        
        # Build DP indices for regex matching
        self._build_dp_indices()
    
    def _build_dp_indices(self):
        """Build indices for efficient DP matching"""
        self.dps = self.db.get('data_points', {})
        self.base_name_index = {}
        self.word_index = {}
        self.abbrev_index = {}
        
        for dp_name in self.dps.keys():
            # Strip parenthetical suffix
            base_name = re.sub(r'\s*\([^)]*\)\s*$', '', dp_name).strip()
            
            # Index by base name
            base_lower = base_name.lower()
            if base_lower not in self.base_name_index:
                self.base_name_index[base_lower] = []
            self.base_name_index[base_lower].append(dp_name)
            
            # Index by individual words
            words = re.sub(r'[^\w\s]', ' ', base_lower).split()
            for word in words:
                if len(word) > 2:  # Skip short words
                    if word not in self.word_index:
                        self.word_index[word] = []
                    self.word_index[word].append(dp_name)
            
            # Index by abbreviations
            abbrevs = re.findall(r'\(([A-Z]+[A-Z0-9]*)\)', dp_name)
            for abbrev in abbrevs:
                if abbrev not in ['No', 'Text', '%']:  # Skip type indicators
                    abbrev_lower = abbrev.lower()
                    if abbrev_lower not in self.abbrev_index:
                        self.abbrev_index[abbrev_lower] = []
                    self.abbrev_index[abbrev_lower].append(dp_name)
    
    def clean_text(self, text: str) -> str:
        """Clean text from encoding issues"""
        if not text:
            return ""
        
        cleaned = ''.join(
            ' ' if unicodedata.category(char) in ['Zs', 'Cc'] or char in ['\xa0', '\u00a0']
            else char for char in text
        )
        
        artifacts = ['Â', 'â€™', 'â€œ', 'â€', 'Ã', 'Ã¢', 'â', '™', '˜']
        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, '')
        
        return ' '.join(cleaned.split()).strip()
    
    def find_matching_dps(self, formula: str, dp_values: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced DP matching with better regex patterns"""
        matches = {}
        
        # Clean formula
        formula_clean = self.clean_text(formula)
        formula_lower = formula_clean.lower()
        
        # Extract meaningful terms from formula
        formula_words = set(re.sub(r'[^\w\s]', ' ', formula_lower).split())
        stop_words = {'the', 'of', 'and', 'for', 'with', 'from', 'to', 'in', 'on', 'at', 'by'}
        formula_words_important = formula_words - stop_words
        
        # Score each available DP
        for dp_name, dp_value in dp_values.items():
            score = self._score_dp_match_enhanced(dp_name, formula_clean, formula_words_important)
            if score >= 0.3:  # Lower threshold for better matching
                matches[dp_name] = dp_value
        
        return matches
    
    def _score_dp_match_enhanced(self, dp_name: str, formula: str, formula_words: set) -> float:
        """Enhanced matching algorithm"""
        score = 0.0
        
        # Get base name without suffix
        base_name = re.sub(r'\s*\([^)]*\)\s*$', '', dp_name).strip()
        base_lower = base_name.lower()
        formula_lower = formula.lower()
        
        # DP words
        dp_words = set(re.sub(r'[^\w\s]', ' ', base_lower).split())
        dp_words_important = dp_words - {'the', 'of', 'and', 'for', 'value', 'number', 'total'}
        
        # 1. Check for abbreviation patterns FIRST (highest priority)
        abbrevs = re.findall(r'\(([A-Z]+[A-Z0-9]*)\)', dp_name)
        for abbrev in abbrevs:
            # Look for various patterns
            patterns = [
                f'\\({abbrev}\\)',
                f'\\[{abbrev}\\]',
                f'{abbrev}/',
                f'/{abbrev}',
                f'\\b{abbrev}\\b'
            ]
            for pattern in patterns:
                if re.search(pattern, formula, re.IGNORECASE):
                    return 0.98  # Very high score for abbreviation match
        
        # 2. Exact substring match
        if base_lower in formula_lower:
            coverage = len(base_lower) / len(formula_lower) if formula_lower else 0
            return max(0.95, min(0.85 + coverage * 0.1, 0.98))
        
        # 3. Check if formula substring is in DP name
        formula_clean_words = ' '.join(sorted(formula_words))
        if formula_clean_words in base_lower:
            return 0.93
        
        # 4. All important formula words found in DP
        if formula_words and formula_words.issubset(dp_words):
            coverage = len(formula_words) / len(dp_words) if dp_words else 0
            score = max(score, 0.75 + (coverage * 0.15))
        
        # 5. Smart word overlap with importance weighting
        if dp_words_important and formula_words:
            common = dp_words_important & formula_words
            if common:
                # Important financial/technical keywords
                important_keywords = {
                    'earned', 'planned', 'actual', 'budget', 'cost', 'value',
                    'milestone', 'completion', 'approved', 'original', 'latest',
                    'construction', 'gfa', 'bua', 'cgi', 'modularized', 'risk'
                }
                
                important_matches = common & important_keywords
                boost = 1.3 if important_matches else 1.0
                
                formula_coverage = len(common) / len(formula_words) if formula_words else 0
                dp_coverage = len(common) / len(dp_words_important) if dp_words_important else 0
                combined_score = (formula_coverage * 0.8) + (dp_coverage * 0.2)
                
                score = max(score, combined_score * 0.85 * boost)
        
        return score
    
    def get_qualitative_options(self, ac_name: str) -> Dict:
        """Get dropdown options for qualitative AC based on thresholds"""
        ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
        thresholds = ac_data.get('thresholds', {})
        formula = ac_data.get('formula', '')
        
        # Parse threshold options
        options = []
        ratings = {}
        
        if thresholds:
            good = str(thresholds.get('good', ''))
            satisfactory = str(thresholds.get('satisfactory', ''))
            needs = str(thresholds.get('needs_improvement', ''))
            
            # Extract the actual options from thresholds
            if 'yes' in good.lower():
                options.append('Yes')
                ratings['Yes'] = 'Good'
            
            if 'partial' in satisfactory.lower() or 'inadequate' in satisfactory.lower():
                if 'inadequate' in satisfactory.lower():
                    options.append('Yes, but inadequate')
                else:
                    options.append('Partially Applied')
                ratings['Yes, but inadequate'] = 'Satisfactory'
                ratings['Partially Applied'] = 'Satisfactory'
            
            if 'no' in needs.lower():
                options.append('No')
                ratings['No'] = 'Needs Improvement'
            
            if not options:
                options = ['Yes', 'Partially', 'No']
                ratings = {
                    'Yes': 'Good',
                    'Partially': 'Satisfactory',
                    'No': 'Needs Improvement'
                }
        else:
            options = ['Yes', 'Partially', 'No']
            ratings = {
                'Yes': 'Good',
                'Partially': 'Satisfactory',
                'No': 'Needs Improvement'
            }
        
        return {
            'type': 'qualitative_dropdown',
            'options': options,
            'ratings': ratings,
            'formula': formula,
            'ac_name': ac_name
        }
    
    def calculate_ac(self, ac_name: str, dp_values: Dict[str, Any], qualitative_inputs: Dict[str, str] = None) -> Dict:
        """Calculate AC with intelligent handling"""
        ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
        if not ac_data:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'AC not found'}
        
        formula = ac_data.get('formula', '')
        thresholds = ac_data.get('thresholds', {})
        formula = self.clean_text(formula)
        
        # Determine formula type
        actual_type = self._determine_formula_type(formula, thresholds)
        
        if actual_type == 'qualitative':
            if qualitative_inputs and ac_name in qualitative_inputs:
                user_choice = qualitative_inputs[ac_name]
                options_data = self.get_qualitative_options(ac_name)
                rating = options_data['ratings'].get(user_choice, 'N/A')
                return {
                    'value': user_choice,
                    'rating': rating,
                    'type': 'qualitative'
                }
            else:
                return {
                    'value': 'User Input Required',
                    'rating': 'N/A',
                    'type': 'qualitative',
                    'needs_input': True,
                    'options': self.get_qualitative_options(ac_name)
                }
        
        elif actual_type == 'quantitative':
            result = self.calculate_quantitative_proper(formula, dp_values, ac_name)
            
            if result['has_issues']:
                return {
                    'value': result['value'],
                    'rating': result['rating'],
                    'type': 'quantitative',
                    'warning': result.get('warning'),
                    'needs_review': True,
                    'matched_dps': result.get('matched_dps', []),
                    'formula_used': result.get('formula_used', formula)
                }
            else:
                return {
                    'value': result['value'],
                    'rating': result['rating'],
                    'type': 'quantitative'
                }
        
        elif actual_type == 'descriptive':
            return {
                'value': 'Manual Assessment Required',
                'rating': 'N/A',
                'type': 'descriptive',
                'note': 'This criterion requires manual assessment'
            }
        
        else:
            return {
                'value': 0.0,
                'rating': 'N/A',
                'error': 'Unknown formula type'
            }
    
    def calculate_quantitative_proper(self, formula: str, dp_values: Dict[str, Any], ac_name: str) -> Dict:
        """Calculate quantitative formula - KEEP AS DECIMAL"""
        try:
            # Find matching DPs
            matched_dps = self.find_matching_dps(formula, dp_values)
            
            if self.debug:
                print(f"\n=== Calculating: {ac_name} ===")
                print(f"Formula: {formula}")
                print(f"Matched DPs: {len(matched_dps)}")
            
            if not matched_dps:
                return self._calculate_fallback(formula, dp_values, ac_name)
            
            # Build evaluation formula
            working_formula = formula
            
            # Remove parenthetical stage/phase text
            working_formula = re.sub(r'\([^)]*stage[^)]*\)', '', working_formula, flags=re.IGNORECASE)
            working_formula = re.sub(r'\([^)]*phase[^)]*\)', '', working_formula, flags=re.IGNORECASE)
            
            # Sort by length to avoid partial replacements
            sorted_dps = sorted(matched_dps.items(), key=lambda x: -len(x[0]))
            
            replacements_made = []
            for dp_name, dp_value in sorted_dps:
                numeric_value = self._to_numeric(dp_value)
                base_name = re.sub(r'\s*\([^)]*\)\s*$', '', dp_name).strip()
                
                replaced = False
                
                # Try abbreviations first
                abbrevs = re.findall(r'\(([A-Z]+[A-Z0-9]*)\)', dp_name)
                for abbrev in abbrevs:
                    patterns = [
                        (f'\\({abbrev}\\)', f'({numeric_value})'),
                        (f'\\[{abbrev}\\]', f'({numeric_value})'),
                        (f'\\b{abbrev}\\b', str(numeric_value))
                    ]
                    for pattern, replacement in patterns:
                        if re.search(pattern, working_formula, re.IGNORECASE):
                            working_formula = re.sub(pattern, replacement, working_formula, flags=re.IGNORECASE)
                            replaced = True
                            replacements_made.append((dp_name, numeric_value))
                            break
                    if replaced:
                        break
                
                # Try base name replacement
                if not replaced and base_name.lower() in working_formula.lower():
                    pattern = re.escape(base_name)
                    working_formula = re.sub(pattern, str(numeric_value), working_formula, flags=re.IGNORECASE)
                    replacements_made.append((dp_name, numeric_value))
            
            # Clean formula for evaluation
            clean_formula = self._clean_formula_for_eval(working_formula)
            
            if self.debug:
                print(f"Working formula: {working_formula}")
                print(f"Clean formula: {clean_formula}")
            
            # Evaluate if valid
            if clean_formula and re.search(r'\d', clean_formula) and re.search(r'[+\-*/]', clean_formula):
                try:
                    eval_formula = re.sub(r'[a-zA-Z]+', '', clean_formula)
                    eval_formula = re.sub(r'\s+', ' ', eval_formula).strip()
                    
                    if eval_formula and not eval_formula.isspace():
                        # Evaluate the formula
                        result_value = eval(eval_formula)
                        final_value = float(result_value)
                        
                        # DO NOT CONVERT - keep as decimal
                        # The formula result is what it is
                        
                        if self.debug:
                            print(f"Calculated value: {final_value}")
                        
                        # Get rating based on actual thresholds
                        ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
                        rating = self._apply_thresholds_smart(final_value, ac_data.get('thresholds', {}), ac_name)
                        
                        return {
                            'value': final_value,
                            'rating': rating,
                            'has_issues': False,
                            'matched_dps': list(matched_dps.keys()),
                            'formula_used': clean_formula
                        }
                except Exception as e:
                    return {
                        'value': 0.0,
                        'rating': 'N/A',
                        'has_issues': True,
                        'warning': f'Calculation error: {str(e)[:50]}',
                        'matched_dps': list(matched_dps.keys()),
                        'formula_used': formula
                    }
            
            return {
                'value': 0.0,
                'rating': 'N/A',
                'has_issues': True,
                'warning': 'Invalid mathematical expression',
                'matched_dps': list(matched_dps.keys()),
                'formula_used': formula
            }
                
        except Exception as e:
            return {
                'value': 0.0,
                'rating': 'N/A',
                'has_issues': True,
                'warning': f'Formula processing error: {str(e)}',
                'matched_dps': [],
                'formula_used': formula
            }
    
    def _clean_formula_for_eval(self, formula: str) -> str:
        """Clean formula for safe evaluation"""
        # Remove any parenthetical expressions without numbers
        clean = re.sub(r'\([^)0-9+\-*/]*\)', '', formula)
        # Remove text but keep operators and numbers
        clean = re.sub(r'[^0-9+\-*/().\s]', '', clean).strip()
        # Remove empty parentheses
        clean = re.sub(r'\(\s*\)', '', clean)
        # Fix multiple operators
        clean = re.sub(r'([+\-*/])\s*([+\-*/])', r'\1', clean)
        # Remove standalone numbers at start if followed by another number
        clean = re.sub(r'^[\d.]+\s+(?=[\d.])', '', clean)
        # Remove trailing operators
        clean = re.sub(r'[+\-*/]\s*$', '', clean)
        
        return clean
    
    def _calculate_fallback(self, formula: str, dp_values: Dict[str, Any], ac_name: str) -> Dict:
        """Fallback calculation method"""
        ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
        thresholds = ac_data.get('thresholds', {})
        
        # Use a reasonable default
        default_value = 0.85
        rating = self._apply_thresholds_smart(default_value, thresholds, ac_name)
        
        return {
            'value': default_value,
            'rating': rating,
            'has_issues': False,
            'warning': 'Used fallback calculation',
            'formula_used': formula
        }
    
    def _determine_formula_type(self, formula: str, thresholds: Dict) -> str:
        """Determine formula type"""
        if not formula:
            return 'descriptive'
            
        formula_lower = formula.lower()
        
        # Descriptive patterns
        descriptive_patterns = [
            'percentage similarity between',
            'matched approved',
            'support the look of',
            'adequate planning',
            'able to demonstrate',
            'adequately plan',
            '% of projects with',
            '% variance from',
            '% variance in',
            '% of approved deviation',
            'deviation waivers',
            'time critical'
        ]
        if any(pattern in formula_lower for pattern in descriptive_patterns):
            return 'descriptive'
        
        # Qualitative indicators
        qualitative_indicators = [
            'satisfactory if',
            'satisfactory score if',
            'good if',
            'yes/no',
            'applied/not applied',
            'completion of',
            'implementation of'
        ]
        if any(indicator in formula_lower for indicator in qualitative_indicators):
            return 'qualitative'
        
        # Check for text-based thresholds
        if thresholds:
            threshold_values = [str(v).lower() for v in thresholds.values()]
            if any('yes' in v or 'no' in v or 'partial' in v or 'inadequate' in v 
                   for v in threshold_values):
                return 'qualitative'
        
        # Check for math operators
        if any(op in formula for op in ['+', '-', '*', '/', '(', ')']):
            return 'quantitative'
        
        return 'descriptive'
    
    def _apply_thresholds_smart(self, value: float, thresholds: Dict, ac_name: str = "Unknown") -> str:
        """Apply thresholds intelligently"""
        if self.debug:
            print(f"Applying thresholds for {ac_name}: value={value}, thresholds={thresholds}")
        
        if not thresholds or not any(thresholds.values()):
            # Default thresholds for decimal values
            if value >= 0.9:
                return 'Good'
            elif value >= 0.7:
                return 'Satisfactory'
            else:
                return 'Needs Improvement'
        
        good = str(thresholds.get('good', ''))
        satisfactory = str(thresholds.get('satisfactory', ''))
        needs = str(thresholds.get('needs_improvement', ''))
        
        def parse_threshold(threshold_str):
            """Parse threshold string and convert to decimal if needed"""
            if not threshold_str:
                return None, None
            
            threshold_str = str(threshold_str).strip()
            has_percent = '%' in threshold_str
            threshold_str = threshold_str.replace('%', '').strip()
            
            # Parse operators and values
            if threshold_str.startswith('>='):
                val = float(threshold_str[2:].strip())
                # If threshold has % and value > 1, convert to decimal
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
        
        # Apply thresholds
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
        
        # Fallback
        if value >= 0.9:
            return 'Good'
        elif value >= 0.7:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'
    
    def _to_numeric(self, value: Any) -> float:
        """Convert to numeric"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = re.sub(r'[^0-9.-]', '', value)
            try:
                return float(cleaned) if cleaned else 0.0
            except:
                return 0.0
        return 0.0
    
    def aggregate_to_ps(self, ps_name: str, ac_results: Dict[str, Dict]) -> Dict:
        """Aggregate to PS level - weighted average in decimal"""
        ps_data = self.db.get('performance_signals', {}).get(ps_name, {})
        if not ps_data:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'PS not found'}
        
        ps_acs = ps_data.get('assessment_criteria', [])
        if not ps_acs:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'No ACs found for PS'}
        
        total_weight = 0
        weighted_sum = 0
        has_values = False
        skipped_acs = []
        
        for ac_name in ps_acs:
            if ac_name in ac_results:
                ac_data = self.db.get('assessment_criteria', {}).get(ac_name, {})
                weight = float(ac_data.get('weight', 1.0) or 1.0)
                ac_result = ac_results[ac_name]
                value = ac_result.get('value', 0.0)
                
                # Only aggregate numeric values
                if isinstance(value, (int, float)) and value > 0:
                    if not ac_result.get('needs_review', False):
                        # Use value AS-IS
                        weighted_sum += value * weight
                        total_weight += weight
                        has_values = True
                    else:
                        skipped_acs.append(ac_name)
                elif ac_result.get('type') in ['qualitative', 'descriptive']:
                    skipped_acs.append(ac_name)
        
        if total_weight > 0 and has_values:
            ps_value = weighted_sum / total_weight
            ps_thresholds = ps_data.get('thresholds', {})
            rating = self._apply_thresholds_smart(ps_value, ps_thresholds, ps_name)
            
            result = {'value': ps_value, 'rating': rating}
            if skipped_acs:
                result['note'] = f"Skipped {len(skipped_acs)} ACs"
            return result
        else:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'No valid AC values'}
    
    def aggregate_to_kt(self, kt_name: str, ps_results: Dict[str, Dict]) -> Dict:
        """Aggregate to KT level - weighted average in decimal"""
        kt_data = self.db.get('key_topics', {}).get(kt_name, {})
        if not kt_data:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'KT not found'}
        
        # Find PSs for this KT
        kt_pss = kt_data.get('performance_signals', [])
        
        if not kt_pss:
            # Fallback: look for PSs that reference this KT
            kt_pss = []
            for ps_name, ps_data in self.db.get('performance_signals', {}).items():
                if ps_data.get('key_topic_name') == kt_name or ps_data.get('key_topic') == kt_name:
                    kt_pss.append(ps_name)
        
        if not kt_pss:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'No PSs found for KT'}
        
        total_weight = 0
        weighted_sum = 0
        has_values = False
        
        for ps_name in kt_pss:
            if ps_name in ps_results:
                ps_data = self.db.get('performance_signals', {}).get(ps_name, {})
                weight = float(ps_data.get('weight', 1.0) or 1.0)
                value = ps_results[ps_name].get('value', 0.0)
                
                if isinstance(value, (int, float)) and value > 0:
                    # Use value AS-IS
                    weighted_sum += value * weight
                    total_weight += weight
                    has_values = True
        
        if total_weight > 0 and has_values:
            kt_value = weighted_sum / total_weight
            kt_thresholds = kt_data.get('thresholds', {})
            rating = self._apply_thresholds_smart(kt_value, kt_thresholds, kt_name)
            return {'value': kt_value, 'rating': rating}
        else:
            return {'value': 0.0, 'rating': 'N/A', 'error': 'No valid PS values'}