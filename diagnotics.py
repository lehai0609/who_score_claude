#!/usr/bin/env python3
"""
WhoScored Page Diagnostic Tool
============================

Quick analysis tool to check what data is actually available on the WhoScored page
without doing full LLM extraction. Helps debug scraping issues.
"""

import asyncio
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from config import MATCH_URL, PRIMARY_SELECTOR, ALTERNATIVE_SELECTORS

async def diagnose_whoscored_page(url: str):
    """
    Analyze the WhoScored page to see what data is actually available.
    """
    print("🔍 WhoScored Page Diagnostic Tool")
    print("=" * 50)
    print(f"Analyzing: {url}")
    print()
    
    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
        verbose=False
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            # Basic page load
            print("📄 Loading page...")
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                delay_before_return_html=5.0
            )
            
            result = await crawler.arun(url=url, config=run_config)
            
            if not result.success:
                print("❌ Failed to load page")
                return
            
            content = result.cleaned_html
            print(f"✅ Page loaded successfully ({len(content):,} characters)")
            print()
            
            # 1. Check for basic match information
            print("🏈 BASIC MATCH INFO:")
            teams = re.findall(r'(nottingham forest|brentford)', content.lower())
            scores = re.findall(r'\b\d+[:-]\d+\b', content)
            print(f"   - Teams found: {set(teams)}")
            print(f"   - Scores found: {set(scores)}")
            print()
            
            # 2. Check for CSS selectors
            print("🎯 CSS SELECTOR ANALYSIS:")
            selectors_found = []
            for selector in [PRIMARY_SELECTOR] + ALTERNATIVE_SELECTORS:
                # Simple check - look for key parts of the selector
                selector_parts = selector.replace("#", "").replace("div", "").replace(".", "").replace("[", "").replace("]", "")
                if selector_parts and selector_parts in content.lower():
                    selectors_found.append(selector)
            
            print(f"   - Selectors potentially present: {len(selectors_found)}")
            for selector in selectors_found[:5]:  # Show first 5
                print(f"     ✓ {selector}")
            print()
            
            # 3. Look for rating-like numbers
            print("📊 RATING DATA ANALYSIS:")
            rating_numbers = re.findall(r'\b[5-9]\.[0-9]\b', content)
            percentage_numbers = re.findall(r'\b\d{1,3}%\b', content)
            
            print(f"   - Potential player ratings (5.0-9.9): {len(rating_numbers)}")
            if rating_numbers:
                print(f"     Examples: {rating_numbers[:10]}")
            
            print(f"   - Percentage values: {len(percentage_numbers)}")
            if percentage_numbers:
                print(f"     Examples: {percentage_numbers[:10]}")
            print()
            
            # 4. Look for football-specific keywords
            print("⚽ FOOTBALL DATA KEYWORDS:")
            keywords = {
                "timeline": content.lower().count("timeline"),
                "rating": content.lower().count("rating"),
                "performance": content.lower().count("performance"),
                "stats": content.lower().count("stats"),
                "player": content.lower().count("player"),
                "passes": content.lower().count("passes"),
                "shots": content.lower().count("shots"),
                "tackles": content.lower().count("tackles"),
                "dribbles": content.lower().count("dribbles")
            }
            
            for keyword, count in keywords.items():
                print(f"   - '{keyword}': {count} occurrences")
            print()
            
            # 5. Look for JSON data in script tags
            print("📱 JAVASCRIPT DATA ANALYSIS:")
            script_tags = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
            json_scripts = []
            
            for script in script_tags:
                if any(keyword in script.lower() for keyword in ['rating', 'player', 'stats', 'timeline']):
                    json_scripts.append(script[:200] + "..." if len(script) > 200 else script)
            
            print(f"   - Script tags containing relevant keywords: {len(json_scripts)}")
            for i, script in enumerate(json_scripts[:3]):  # Show first 3
                print(f"     Script {i+1}: {script.replace('\n', ' ')}")
            print()
            
            # 6. Check for data attributes
            print("🔧 DATA ATTRIBUTES:")
            data_attributes = re.findall(r'data-[a-zA-Z-]+="[^"]*"', content)
            relevant_data_attrs = [attr for attr in data_attributes if any(keyword in attr.lower() for keyword in ['rating', 'player', 'stats', 'match'])]
            
            print(f"   - Total data attributes: {len(data_attributes)}")
            print(f"   - Relevant data attributes: {len(relevant_data_attrs)}")
            for attr in relevant_data_attrs[:5]:  # Show first 5
                print(f"     {attr}")
            print()
            
            # 7. Overall assessment
            print("📋 ASSESSMENT:")
            
            has_basic_match_data = len(teams) >= 2 and len(scores) >= 1
            has_potential_selectors = len(selectors_found) > 0
            has_rating_data = len(rating_numbers) > 5
            has_rich_content = sum(keywords.values()) > 20
            
            print(f"   - Has basic match data: {'✅' if has_basic_match_data else '❌'}")
            print(f"   - Has potential CSS selectors: {'✅' if has_potential_selectors else '❌'}")
            print(f"   - Has rating data: {'✅' if has_rating_data else '❌'}")
            print(f"   - Has rich football content: {'✅' if has_rich_content else '❌'}")
            
            if has_rating_data and has_rich_content:
                print("   🎯 VERDICT: Page contains detailed data - scraper should work!")
            elif has_basic_match_data and has_rich_content:
                print("   ⚠️  VERDICT: Page has some data but may lack detailed ratings")
            else:
                print("   ❌ VERDICT: Page appears to lack detailed timeline/rating data")
            
            print()
            
            # 8. Recommendations
            print("💡 RECOMMENDATIONS:")
            
            if not has_rating_data:
                print("   - The match may be too old or ratings data not available")
                print("   - Try a more recent/live match URL")
                
            if not has_potential_selectors:
                print("   - CSS selectors may need updating")
                print("   - WhoScored may have changed their page structure")
                
            if has_basic_match_data and not has_rating_data:
                print("   - Basic match info is available but not detailed performance data")
                print("   - This is expected for older/completed matches")
                
            print("   - Consider using the enhanced scraper with broader selectors")
            print("   - Try different match URLs (more recent matches)")
            
        except Exception as e:
            print(f"❌ Diagnostic failed: {e}")

async def main():
    """Run the diagnostic tool."""
    await diagnose_whoscored_page(MATCH_URL)

if __name__ == "__main__":
    asyncio.run(main())