import asyncio
import json
from typing import Dict, Any, Optional, Type
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from config import (
    LLM_MODEL, API_TOKEN, PRIMARY_SELECTOR, ALTERNATIVE_SELECTORS, 
    CONTEXT_SELECTORS, SCRAPER_INSTRUCTIONS, MAX_RETRIES, REQUEST_DELAY,
    WAIT_FOR_TIMELINE_JS
)
from src.utils import clean_extracted_data, handle_extraction_error

def get_browser_config() -> BrowserConfig:
    """
    Enhanced browser configuration for better WhoScored.com scraping.
    """
    return BrowserConfig(
        headless=True,
        viewport_width=1920,  # Larger viewport for better content rendering
        viewport_height=1080,
        verbose=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Configure LLM extraction strategy with enhanced instructions.
    """
    llm_config = LLMConfig(
        provider=f"openai/{LLM_MODEL}",
        api_token=API_TOKEN
    )
    
    return LLMExtractionStrategy(
        llm_config=llm_config,
        instruction=SCRAPER_INSTRUCTIONS,
        extraction_type="schema"
    )

async def check_page_loaded_with_timeline(crawler: AsyncWebCrawler, url: str) -> Dict[str, Any]:
    """
    Enhanced page loading check that specifically looks for timeline/rating data.
    """
    try:
        print("🔍 Checking page load and timeline data availability...")
        
        # First, basic page load check with longer wait
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            delay_before_return_html=5.0,  # Wait longer for content
            js_code=WAIT_FOR_TIMELINE_JS,
            wait_for=WAIT_FOR_TIMELINE_JS,
            page_timeout=30000  # 30 second timeout
        )
        
        result = await crawler.arun(url=url, config=run_config)
        
        analysis = {
            "page_loaded": False,
            "has_basic_content": False,
            "has_timeline_indicators": False,
            "has_rating_data": False,
            "content_size": 0,
            "found_selectors": []
        }
        
        if result.success:
            content = result.cleaned_html.lower()
            analysis["content_size"] = len(content)
            analysis["page_loaded"] = True
            
            # Check for basic match content
            basic_indicators = ["match", "vs", "score", "nottingham", "brentford"]
            analysis["has_basic_content"] = sum(1 for indicator in basic_indicators if indicator in content) >= 3
            
            # Check for timeline/rating specific content
            timeline_indicators = ["timeline", "rating", "performance", "stats", "player"]
            analysis["has_timeline_indicators"] = sum(1 for indicator in timeline_indicators if indicator in content) >= 2
            
            # Check for numerical rating data (numbers like 6.5, 7.2, etc.)
            import re
            rating_pattern = r'[5-9]\.[0-9]'
            rating_matches = re.findall(rating_pattern, content)
            analysis["has_rating_data"] = len(rating_matches) > 5  # At least 5 potential ratings
            
            # Check which of our selectors exist
            for selector in [PRIMARY_SELECTOR] + ALTERNATIVE_SELECTORS[:5]:
                if selector.replace("#", "").replace("div", "").replace(".", "") in content:
                    analysis["found_selectors"].append(selector)
        
        print(f"📊 Page Analysis Results:")
        print(f"   - Page loaded: {analysis['page_loaded']}")
        print(f"   - Content size: {analysis['content_size']:,} characters")
        print(f"   - Has basic content: {analysis['has_basic_content']}")
        print(f"   - Has timeline indicators: {analysis['has_timeline_indicators']}")
        print(f"   - Has rating data: {analysis['has_rating_data']}")
        print(f"   - Found selectors: {analysis['found_selectors']}")
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error in page analysis: {e}")
        return {"page_loaded": False, "error": str(e)}

async def extract_with_enhanced_selectors(
    crawler: AsyncWebCrawler,
    url: str, 
    llm_strategy: LLMExtractionStrategy,
    page_analysis: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Enhanced extraction using multiple strategies based on page analysis.
    """
    print("🎯 Starting enhanced extraction process...")
    
    # Strategy 1: Try primary selector with longer wait
    if PRIMARY_SELECTOR in page_analysis.get("found_selectors", []):
        print(f"📍 Trying primary selector: {PRIMARY_SELECTOR}")
        result = await try_selector_extraction(crawler, url, llm_strategy, PRIMARY_SELECTOR, wait_time=8.0)
        if result:
            return result
    
    # Strategy 2: Try alternative selectors
    for i, selector in enumerate(ALTERNATIVE_SELECTORS):
        print(f"📍 Trying alternative selector {i+1}/{len(ALTERNATIVE_SELECTORS)}: {selector}")
        result = await try_selector_extraction(crawler, url, llm_strategy, selector, wait_time=3.0)
        if result:
            return result
        await asyncio.sleep(1)  # Small delay between attempts
    
    # Strategy 3: Context-based extraction (broad page content)
    print("📍 Trying context-based extraction...")
    return await extract_with_context_selectors(crawler, url, llm_strategy)

async def try_selector_extraction(
    crawler: AsyncWebCrawler,
    url: str,
    llm_strategy: LLMExtractionStrategy,
    selector: str,
    wait_time: float = 3.0
) -> Optional[Dict[str, Any]]:
    """
    Try extraction with a specific selector.
    """
    try:
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=selector,
            delay_before_return_html=wait_time,
            word_count_threshold=20,
            # Try to trigger any dynamic content loading
            js_code="""
            // Scroll to trigger any lazy loading
            window.scrollTo(0, document.body.scrollHeight);
            // Click any timeline or stats tabs that might exist
            const tabs = document.querySelectorAll('[data-tab], .tab, [role="tab"]');
            tabs.forEach(tab => {
                if (tab.textContent.toLowerCase().includes('stats') || 
                    tab.textContent.toLowerCase().includes('timeline')) {
                    tab.click();
                }
            });
            """
        )
        
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success and result.extracted_content:
            try:
                if isinstance(result.extracted_content, str):
                    extracted_data = json.loads(result.extracted_content)
                else:
                    extracted_data = result.extracted_content
                    
                if extracted_data and validate_enhanced_data(extracted_data, selector):
                    print(f"✅ Successfully extracted data with selector: {selector}")
                    return extracted_data
                else:
                    print(f"⚠️ Data validation failed for selector: {selector}")
                    
            except (json.JSONDecodeError, TypeError) as e:
                print(f"❌ JSON parsing error for selector {selector}: {e}")
                
        else:
            print(f"❌ No extraction result for selector: {selector}")
            
    except Exception as e:
        print(f"❌ Exception with selector {selector}: {e}")
    
    return None

