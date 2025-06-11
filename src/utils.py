import json
import logging
import re
from typing import Any, Dict
from datetime import datetime
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Configure logging for the scraper."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("scraper.log"),
            logging.StreamHandler()
        ]
    )

def validate_match_url(url: str) -> bool:
    """
    Validate that the URL is a proper WhoScored match URL.
    """
    pattern = r"^https://www\.whoscored\.com/matches/\d+/live/.+"
    return re.match(pattern, url) is not None

def clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and normalize extracted data from WhoScored.
    """
    if not isinstance(data, dict):
        return {}
    cleaned = {}
    for key, value in data.items():
        # Skip error flags
        if key == "error" and value is False:
            continue
        # Clean string values
        if isinstance(value, str):
            value = value.strip()
            if value.lower() in ['n/a', 'null', 'none', '']:
                value = None
        # Clean numerical strings
        elif isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit():
            try:
                value = float(value) if '.' in value else int(value)
            except ValueError:
                pass
        # Recursively clean nested dictionaries
        elif isinstance(value, dict):
            value = clean_extracted_data(value)
        # Clean lists
        elif isinstance(value, list):
            value = [clean_extracted_data(item) if isinstance(item, dict) else item \
                    for item in value if item is not None]
        if value is not None:
            cleaned[key] = value
    return cleaned

def handle_extraction_error(error: Exception, attempt: int) -> str:
    """
    Handle and format extraction errors.
    """
    error_type = type(error).__name__
    error_message = str(error)
    return f"Attempt {attempt} failed - {error_type}: {error_message}"

def format_timeline_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format raw extracted data into structured timeline format.
    """
    formatted = {
        "match_info": {},
        "timeline_data": [],
        "summary_stats": {}
    }
    # Extract basic match info
    if "match_info" in raw_data:
        formatted["match_info"] = raw_data["match_info"]
    elif any(key in raw_data for key in ["home_team", "away_team", "score"]):
        # Try to extract match info from top level
        formatted["match_info"] = {
            k: raw_data.get(k) for k in ["home_team", "away_team", "score", "date", "competition"] if k in raw_data
        }
    # Timeline data
    if "timeline" in raw_data:
        formatted["timeline_data"] = raw_data["timeline"]
    elif "timeline_data" in raw_data:
        formatted["timeline_data"] = raw_data["timeline_data"]
    # Summary stats
    if "summary_stats" in raw_data:
        formatted["summary_stats"] = raw_data["summary_stats"]
    elif "stats" in raw_data:
        formatted["summary_stats"] = raw_data["stats"]
    return formatted

def save_data_to_json(data: Any, filename: str) -> bool:
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON: {e}")
        return False

def create_summary_report(data: Any) -> str:
    # Placeholder for summary creation logic
    return "Summary report generated."
