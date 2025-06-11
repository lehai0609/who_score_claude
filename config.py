import os
from dotenv import load_dotenv

load_dotenv()

MATCH_URL = os.getenv("MATCH_URL", "https://www.whoscored.com/matches/1821372/live/england-premier-league-2024-2025-nottingham-forest-brentford")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
API_TOKEN = os.getenv("OPENAI_API_KEY", "")
PRIMARY_SELECTOR = "div#matchcentre-timeline-minutes"
ALTERNATIVE_SELECTORS = [
    "div.match-centre-container",
    "div.timeline-container",
    "div#timeline",
    "div#match-centre"
]
CONTEXT_SELECTORS = [
    "div#match-centre",
    "div#match-centre-header",
    "div#match-centre-content"
]
BROWSER_CONFIG = {
    "headless": True,
    "timeout": 60,
    "viewport": {"width": 1280, "height": 800}
}
SCRAPER_INSTRUCTIONS = """
Extract all timeline rating data, match events, and performance metrics from the WhoScored match centre page. Ignore advertisements, banners, and irrelevant content. Return clean, structured JSON with timeline progression and rating data.
"""
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2"))
TIMEOUT_DURATION = int(os.getenv("TIMEOUT_DURATION", "60"))
OUTPUT_FILE = "match_timeline_data.json"
