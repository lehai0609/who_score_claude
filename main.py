import asyncio
import sys
from config import MATCH_URL, OUTPUT_FILE
from src.scraper import scrape_whoscored_match  # This will use the enhanced version
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
 WhoScored Enhanced Timeline Scraper
 v2.0 - Improved Rating Data Extraction
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
    print("🔍 Enhanced extraction mode: Looking for detailed rating data")
    print()
    
    try:
        print("🚀 Starting enhanced data extraction...")
        extracted_data = await scrape_whoscored_match(MATCH_URL, MatchData)
        
        if extracted_data:
            formatted_data = format_timeline_data(extracted_data)
            
            if save_data_to_json(formatted_data, OUTPUT_FILE):
                print(f"✅ Success! Data saved to {OUTPUT_FILE}")
                
                # Analyze what we actually got
                print("\n📊 EXTRACTION ANALYSIS:")
                
                # Check if we got detailed rating data
                timeline_data = formatted_data.get("timeline_data", [])
                raw_data = formatted_data.get("raw_extracted_data", {})
                
                if isinstance(timeline_data, list) and len(timeline_data) > 0:
                    first_item = timeline_data[0] if timeline_data else {}
                    
                    # Check for detailed rating information
                    has_player_ratings = "player_ratings" in str(first_item) or "ratings" in str(first_item)
                    has_performance_data = "performance" in str(first_item) or "stats" in str(first_item)
                    has_timeline_changes = "timeline" in str(first_item) and len(str(first_item).get("timeline", [])) > 0
                    
                    print(f"   - Timeline entries found: {len(timeline_data)}")
                    print(f"   - Player ratings detected: {'✅' if has_player_ratings else '❌'}")
                    print(f"   - Performance data detected: {'✅' if has_performance_data else '❌'}")
                    print(f"   - Timeline changes detected: {'✅' if has_timeline_changes else '❌'}")
                    
                    if not has_player_ratings and not has_performance_data:
                        print("\n⚠️  NOTICE: Detailed rating data not found!")
                        print("   This could mean:")
                        print("   - The match is completed and detailed data no longer available")
                        print("   - WhoScored has changed their data structure")
                        print("   - The page requires login or has access restrictions")
                        print("   - Try a more recent/live match for better results")
                else:
                    print("   - No timeline data structure found")
                
                # Page analysis results
                page_analysis = formatted_data.get("page_analysis", {})
                if page_analysis:
                    print(f"\n🔍 PAGE ANALYSIS:")
                    print(f"   - Content size: {page_analysis.get('content_size', 0):,} characters")
                    print(f"   - Timeline indicators: {'✅' if page_analysis.get('has_timeline_indicators') else '❌'}")
                    print(f"   - Rating data: {'✅' if page_analysis.get('has_rating_data') else '❌'}")
                    print(f"   - Working selectors: {len(page_analysis.get('found_selectors', []))}")
                
                summary = create_summary_report(formatted_data)
                print(f"\n{summary}")
                
                summary_file = OUTPUT_FILE.replace('.json', '_summary.txt')
                with open(summary_file, 'w', encoding='utf-8') as f:
                    f.write(summary)
                print(f"📋 Summary report saved to {summary_file}")
                
            else:
                print("❌ Failed to save extracted data")
                sys.exit(1)
        else:
            print("💥 No data was extracted from the match page")
            print("\n🔧 TROUBLESHOOTING SUGGESTIONS:")
            print("1. Run diagnostic tool: python diagnostic.py")
            print("2. Try a more recent match URL")
            print("3. Check if the match page is accessible in a browser")
            print("4. Verify your OpenAI API key is working")
            print("5. Check the scraper.log file for detailed error information")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        print("\n🔧 For debugging:")
        print("1. Check scraper.log for detailed error information")
        print("2. Run: python diagnostic.py to analyze the page")
        print("3. Verify your internet connection and OpenAI API key")
        import traceback
        traceback.print_exc()
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