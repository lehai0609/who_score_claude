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

def clean_extracted_data(data: Any) -> Dict[str, Any]:
    """
    Clean and normalize extracted data from WhoScored.
    Handles both dictionary and list formats.
    """
    print(f"🔍 Input data type: {type(data)}")
    
    # Handle list data (convert to dictionary format)
    if isinstance(data, list):
        print(f"📋 Processing list with {len(data)} items")
        
        # If it's a list of dictionaries, try to structure it
        if data and isinstance(data[0], dict):
            cleaned = {
                "extracted_items": data,
                "match_data": {},
                "timeline_events": []
            }
            
            # Try to extract match info from the first item
            first_item = data[0]
            for key, value in first_item.items():
                if any(keyword in str(key).lower() for keyword in ['match', 'team', 'score', 'game']):
                    cleaned["match_data"][key] = value
                elif any(keyword in str(key).lower() for keyword in ['timeline', 'event', 'minute', 'time']):
                    cleaned["timeline_events"].append({key: value})
            
            print(f"✅ Converted list to structured format with {len(cleaned)} sections")
            return cleaned
        
        # If it's a simple list, wrap it
        else:
            cleaned = {
                "extracted_data": data,
                "data_type": "list",
                "item_count": len(data)
            }
            print(f"✅ Wrapped simple list with {len(data)} items")
            return cleaned
    
    # Handle dictionary data (original logic)
    elif isinstance(data, dict):
        print(f"📊 Processing dictionary with {len(data)} top-level keys: {list(data.keys())}")
        cleaned = {}
    
    # Handle other data types
    else:
        print(f"⚠️ Unexpected data type: {type(data)}")
        return {
            "raw_data": str(data),
            "data_type": str(type(data)),
            "extraction_note": "Data was not in expected format but has been preserved"
        }
    
    # Continue processing for dictionary data
    if isinstance(data, dict):
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
                value = [clean_extracted_data(item) if isinstance(item, dict) else item 
                        for item in value if item is not None]
            
            if value is not None:
                cleaned[key] = value
        
        print(f"✅ Cleaned dictionary data has {len(cleaned)} keys")
    
    return cleaned

def handle_extraction_error(error: Exception, attempt: int) -> str:
    """
    Handle and format extraction errors.
    """
    error_type = type(error).__name__
    error_message = str(error)
    return f"Attempt {attempt} failed - {error_type}: {error_message}"

def format_timeline_data(raw_data: Any) -> Dict[str, Any]:
    """
    Format raw extracted data into structured timeline format.
    Handles both dictionary and list inputs.
    """
    print(f"📊 Formatting data type: {type(raw_data)}")
    
    formatted = {
        "match_info": {},
        "timeline_data": [],
        "summary_stats": {},
        "raw_extracted_data": raw_data  # Keep the original data for debugging
    }
    
    # Handle list input
    if isinstance(raw_data, list):
        print(f"📋 Processing list with {len(raw_data)} items")
        formatted["timeline_data"] = raw_data
        
        # Try to extract match info from list items
        for item in raw_data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if any(keyword in str(key).lower() for keyword in ['match', 'team', 'score', 'home', 'away']):
                        formatted["match_info"][key] = value
    
    # Handle dictionary input (original logic)
    elif isinstance(raw_data, dict):
        print(f"📊 Processing dictionary with keys: {list(raw_data.keys())}")
        
        # Extract basic match info
        if "match_info" in raw_data:
            formatted["match_info"] = raw_data["match_info"]
        elif any(key in raw_data for key in ["home_team", "away_team", "score"]):
            # Try to extract match info from top level
            formatted["match_info"] = {
                k: raw_data.get(k) for k in ["home_team", "away_team", "score", "date", "competition"] if k in raw_data
            }
        
        # Timeline data
        if "timeline_ratings" in raw_data:
            formatted["timeline_data"] = raw_data["timeline_ratings"]
        elif "timeline_data" in raw_data:
            formatted["timeline_data"] = raw_data["timeline_data"]
        elif "timeline" in raw_data:
            formatted["timeline_data"] = raw_data["timeline"]
        elif "events" in raw_data:
            formatted["timeline_data"] = raw_data["events"]
        elif "extracted_items" in raw_data:
            formatted["timeline_data"] = raw_data["extracted_items"]
        
        # Summary stats
        if "summary_stats" in raw_data:
            formatted["summary_stats"] = raw_data["summary_stats"]
        elif "stats" in raw_data:
            formatted["summary_stats"] = raw_data["stats"]
        elif "team_stats" in raw_data:
            formatted["summary_stats"] = raw_data["team_stats"]
    
    # Handle other data types
    else:
        formatted["raw_extracted_data"] = str(raw_data)
        formatted["data_type"] = str(type(raw_data))
    
    # Add extraction metadata
    formatted["extraction_metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "scraper_version": "1.0.1",
        "source": "WhoScored.com",
        "crawl4ai_version": "0.6.3",
        "extraction_success": True,
        "original_data_type": str(type(raw_data)),
        "data_structure": str(type(raw_data).__name__)
    }
    
    print(f"✅ Formatted data structure complete")
    return formatted

