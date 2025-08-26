# database/json_db.py
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import shutil

class JsonDatabase:
    """JSON-based database for Meinhardt WebApp"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.db_file = self.data_dir / "meinhardt_db.json"
        self.backup_dir = self.data_dir / "backups"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Initialize database structure
        self.init_database()
    
    def init_database(self):
        """Initialize or load existing database"""
        if not self.db_file.exists():
            # Create new database structure
            initial_db = {
                "metadata": {
                    "version": "1.0",
                    "created_at": datetime.now().isoformat(),
                    "last_modified": datetime.now().isoformat()
                },
                "key_topics": {},
                "performance_signals": {},
                "assessment_criteria": {},
                "data_points": {},
                "relationships": {
                    "kt_to_ps": {},
                    "ps_to_ac": {},
                    "ac_to_dp": {}
                },
                "thresholds": {},
                "assessments": {},
                "statistics": {
                    "total_dps": 0,
                    "total_acs": 0,
                    "total_pss": 0,
                    "total_kts": 0
                }
            }
            self.save_database(initial_db)
            print(f"Created new database at {self.db_file}")
        else:
            print(f"Loaded existing database from {self.db_file}")
    
    def load_database(self) -> Dict:
        """Load database from JSON file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return {}
    
    def save_database(self, data: Dict) -> bool:
        """Save database to JSON file"""
        try:
            # Update metadata
            if "metadata" not in data:
                data["metadata"] = {}
            data["metadata"]["last_modified"] = datetime.now().isoformat()
            
            # Create backup before saving
            if self.db_file.exists():
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.backup_dir / backup_name
                shutil.copy(self.db_file, backup_path)
                
                # Keep only last 5 backups
                self._cleanup_old_backups()
            
            # Save database
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            return True
        except Exception as e:
            print(f"Error saving database: {e}")
            return False
    
    def _cleanup_old_backups(self, keep_count: int = 5):
        """Keep only the most recent backups"""
        backups = sorted(self.backup_dir.glob("backup_*.json"))
        if len(backups) > keep_count:
            for backup in backups[:-keep_count]:
                backup.unlink()
    
    def clear_database(self):
        """Clear all data and reset database"""
        initial_db = {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            },
            "key_topics": {},
            "performance_signals": {},
            "assessment_criteria": {},
            "data_points": {},
            "relationships": {
                "kt_to_ps": {},
                "ps_to_ac": {},
                "ac_to_dp": {}
            },
            "thresholds": {},
            "assessments": {},
            "statistics": {
                "total_dps": 0,
                "total_acs": 0,
                "total_pss": 0,
                "total_kts": 0
            }
        }
        self.save_database(initial_db)
        print("Database cleared and reset")
    
    def save_parsed_data(self, parsed_data: Dict[str, Any]) -> bool:
        """Save parsed Excel data to JSON database"""
        try:
            # Load existing database
            db = self.load_database()
            
            # Clear existing data structures
            db["key_topics"] = {}
            db["performance_signals"] = {}
            db["assessment_criteria"] = {}
            db["data_points"] = {}
            db["relationships"] = parsed_data.get('relationships', {})
            db["thresholds"] = {}
            
            hierarchy = parsed_data.get('hierarchy', {})
            
            # Process each type of data - handle both dict and object formats
            for kt_name, kt_data in hierarchy.get('key_topics', {}).items():
                if isinstance(kt_data, dict):
                    db["key_topics"][kt_name] = kt_data
                else:
                    # It's an object with attributes
                    db["key_topics"][kt_name] = {
                        "code": getattr(kt_data, 'code', ''),
                        "name": getattr(kt_data, 'name', kt_name),
                        "pillar": getattr(kt_data, 'pillar', ''),
                        "performance_signals": getattr(kt_data, 'performance_signals', [])
                    }
            
            for ps_name, ps_data in hierarchy.get('performance_signals', {}).items():
                if isinstance(ps_data, dict):
                    db["performance_signals"][ps_name] = ps_data
                else:
                    db["performance_signals"][ps_name] = {
                        "code": getattr(ps_data, 'code', ''),
                        "name": getattr(ps_data, 'name', ps_name),
                        "weight": getattr(ps_data, 'weight', 0),
                        "key_topic_name": getattr(ps_data, 'key_topic_name', ''),
                        "assessment_criteria": getattr(ps_data, 'assessment_criteria', [])
                    }
            
            for ac_name, ac_data in hierarchy.get('assessment_criteria', {}).items():
                if isinstance(ac_data, dict):
                    db["assessment_criteria"][ac_name] = ac_data
                    if 'thresholds' in ac_data and ac_data['thresholds']:
                        db["thresholds"][ac_name] = ac_data['thresholds']
                else:
                    db["assessment_criteria"][ac_name] = {
                        "code": getattr(ac_data, 'code', ''),
                        "name": getattr(ac_data, 'name', ac_name),
                        "formula": getattr(ac_data, 'formula', ''),
                        "formula_type": getattr(ac_data, 'formula_type', 'qualitative'),
                        "weight": getattr(ac_data, 'weight', 0),
                        "performance_signal_name": getattr(ac_data, 'performance_signal_name', ''),
                        "data_points": getattr(ac_data, 'data_points', []),
                        "thresholds": getattr(ac_data, 'thresholds', {})
                    }
                    if hasattr(ac_data, 'thresholds') and ac_data.thresholds:
                        db["thresholds"][ac_name] = ac_data.thresholds
            
            for dp_name, dp_data in hierarchy.get('data_points', {}).items():
                if isinstance(dp_data, dict):
                    db["data_points"][dp_name] = dp_data
                else:
                    db["data_points"][dp_name] = {
                        "code": getattr(dp_data, 'code', ''),
                        "name": getattr(dp_data, 'name', dp_name),
                        "pillar": getattr(dp_data, 'pillar', ''),
                        "data_type": getattr(dp_data, 'data_type', 'text'),
                        "display_name": getattr(dp_data, 'display_name', None) or getattr(dp_data, 'name', dp_name)
                    }
            
            # Update statistics
            db["statistics"] = {
                "total_dps": len(db["data_points"]),
                "total_acs": len(db["assessment_criteria"]),
                "total_pss": len(db["performance_signals"]),
                "total_kts": len(db["key_topics"]),
                "last_import": datetime.now().isoformat()
            }
            
            # Save to file
            success = self.save_database(db)
            
            if success:
                print(f"Successfully saved:")
                print(f"   - {db['statistics']['total_dps']} Data Points")
                print(f"   - {db['statistics']['total_acs']} Assessment Criteria")
                print(f"   - {db['statistics']['total_pss']} Performance Signals")
                print(f"   - {db['statistics']['total_kts']} Key Topics")
            
            return success
            
        except Exception as e:
            print(f"Error saving parsed data: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the database"""
        db = self.load_database()
        return db.get("statistics", {})
    
    def get_all_data_points(self) -> List[Dict]:
        """Get all data points"""
        db = self.load_database()
        return list(db.get("data_points", {}).values())
    
    def get_all_assessment_criteria(self) -> List[Dict]:
        """Get all assessment criteria"""
        db = self.load_database()
        return list(db.get("assessment_criteria", {}).values())
    
    def get_data_points_by_pillar(self, pillar: str) -> List[Dict]:
        """Get data points for a specific pillar"""
        db = self.load_database()
        dps = []
        for dp in db.get("data_points", {}).values():
            if dp.get("pillar") == pillar:
                dps.append(dp)
        return dps
    
    def search_data_points(self, search_term: str) -> List[Dict]:
        """Search data points by name"""
        db = self.load_database()
        results = []
        search_lower = search_term.lower()
        
        for dp in db.get("data_points", {}).values():
            if search_lower in dp.get("name", "").lower():
                results.append(dp)
        
        return results
    
    def export_to_excel(self, output_path: str) -> bool:
        """Export database to Excel format"""
        try:
            import pandas as pd
            
            db = self.load_database()
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Export Data Points
                if db.get("data_points"):
                    df_dp = pd.DataFrame.from_dict(db["data_points"], orient='index')
                    df_dp.to_excel(writer, sheet_name='Data Points', index=False)
                
                # Export Assessment Criteria
                if db.get("assessment_criteria"):
                    df_ac = pd.DataFrame.from_dict(db["assessment_criteria"], orient='index')
                    df_ac.to_excel(writer, sheet_name='Assessment Criteria', index=False)
                
                # Export Performance Signals
                if db.get("performance_signals"):
                    df_ps = pd.DataFrame.from_dict(db["performance_signals"], orient='index')
                    df_ps.to_excel(writer, sheet_name='Performance Signals', index=False)
                
                # Export Key Topics
                if db.get("key_topics"):
                    df_kt = pd.DataFrame.from_dict(db["key_topics"], orient='index')
                    df_kt.to_excel(writer, sheet_name='Key Topics', index=False)
                
                # Export Statistics
                if db.get("statistics"):
                    df_stats = pd.DataFrame([db["statistics"]])
                    df_stats.to_excel(writer, sheet_name='Statistics', index=False)
            
            print(f"Exported database to {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False