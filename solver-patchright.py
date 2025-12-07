from patchright.async_api import async_playwright
import asyncio
import logging
import argparse
from xvfbwrapper import Xvfb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudflareBypass:
    def __init__(self, max_retries=5, retry_delay=5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def wait_for_cloudflare_challenge(self, page, timeout=30000):
        """Wait for Cloudflare challenge to appear and complete it."""
        try:
            logger.info("Waiting for Cloudflare challenge iframe...")
            
            # Wait for the iframe to appear
            await page.wait_for_selector(
                "iframe[src*='challenges.cloudflare.com']",
                timeout=timeout,
                state="attached"
            )
            logger.info("Cloudflare iframe detected")
            
            # Get the iframe
            cf_iframe_locator = page.frame_locator(
                "iframe[src*='challenges.cloudflare.com']"
            ).first
            
            # Wait for checkbox to be visible
            cf_checkbox_locator = cf_iframe_locator.locator('input[type="checkbox"]')
            await cf_checkbox_locator.wait_for(state="visible", timeout=10000)
            logger.info("Cloudflare checkbox is visible")
            
            # Click the checkbox
            await cf_checkbox_locator.click()
            logger.info("Clicked Cloudflare checkbox")
            
            # Wait for challenge to complete (iframe should disappear or page should redirect)
            await asyncio.sleep(3)
            
            # Check if challenge is still present
            iframe_count = await page.locator("iframe[src*='challenges.cloudflare.com']").count()
            if iframe_count == 0:
                logger.info("Cloudflare challenge completed successfully")
                return True
            else:
                logger.warning("Cloudflare challenge still present after clicking")
                return False
                
        except Exception as e:
            logger.error(f"Error during Cloudflare challenge: {str(e)}")
            return False
    
    async def is_cloudflare_challenge(self, page):
        """Check if Cloudflare challenge is present by checking title and iframe."""
        try:
            title = await page.title()
            logger.info(f"Page title: {title}")
            
            # Check for Cloudflare in title
            if "just a moment" in title.lower() or "cloudflare" in title.lower():
                logger.info("Cloudflare challenge detected in page title")
                return True
            
            # Also check for iframe
            iframe_count = await page.locator("iframe[src*='challenges.cloudflare.com']").count()
            if iframe_count > 0:
                logger.info("Cloudflare iframe detected")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for Cloudflare: {str(e)}")
            return False
    
    async def navigate_with_retry(self, page, url):
        """Navigate to URL and handle Cloudflare with retries."""
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.max_retries}: Navigating to {url}")
                
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                logger.info("Page loaded")
                
                # Check if Cloudflare challenge is present
                is_cf_challenge = await self.is_cloudflare_challenge(page)
                
                if is_cf_challenge:
                    logger.info("Cloudflare challenge detected")
                    success = await self.wait_for_cloudflare_challenge(page)
                    
                    if success:
                        # Wait a bit and check again
                        await asyncio.sleep(2)
                        still_challenge = await self.is_cloudflare_challenge(page)
                        
                        if not still_challenge:
                            logger.info("Successfully bypassed Cloudflare challenge")
                            return True
                        else:
                            logger.warning(f"Cloudflare challenge still present on attempt {attempt}")
                            if attempt < self.max_retries:
                                logger.info(f"Retrying in {self.retry_delay} seconds...")
                                await asyncio.sleep(self.retry_delay)
                                continue
                    else:
                        logger.warning(f"Failed to bypass Cloudflare on attempt {attempt}")
                        if attempt < self.max_retries:
                            logger.info(f"Retrying in {self.retry_delay} seconds...")
                            await asyncio.sleep(self.retry_delay)
                            continue
                else:
                    logger.info("No Cloudflare challenge detected, page accessible")
                    return True
                    
            except Exception as e:
                logger.error(f"Error on attempt {attempt}: {str(e)}")
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached, giving up")
                    return False
        
        return False

async def run():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Cloudflare bypass script')
    parser.add_argument('-x', '--xvfb', action='store_true', help='Run with XVFB (virtual display)')
    args = parser.parse_args()
    
    bypass = CloudflareBypass(max_retries=5, retry_delay=5)
    
    # Start XVFB if requested
    vdisplay = None
    if args.xvfb:
        logger.info("Starting XVFB virtual display...")
        vdisplay = Xvfb(width=1920, height=1080)
        vdisplay.start()
        logger.info("XVFB started")
    
    try:
        async with async_playwright() as playwright:
            logger.info("Launching browser...")
            
            browser = await playwright.chromium.launch_persistent_context(
                user_data_dir="data",
                channel='chrome',
                headless=False,
                no_viewport=True,
            )
            
            page = await browser.new_page()
            logger.info("New page created")
            
            # Navigate with retry logic
            success = await bypass.navigate_with_retry(page, "https://daddyhd.com/")
            
            if success:
                logger.info("Successfully loaded page!")
                
                # Save page content to file
                try:
                    content = await page.content()
                    with open('dlhd.html', 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info("Page content saved to dlhd.html")
                except Exception as e:
                    logger.error(f"Failed to save page content: {str(e)}")
                
                # Keep browser open for inspection
                await asyncio.sleep(10)
            else:
                logger.error("Failed to load page after all retries")
            
            await browser.close()
            logger.info("Browser closed")
    finally:
        # Stop XVFB if it was started
        if vdisplay:
            logger.info("Stopping XVFB...")
            vdisplay.stop()
            logger.info("XVFB stopped")

if __name__ == "__main__":
    asyncio.run(run())