def save_data_to_json(data: Any, filename: str) -> bool:
    """
    Save extracted data to JSON file with detailed logging.
    """
    try:
        print(f"💾 Saving data to {filename}...")
        
        # Ensure output directory exists
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with pretty formatting
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        # Get file size for confirmation
        file_size = output_path.stat().st_size
        print(f"✅ Data saved successfully to: {filename} ({file_size:,} bytes)")
        
        # Also save a readable summary
        summary_file = filename.replace('.json', '_summary.txt')
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(create_summary_report(data))
        print(f"📋 Summary saved to: {summary_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving data to {filename}: {e}")
        logging.error(f"Failed to save JSON: {e}")
        return False

def create_summary_report(data: Any) -> str:
    """
    Create a detailed summary report of the extracted data.
    """
    lines = [
        "=" * 60,
        "WHOSCORED MATCH CENTRE DATA EXTRACTION REPORT",
        "=" * 60,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    if not data:
        lines.extend([
            "❌ NO DATA EXTRACTED",
            "",
            "The extraction process completed but no data was found.",
            "This could indicate:",
            "- The page structure has changed",
            "- The match page is not accessible",
            "- The CSS selectors need updating",
            "- The LLM extraction failed to find relevant content"
        ])
        return "\n".join(lines)
    
    # Extraction metadata
    if "extraction_metadata" in data:
        metadata = data["extraction_metadata"]
        lines.extend([
            "EXTRACTION INFO:",
            f"- Timestamp: {metadata.get('timestamp', 'N/A')}",
            f"- Source: {metadata.get('source', 'N/A')}",
            f"- Scraper Version: {metadata.get('scraper_version', 'N/A')}",
            f"- Crawl4AI Version: {metadata.get('crawl4ai_version', 'N/A')}",
            f"- Success: {metadata.get('extraction_success', 'Unknown')}",
            f"- Data Fields Found: {', '.join(metadata.get('data_fields_found', []))[:100]}...",
            ""
        ])
    
    # Match info
    if "match_info" in data and data["match_info"]:
        match_info = data["match_info"]
        lines.extend([
            "MATCH INFORMATION:",
            f"- Home Team: {match_info.get('home_team', 'N/A')}",
            f"- Away Team: {match_info.get('away_team', 'N/A')}",
            f"- Score: {match_info.get('score', 'N/A')}",
            f"- Date: {match_info.get('date', 'N/A')}",
            f"- Competition: {match_info.get('competition', 'N/A')}",
            ""
        ])
    
    # Timeline data
    if "timeline_data" in data:
        timeline = data["timeline_data"]
        if isinstance(timeline, list) and timeline:
            lines.extend([
                "TIMELINE DATA:",
                f"- Timeline entries: {len(timeline)}",
                f"- First entry: {str(timeline[0])[:100]}..." if timeline else "None",
                ""
            ])
        elif timeline:
            lines.extend([
                "TIMELINE DATA:",
                f"- Timeline data type: {type(timeline)}",
                f"- Timeline summary: {str(timeline)[:200]}...",
                ""
            ])
    
    # Raw data summary
    if "raw_extracted_data" in data:
        raw_data = data["raw_extracted_data"]
        if raw_data:
            lines.extend([
                "RAW EXTRACTED DATA SUMMARY:",
                f"- Total fields: {len(raw_data)}",
                f"- Field names: {', '.join(list(raw_data.keys())[:10])}{'...' if len(raw_data) > 10 else ''}",
                f"- Data size: ~{len(str(raw_data)):,} characters",
                ""
            ])
    
    # Overall summary
    lines.extend([
        "SUMMARY:",
        f"- Extraction completed: ✅",
        f"- Data structure keys: {list(data.keys())}",
        f"- Total data size: ~{len(str(data)):,} characters",
        ""
    ])
    
    lines.append("=" * 60)
    
    return "\n".join(lines)