"""
IMPROVED TEST LOADER
Better test data generation
"""

import random

def generate_better_test_values(db):
    """Generate more realistic test values"""
    test_values = {}
    
    # Critical mappings that must be exact
    critical = {
        "Earned Value (EV) (No.)": 3089866.13,
        "Planned Value (PV) (No.)": 9895243.49,
        "No. of milestones achieved on time (No.)": 85,
        "No. of planned milestones (No.)": 100,
        "Number of Controlled Risks (No.)": 45,
        "Total number of identified risks (No.)": 75,
        "Value of Modularized Construction Cost (No.)": 500000,
        "Value of Total Construction Cost (No.)": 2000000,
    }
    
    for dp_name, dp_info in db.get('data_points', {}).items():
        if dp_name in critical:
            test_values[dp_name] = critical[dp_name]
        else:
            data_type = dp_info.get('data_type', 'text')
            
            if data_type == 'number':
                test_values[dp_name] = random.uniform(100, 10000)
            elif data_type == 'percentage':
                test_values[dp_name] = random.uniform(70, 95)
            elif data_type == 'boolean':
                test_values[dp_name] = random.choice(['Yes', 'Yes', 'No'])
            else:
                test_values[dp_name] = 'Completed'
    
    return test_values

def auto_fill_qualitative(ac_results):
    """Auto-fill qualitative inputs"""
    qual_inputs = {}
    
    for ac_name, result in ac_results.items():
        if result.get('type') == 'qualitative' and result.get('needs_input'):
            options = result.get('options', {}).get('options', [])
            if options:
                # Favor positive responses
                if 'Yes' in options:
                    qual_inputs[ac_name] = 'Yes'
                elif options:
                    qual_inputs[ac_name] = options[0]
    
    return qual_inputs