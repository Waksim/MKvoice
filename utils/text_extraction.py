# ============================= FILE: utils/text_extraction.py =============================
import asyncio
from newspaper import Article
from playwright.async_api import async_playwright

async def extract_text_from_url_static(url: str) -> str:
    """
    Extract text from a URL using the Newspaper library.
    Works best for static pages.
    """
    article = Article(url)
    article.download()
    article.parse()
    return article.text.strip()

async def extract_text_from_url_dynamic(url: str) -> str:
    """
    Use Playwright to extract text from dynamically generated webpages.
    Fallback if static extraction returns too little content.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)

            special_selectors = [".ReadTextContainerIn"]
            selectors = special_selectors + ["article", ".content", ".main-content"]
            article_text = None

            for selector in selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await page.wait_for_selector(selector, timeout=5000)
                        texts = await page.locator(selector).all_inner_texts()
                        article_text = "\n\n".join(texts).strip()
                        if article_text:
                            break
                except Exception:
                    continue

            if not article_text or article_text.strip() == "":
                article_text = await page.evaluate("document.body.innerText")

            return article_text.strip()
        except Exception:
            return ""
        finally:
            await browser.close()