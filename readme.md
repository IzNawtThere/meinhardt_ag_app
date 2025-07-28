# Meinhardt AG App

A modular Streamlit-based WebApp replacing Excel-based Assessment Guide (AG) workflows for Meinhardt Singapore.

## Project Overview

This app digitizes the legacy Excel system for project evaluation and assessment into a streamlined, database-backed web interface.

**Core features include:**
- Dynamic DevCo input entry
- Formula-based scoring engine using human-readable logic
- Auto-rating via thresholds
- Real-time audit logs and historical tracking
- Modular Excel AG versioning
- SQLite backend with SQLAlchemy
- Future-ready for Power BI/dashboarding extensions

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit app |
| `analyze_ag.py` / `analyze_ag_rebuilt.py` | Scoring logic engine |
| `devco_entry.py` | DevCo input interface |
| `init_db.py`, `db.py` | Database setup & connection |
| `assessment_matrix.xlsx` | Central criteria + formulas |
| `auth.py` | Login/authentication |
| `utils.py` | Shared helper functions |
| `version_control.py` | AG version management |

## Technologies Used
- Python
- Streamlit
- SQLite + SQLAlchemy
- pandas
- Regex + dynamic formula parsing

## Future Enhancements
- Full dashboard integration via Power BI
- Admin-side AG designer UI
- External DevCo submission portals
