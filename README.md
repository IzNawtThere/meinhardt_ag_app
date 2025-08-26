# Meinhardt Assessment Guide WebApp

Streamlit application for Meinhardt Singapore assessment management.

## How to Run
1. Install Python 3.9+
2. Install requirements: `pip install streamlit pandas openpyxl numpy`
3. Run: `streamlit run app.py`

## Features
- Excel file parsing
- Assessment criteria management  
- Formula calculations
- Hierarchical scoring
- Professional reporting

## Modules
- `app.py` - Main application
- `master_file_module.py` - Configuration management
- `main_ag_module.py` - Assessment calculations
- `parsers/excel_parser.py` - Excel parsing
- `database/json_db.py` - Database handler
