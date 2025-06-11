import asyncio
import sys
from config import MATCH_URL, OUTPUT_FILE
from src.scraper import scrape_whoscored_match
from models.match_data import MatchData
from src.utils import (
    format_timeline_data,
    save_data_to_json,
    create_summary_report,
    setup_logging,
    validate_match_url
)

def print_startup_banner():
    print("""
========================================
 WhoScored Match Centre Timeline Scraper
========================================
    """)

async def main():
    print_startup_banner()
    setup_logging()
    if not validate_match_url(MATCH_URL):
        print("❌ Invalid WhoScored match URL!")
        print(f"URL: {MATCH_URL}")
        print("Expected format: https://www.whoscored.com/matches/{id}/live/{match-slug}")
        sys.exit(1)
    print(f"🎯 Target URL: {MATCH_URL}")
    print(f"📊 Output file: {OUTPUT_FILE}")
    print()
    try:
        print("🚀 Starting data extraction...")
        extracted_data = await scrape_whoscored_match(MATCH_URL, MatchData)
        if extracted_data:
            formatted_data = format_timeline_data(extracted_data)
            if save_data_to_json(formatted_data, OUTPUT_FILE):
                print(f"✅ Success! Data saved to {OUTPUT_FILE}")
                summary = create_summary_report(formatted_data)
                print()
                print(summary)
                summary_file = OUTPUT_FILE.replace('.json', '_summary.txt')
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"📋 Summary report saved to {summary_file}")
            else:
                print("❌ Failed to save extracted data")
                sys.exit(1)
        else:
            print("💥 No data was extracted from the match page")
            print()
            print("Possible reasons:")
            print("- Match page not accessible")
            print("- Page structure changed")
            print("- Network connectivity issues")
            print("- Rate limiting or blocking")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        sys.exit(1)

def run_scraper():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Scraping stopped")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_scraper()
