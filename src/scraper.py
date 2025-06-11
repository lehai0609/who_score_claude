import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMExtractionStrategy
from config import (
    LLM_MODEL, API_TOKEN, PRIMARY_SELECTOR, ALTERNATIVE_SELECTORS, CONTEXT_SELECTORS, BROWSER_CONFIG, SCRAPER_INSTRUCTIONS, MAX_RETRIES, REQUEST_DELAY
)
from src.utils import clean_extracted_data, handle_extraction_error
from typing import Type

def get_browser_config() -> BrowserConfig:
    return BrowserConfig(
        headless=BROWSER_CONFIG["headless"],
        timeout=BROWSER_CONFIG["timeout"],
        viewport=BROWSER_CONFIG["viewport"],
        extra_args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage"
        ]
    )

def get_llm_strategy(output_format) -> LLMExtractionStrategy:
    return LLMExtractionStrategy(
        provider=LLM_MODEL,
        api_token=API_TOKEN,
        output_format=output_format,
        instructions=SCRAPER_INSTRUCTIONS,
        verbose=True,
        extra_args={
            "temperature": 0.1,
            "max_tokens": 4000
        }
    )

async def check_page_loaded(crawler: AsyncWebCrawler, url: str, session_id: str) -> bool:
    try:
        await crawler.goto(url, session_id=session_id)
        await asyncio.sleep(REQUEST_DELAY)
        elements = await crawler.query_selector_all(PRIMARY_SELECTOR, session_id=session_id)
        return bool(elements)
    except Exception as e:
        print(f"Error checking page load: {e}")
        return False

async def extract_with_fallback_selectors(crawler: AsyncWebCrawler, url: str, llm_strategy: LLMExtractionStrategy, session_id: str):
    selectors = [PRIMARY_SELECTOR] + ALTERNATIVE_SELECTORS
    for selector in selectors:
        try:
            html = await crawler.extract_html(selector, session_id=session_id)
            if html:
                data = await llm_strategy.extract(html)
                return data
        except Exception:
            continue
    return None

async def scrape_whoscored_match(url: str, data_model: Type):
    crawler = AsyncWebCrawler(get_browser_config())
    session_id = await crawler.start()
    try:
        if not await check_page_loaded(crawler, url, session_id):
            print("❌ Could not load match page.")
            return None
        llm_strategy = get_llm_strategy(output_format="json")
        raw_data = await extract_with_fallback_selectors(crawler, url, llm_strategy, session_id)
        if not raw_data:
            print("❌ No data extracted.")
            return None
        cleaned_data = clean_extracted_data(raw_data)
        return data_model(**cleaned_data)
    except Exception as e:
        handle_extraction_error(e)
        return None
    finally:
        await crawler.stop(session_id)
