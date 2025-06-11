import asyncio
import json
from typing import Dict, Any, Optional, Type
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from config import (
    LLM_MODEL, API_TOKEN, PRIMARY_SELECTOR, ALTERNATIVE_SELECTORS, CONTEXT_SELECTORS, SCRAPER_INSTRUCTIONS, MAX_RETRIES, REQUEST_DELAY
)
from src.utils import clean_extracted_data, handle_extraction_error

def get_browser_config() -> BrowserConfig:
    """
    Configure browser for WhoScored.com scraping.
    Updated for Crawl4AI 0.6.3 API.
    """
    return BrowserConfig(
        headless=True,
        viewport_width=1280,
        viewport_height=800,
        verbose=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

def get_llm_strategy() -> LLMExtractionStrategy:
    """
    Configure LLM extraction strategy for Crawl4AI 0.6.3.
    """
    return LLMExtractionStrategy(
        provider=LLM_MODEL,
        api_token=API_TOKEN,
        instructions=SCRAPER_INSTRUCTIONS,
        output_format="json",
        extra_args={
            "temperature": 0.1,
            "max_tokens": 4000
        }
    )

async def check_page_loaded(crawler: AsyncWebCrawler, url: str) -> bool:
    """
    Verify that the WhoScored page has loaded properly.
    """
    try:
        # Simple check to see if page loads
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for=f"() => document.querySelector('{PRIMARY_SELECTOR}') !== null || document.querySelector('div.match-centre-container') !== null",
            delay_before_return_html=3.0
        )
        result = await crawler.arun(url=url, config=run_config)
        if result.success:
            # Check for key indicators
            content = result.cleaned_html.lower()
            indicators = ["match", "timeline", "rating", "vs", "score"]
            found_indicators = sum(1 for indicator in indicators if indicator in content)
            return found_indicators >= 2
        return False
    except Exception as e:
        print(f"Error checking page load: {e}")
        return False

async def extract_with_fallback_selectors(
    crawler: AsyncWebCrawler,
    url: str, 
    llm_strategy: LLMExtractionStrategy
) -> Optional[Dict[str, Any]]:
    """
    Attempt data extraction with multiple CSS selectors as fallback.
    Updated for Crawl4AI 0.6.3 API.
    """
    selectors_to_try = [PRIMARY_SELECTOR] + ALTERNATIVE_SELECTORS
    for i, selector in enumerate(selectors_to_try):
        try:
            print(f"Attempting extraction with selector {i+1}/{len(selectors_to_try)}: {selector}")
            # Build run config for this selector
            run_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=llm_strategy,
                css_selector=selector,
                wait_for=f"() => document.querySelector('{selector}') !== null" if i == 0 else None,
                delay_before_return_html=3.0 if i == 0 else 1.0,
                word_count_threshold=10
            )
            result = await crawler.arun(url=url, config=run_config)
            if result.success and result.extracted_content:
                try:
                    # Parse the extracted content
                    if isinstance(result.extracted_content, str):
                        extracted_data = json.loads(result.extracted_content)
                    else:
                        extracted_data = result.extracted_content
                    if extracted_data and validate_extracted_data(extracted_data):
                        print(f"✅ Successfully extracted data with selector: {selector}")
                        return extracted_data
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"❌ Invalid JSON from selector {selector}: {e}")
                    continue
            else:
                print(f"❌ No data extracted with selector: {selector}")
                if result.error_message:
                    print(f"Error: {result.error_message}")
        except Exception as e:
            print(f"❌ Exception with selector {selector}: {e}")
            continue
        # Brief delay between attempts
        await asyncio.sleep(1)
    print("⚠️ All selectors failed - attempting context-based extraction")
    return await extract_with_context_selectors(crawler, url, llm_strategy)

async def extract_with_context_selectors(
    crawler: AsyncWebCrawler,
    url: str,
    llm_strategy: LLMExtractionStrategy
) -> Optional[Dict[str, Any]]:
    """
    Extract data using broader context selectors when specific selectors fail.
    """
    try:
        # Try extracting from broader page context
        combined_selectors = ", ".join(CONTEXT_SELECTORS)
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=combined_selectors,
            word_count_threshold=50
        )
        result = await crawler.arun(url=url, config=run_config)
        if result.success and result.extracted_content:
            try:
                if isinstance(result.extracted_content, str):
                    extracted_data = json.loads(result.extracted_content)
                else:
                    extracted_data = result.extracted_content
                if extracted_data:
                    print("✅ Extracted data using context selectors")
                    return extracted_data
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception as e:
        print(f"Context extraction failed: {e}")
    return None

def validate_extracted_data(data: Dict[str, Any]) -> bool:
    """
    Validate that extracted data contains essential match information.
    """
    if not isinstance(data, dict):
        return False
    # Check for required fields
    data_str = str(data).lower()
    required_indicators = [
        any(key in data_str for key in ["match", "team", "score", "rating"]),
        len(data_str) > 100,  # Substantial content
        not all(v is None for v in data.values() if v is not None)  # Not all empty
    ]
    return all(required_indicators)

async def scrape_whoscored_match(match_url: str, output_format: Type) -> Optional[Dict[str, Any]]:
    """
    Main function to scrape WhoScored match centre data.
    Updated for Crawl4AI 0.6.3 API.
    Args:
        match_url: URL of the WhoScored match page
        output_format: Pydantic model class for data structure
    Returns:
        Extracted match data or None if extraction fails
    """
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    print(f"🏆 Starting WhoScored match scraping: {match_url}")
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # First, verify the page loads correctly
        print("🔄 Checking page load status...")
        page_loaded = await check_page_loaded(crawler, match_url)
        if not page_loaded:
            print("⚠️ Page may not have loaded completely, proceeding anyway...")
        # Attempt extraction with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                print(f"🎯 Extraction attempt {attempt + 1}/{MAX_RETRIES}")
                extracted_data = await extract_with_fallback_selectors(
                    crawler, match_url, llm_strategy
                )
                if extracted_data:
                    # Clean and validate the data
                    cleaned_data = clean_extracted_data(extracted_data)
                    print("✅ Match data extracted successfully!")
                    return cleaned_data
                else:
                    print(f"❌ Extraction attempt {attempt + 1} failed")
            except Exception as e:
                error_msg = handle_extraction_error(e, attempt + 1)
                print(f"❌ {error_msg}")
            # Wait before retry
            if attempt < MAX_RETRIES - 1:
                print(f"⏳ Waiting {REQUEST_DELAY} seconds before retry...")
                await asyncio.sleep(REQUEST_DELAY)
    print("💥 All extraction attempts failed")
    return None
