import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
API_TOKEN = os.getenv("OPENAI_API_KEY", "")

# Target URL
MATCH_URL = os.getenv("MATCH_URL", "https://www.whoscored.com/matches/1821372/live/england-premier-league-2024-2025-nottingham-forest-brentford")

# Updated CSS Selectors for Current WhoScored Structure
PRIMARY_SELECTOR = "div#matchcentre-timeline-minutes"

# More comprehensive alternative selectors
ALTERNATIVE_SELECTORS = [
    "div.match-centre-container",
    "div.timeline-container",
    "div#timeline",
    "div#match-centre",
    "div.match-center",
    "[class*='timeline']",
    "[class*='matchcentre']",
    "[class*='match-center']",
    "[class*='rating']",
    "[class*='performance']",
    "[data-widget='match-centre']",
    "[data-widget='timeline']",
    ".ratings-widget",
    ".player-ratings",
    ".match-stats",
    ".live-match-centre"
]

# Context selectors for broader page extraction
CONTEXT_SELECTORS = [
    "div#match-centre",
    "div#match-centre-header", 
    "div#match-centre-content",
    "div.match-header",
    "div.score-box",
    "div.match-info",
    "div.team-info",
    "div.player-stats",
    "div.match-timeline",
    "div.ratings-section",
    "div.statistics-section",
    "[class*='player']",
    "[class*='rating']",
    "[class*='stat']"
]

# Enhanced LLM Instructions with Specific Focus on Ratings Data
SCRAPER_INSTRUCTIONS = """
You are analyzing a WhoScored.com match centre page to extract comprehensive match data, with SPECIAL FOCUS on player ratings and performance metrics.

PRIORITY EXTRACTION TARGETS (MOST IMPORTANT):
1. **Player Ratings by Timeline**: Individual player ratings throughout the match (by minute/period)
2. **Rating Changes**: How each player's rating evolved during the match
3. **Performance Metrics**: Detailed statistics like passes, shots, tackles, dribbles
4. **Timeline Statistics**: Minute-by-minute statistical breakdown
5. **Team Performance Data**: Overall team ratings and statistics by time period

EXTRACT the following information in this order of priority:

### HIGH PRIORITY (Rating Data):
- **Individual Player Ratings**: Each player's rating at different time points
- **Rating Timeline**: How ratings changed throughout the match (e.g., minute 15: 6.2, minute 30: 6.8)
- **Top Performers**: Highest rated players by time period
- **Rating Influencing Events**: Events that caused rating changes (goals, assists, cards, etc.)
- **Performance Statistics**: Key stats for each player (passes, shots, tackles, interceptions)

### MEDIUM PRIORITY (Match Data):
- **Match Information**: Team names, final score, date, competition
- **Match Events**: Goals, cards, substitutions with exact timestamps
- **Team Statistics**: Possession, shots, pass accuracy by time period
- **Formation/Lineup Data**: Starting formations and player positions

### LOW PRIORITY (Context):
- **Match Details**: Venue, referee, attendance
- **Weather Conditions**: If available
- **Manager Information**: Team managers

SPECIAL INSTRUCTIONS FOR RATINGS:
- Look for any numerical values between 5.0-10.0 (these are likely player ratings)
- Search for timeline or minute-based data structures
- Find any JSON data embedded in the page containing player statistics
- Look for AJAX/dynamic content that might contain live rating updates
- Extract any data-attributes or JavaScript variables containing match statistics

IGNORE completely:
- Advertisement content and promotional banners
- Social media widgets and sharing buttons
- Navigation menus and footer content
- Cookie notices and pop-up overlays
- Comment sections and user discussions

OUTPUT FORMAT:
Return a comprehensive JSON structure like this:
{
  "match_info": {
    "home_team": "...",
    "away_team": "...",
    "score": "...",
    "date": "...",
    "competition": "..."
  },
  "player_ratings": [
    {
      "player_name": "...",
      "team": "...",
      "position": "...",
      "final_rating": 7.2,
      "rating_timeline": [
        {"minute": 15, "rating": 6.8},
        {"minute": 30, "rating": 7.1},
        {"minute": 45, "rating": 7.2}
      ],
      "statistics": {
        "passes": 45,
        "pass_accuracy": 89,
        "shots": 2,
        "tackles": 4
      }
    }
  ],
  "timeline_data": [
    {
      "minute": 15,
      "period": "first_half",
      "team_ratings": {
        "home_avg": 6.5,
        "away_avg": 6.8
      },
      "key_events": ["event1", "event2"],
      "statistics": {}
    }
  ],
  "performance_metrics": {
    "team_stats": {},
    "individual_stats": [],
    "key_performances": []
  }
}

If detailed rating data is not available (match finished, data not loaded), clearly indicate this in the response and extract whatever statistical data is available.
"""

# Enhanced scraping configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "3"))  # Increased delay
TIMEOUT_DURATION = int(os.getenv("TIMEOUT_DURATION", "90"))  # Increased timeout
OUTPUT_FILE = "match_timeline_data.json"

# JavaScript code to wait for dynamic content
WAIT_FOR_TIMELINE_JS = """
// Wait for timeline or rating data to load
const waitForData = () => {
    const selectors = [
        'div#matchcentre-timeline-minutes',
        '[class*="timeline"]',
        '[class*="rating"]',
        '[class*="player"]',
        '.match-stats',
        '.player-stats'
    ];
    
    for (let selector of selectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent.trim().length > 100) {
            return true;
        }
    }
    return false;
};

// Check for any data that looks like ratings (numbers between 5-10)
const hasRatingData = () => {
    const pageText = document.body.textContent;
    const ratingPattern = /[56789]\.[0-9]/g;
    const matches = pageText.match(ratingPattern);
    return matches && matches.length > 5; // At least 5 potential ratings
};

return waitForData() || hasRatingData();
"""