async def extract_with_context_selectors(
    crawler: AsyncWebCrawler,
    url: str,
    llm_strategy: LLMExtractionStrategy
) -> Optional[Dict[str, Any]]:
    """
    Extract from broader page context when specific selectors fail.
    """
    try:
        print("🌐 Attempting broad context extraction...")
        
        # Use entire page content with enhanced processing
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            delay_before_return_html=5.0,
            word_count_threshold=100,
            # Additional JavaScript to extract any hidden data
            js_code="""
            // Look for any JSON data in script tags
            const scripts = document.querySelectorAll('script');
            let jsonData = [];
            scripts.forEach(script => {
                const content = script.textContent;
                if (content.includes('rating') || content.includes('player') || content.includes('stats')) {
                    jsonData.push(content.substring(0, 500)); // First 500 chars
                }
            });
            
            // Add any data attributes that might contain stats
            const elements = document.querySelectorAll('[data-stats], [data-rating], [data-player]');
            elements.forEach(el => {
                jsonData.push(el.outerHTML.substring(0, 200));
            });
            
            // Store in window for extraction
            window.extractedJsonData = jsonData;
            """
        )
        
        result = await crawler.arun(url=url, config=run_config)
        
        if result.success and result.extracted_content:
            try:
                if isinstance(result.extracted_content, str):
                    extracted_data = json.loads(result.extracted_content)
                else:
                    extracted_data = result.extracted_content
                    
                if extracted_data:
                    print("✅ Context extraction completed")
                    print(f"📊 Extracted data type: {type(extracted_data)}")
                    if isinstance(extracted_data, dict):
                        print(f"📊 Data keys: {list(extracted_data.keys())}")
                    elif isinstance(extracted_data, list):
                        print(f"📊 List length: {len(extracted_data)}")
                    return extracted_data
                    
            except (json.JSONDecodeError, TypeError) as e:
                print(f"❌ JSON parsing error in context extraction: {e}")
                print(f"📄 Raw content preview: {str(result.extracted_content)[:300]}...")
                
    except Exception as e:
        print(f"❌ Context extraction failed: {e}")
    
    return None

