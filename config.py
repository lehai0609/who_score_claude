import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
API_TOKEN = os.getenv("OPENAI_API_KEY", "")

# Target URL
MATCH_URL = os.getenv("MATCH_URL", "https://www.whoscored.com/matches/1821372/live/england-premier-league-2024-2025-nottingham-forest-brentford")

# CSS Selectors
PRIMARY_SELECTOR = "div#matchcentre-timeline-minutes"
ALTERNATIVE_SELECTORS = [
    "div.match-centre-container",
    "div.timeline-container",
    "div#timeline",
    "div#match-centre",
    "[class*='timeline']",
    "[class*='matchcentre']"
]

CONTEXT_SELECTORS = [
    "div#match-centre",
    "div#match-centre-header", 
    "div#match-centre-content",
    "div.match-header",
    "div.score-box"
]

# Scraper Instructions for LLM
SCRAPER_INSTRUCTIONS = """
You are analyzing a WhoScored.com match centre page to extract timeline rating data.

EXTRACT the following information:
1. **Match Information**: Team names, score, date, competition
2. **Timeline Data**: Player/team ratings by minute/period
3. **Match Events**: Goals, cards, substitutions with exact timestamps  
4. **Rating Changes**: How ratings evolve throughout the match
5. **Performance Metrics**: Key statistics by time period

IGNORE completely:
- Advertisement content
- Promotional banners
- Social media widgets
- Navigation menus
- Cookie notices
- Pop-up overlays

FOCUS on:
- Data from the match centre timeline container
- Numerical ratings and statistics
- Timestamped events and changes
- Performance data tables

Return clean, structured JSON with timeline progression and rating data.
"""

# Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2"))
TIMEOUT_DURATION = int(os.getenv("TIMEOUT_DURATION", "60"))
OUTPUT_FILE = "match_timeline_data.json"
