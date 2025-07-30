# Core WebApp Framework
streamlit==1.35.0

# Data handling and logic
pandas==2.2.2
numpy==1.26.4

# Database and ORM
SQLAlchemy==2.0.30
sqlite-utils==3.36  # Optional but useful if working with SQLite CLI

# Regex and fuzzy matching
regex==2024.5.15
fuzzywuzzy==0.18.0
python-Levenshtein==0.25.1  # Required by fuzzywuzzy for performance

# Authentication
streamlit-authenticator==0.3.1  # Update this if you installed a newer fork

# Formula Parsing and Evaluation
numexpr==2.9.0  # Optional, if we use it to safely evaluate formulas

# File handling
openpyxl==3.1.2  # For Excel file parsing
xlsxwriter==3.2.0  # For Excel export formatting

# JSON logic and config parsing
python-dotenv==1.0.1  # If you use .env for secrets

# Utility packages (used in dev or analysis)
tabulate==0.9.0  # Optional, for clean terminal table output
Jinja2==3.1.4    # Optional, if needed for templated output generation