def validate_enhanced_data(data: Any, selector: str = "") -> bool:
    """
    Enhanced validation that looks specifically for rating and performance data.
    """
    if not data:
        return False
    
    print(f"🔍 Enhanced validation for data from {selector}")
    
    data_str = str(data).lower()
    data_size = len(data_str)
    
    # Look for specific indicators of valuable rating data
    rating_indicators = [
        "rating", "performance", "player", "timeline", "stats", 
        "passes", "shots", "tackles", "dribbles", "interceptions"
    ]
    
    # Look for numerical patterns that suggest ratings
    import re
    rating_numbers = re.findall(r'[5-9]\.[0-9]', data_str)  # Player ratings typically 5.0-10.0
    percentage_numbers = re.findall(r'\d{1,3}%', data_str)  # Pass accuracy, etc.
    
    has_rating_keywords = sum(1 for indicator in rating_indicators if indicator in data_str) >= 3
    has_rating_numbers = len(rating_numbers) >= 2
    has_stats_numbers = len(percentage_numbers) >= 1
    has_substantial_content = data_size > 200
    
    print(f"🔍 Validation metrics:")
    print(f"   - Has rating keywords: {has_rating_keywords} ({sum(1 for indicator in rating_indicators if indicator in data_str)}/3)")
    print(f"   - Has rating numbers: {has_rating_numbers} (found {len(rating_numbers)} rating-like numbers)")
    print(f"   - Has stats numbers: {has_stats_numbers} (found {len(percentage_numbers)} percentages)")
    print(f"   - Has substantial content: {has_substantial_content} ({data_size} chars)")
    
    # Accept data if it has meaningful rating/performance content
    return (has_rating_keywords and has_substantial_content) or (has_rating_numbers and has_substantial_content)

async def scrape_whoscored_match(match_url: str, output_format: Type) -> Optional[Dict[str, Any]]:
    """
    Enhanced main scraping function with better timeline data detection.
    """
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    
    print(f"🏆 Starting Enhanced WhoScored match scraping: {match_url}")
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Enhanced page analysis
        page_analysis = await check_page_loaded_with_timeline(crawler, match_url)
        
        if not page_analysis.get("page_loaded", False):
            print("⚠️ Page failed to load properly, but continuing anyway...")
        
        # Attempt extraction with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                print(f"🎯 Enhanced extraction attempt {attempt + 1}/{MAX_RETRIES}")
                
                extracted_data = await extract_with_enhanced_selectors(
                    crawler, match_url, llm_strategy, page_analysis
                )
                
                if extracted_data:
                    print("🧹 Processing extracted data...")
                    cleaned_data = clean_extracted_data(extracted_data)
                    
                    if cleaned_data:
                        print("✅ Enhanced match data extraction completed!")
                        # Add page analysis to the results for debugging
                        cleaned_data["page_analysis"] = page_analysis
                        return cleaned_data
                    else:
                        print("⚠️ Data cleaning resulted in empty data, returning original")
                        return extracted_data
                else:
                    print(f"❌ Enhanced extraction attempt {attempt + 1} failed")
                    
            except Exception as e:
                error_msg = handle_extraction_error(e, attempt + 1)
                print(f"❌ {error_msg}")
                
            # Wait before retry
            if attempt < MAX_RETRIES - 1:
                print(f"⏳ Waiting {REQUEST_DELAY} seconds before retry...")
                await asyncio.sleep(REQUEST_DELAY)
    
    print("💥 All enhanced extraction attempts failed")
    return None