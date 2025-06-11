# WhoScored Match Centre Timeline Scraper

### 🏆 **AI-Powered Football Match Data Extraction**

This project is an AI-powered web scraper built with [**Crawl4AI**](https://docs.crawl4ai.com/) to extract **match centre rating data** and **timeline information** from [**WhoScored.com**](https://www.whoscored.com/). Using **GPT-4o**, it intelligently processes live match data, filters out advertisements, and outputs clean **JSON** data for analysis.

## Features

- **Real-time Match Data** – Extract player ratings, timeline events, and match statistics
- **AI-Powered Filtering** – Use GPT-4o to identify relevant data and ignore ads/promotional content  
- **Timeline Analysis** – Capture rating changes throughout match periods
- **JSON Output** – Clean, structured data ready for analysis or integration
- **No Authentication Required** – Access publicly available match data

## Target Data

The scraper extracts the following information from WhoScored match pages:
- **Timeline Ratings** – Player and team ratings by minute/period
- **Match Events** – Goals, cards, substitutions with timestamps
- **Performance Metrics** – Live statistics during match progression
- **Team Data** – Formation, lineup, and tactical information

## Adaptability

This scraper targets **WhoScored.com** match centre pages but can be adapted for:
- Different match URLs and leagues
- Historical match data extraction
- Live match monitoring
- Custom data fields and filtering

## Use Cases

- **Match Analysis** – Track performance changes throughout matches
- **Data Analytics** – Build datasets for football research
- **Live Monitoring** – Extract real-time match statistics
- **Historical Research** – Collect data from completed matches
- **Performance Tracking** – Monitor player/team rating trends

## Project Structure

```
.
├── main.py              # Main entry point for the scraper
├── config.py            # Configuration (LLM models, URLs, selectors)
├── models/
│   └── match_data.py    # Pydantic models for match data structures
├── src/
│   ├── scraper.py       # Core scraping functionality
│   └── utils.py         # Data processing and export utilities
└── requirements.txt     # Python dependencies
```

## How to Run

### Prerequisites
- Python 3.11+
- OpenAI API key (for GPT-4o)
- Required Python libraries

### Setup

#### 1. Clone and Setup Environment
```bash
git clone <repository-url>
cd whoscored-scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
playwright install
```

#### 3. Configure Environment
Create `.env` file:
```ini
OPENAI_API_KEY="your-openai-api-key-here"
```

#### 4. Run the Scraper
```bash
python main.py
```

The scraper will:
1. Extract data from the configured WhoScored match URL
2. Process timeline and rating information using GPT-4o
3. Filter out advertisements and irrelevant content
4. Save results to `match_timeline_data.json`

## Configuration

Modify `config.py` to customize:

- **MATCH_URL**: Target WhoScored match page
- **LLM_MODEL**: AI model for data processing (`gpt-4o`)
- **CSS_SELECTORS**: HTML elements to target
- **OUTPUT_FORMAT**: JSON structure and fields
- **SCRAPER_INSTRUCTIONS**: AI prompts for data extraction
