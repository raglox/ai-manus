"""
Enhanced Playwright Browser with Vision-Enhanced Navigation, Smart Scroll, and Error Handling
This file contains extensions to the PlaywrightBrowser class for advanced browser automation.
"""

from typing import Dict, Any, Optional, List
from playwright.async_api import Page
import asyncio
import logging

logger = logging.getLogger(__name__)


class BrowserEnhancedMixin:
    """
    Mixin class providing enhanced browser capabilities:
    - Vision-Enhanced Navigation with bounding boxes
    - Smart scroll for infinite scroll pages
    - Automatic handling of common errors (popups, cookie banners, timeouts)
    """
    
    async def _handle_common_popups(self) -> None:
        """
        Automatically detect and close common popups, cookie banners, and overlays.
        This prevents them from blocking interactions with the main page content.
        """
        page: Page = self.page
        
        # Common cookie banner selectors
        cookie_selectors = [
            # Generic patterns
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            'button:has-text("I Accept")',
            'button:has-text("Agree")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button:has-text("Allow")',
            '[class*="cookie"] button:has-text("Accept")',
            '[class*="cookie"] button:has-text("OK")',
            '[class*="gdpr"] button:has-text("Accept")',
            '[id*="cookie"] button:has-text("Accept")',
            # Specific frameworks
            '.cc-banner button.cc-allow',
            '.cc-compliance button.cc-allow',
            '#onetrust-accept-btn-handler',
            '.optanon-allow-all-button',
            '[aria-label*="Accept cookies"]',
            '[aria-label*="Accept all"]',
        ]
        
        # Try to close cookie banners
        for selector in cookie_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    # Check if visible
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.click(timeout=2000)
                        logger.info(f"Closed cookie banner using selector: {selector}")
                        await asyncio.sleep(0.5)  # Wait for animation
                        break
            except Exception:
                continue
        
        # Close modal dialogs and popups
        modal_selectors = [
            '[class*="modal"] button[class*="close"]',
            '[class*="popup"] button[class*="close"]',
            '[class*="overlay"] button[class*="close"]',
            'button[aria-label="Close"]',
            'button[aria-label="close"]',
            '[class*="close-button"]',
            '.modal-close',
            '.popup-close',
        ]
        
        for selector in modal_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.click(timeout=2000)
                        logger.info(f"Closed modal using selector: {selector}")
                        await asyncio.sleep(0.3)
            except Exception:
                continue
    
    async def smart_scroll(
        self,
        direction: str = "down",
        max_scrolls: int = 10,
        check_for_new_content: bool = True
    ) -> Dict[str, Any]:
        """
        Smart scrolling that handles infinite scroll pages intelligently.
        
        Args:
            direction: 'down' or 'up'
            max_scrolls: Maximum number of scroll attempts
            check_for_new_content: If True, stops when no new content is loaded
            
        Returns:
            Dict with scroll statistics
        """
        page: Page = self.page
        await self._ensure_page()
        
        stats = {
            "scrolls_performed": 0,
            "content_height_start": 0,
            "content_height_end": 0,
            "new_content_loaded": False
        }
        
        # Get initial page height
        initial_height = await page.evaluate("document.body.scrollHeight")
        stats["content_height_start"] = initial_height
        
        scroll_pause_time = 1.5  # Wait for content to load
        last_height = initial_height
        scrolls_without_change = 0
        max_scrolls_without_change = 3
        
        for scroll_num in range(max_scrolls):
            # Perform scroll
            if direction == "down":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:  # up
                await page.evaluate("window.scrollTo(0, 0)")
            
            stats["scrolls_performed"] += 1
            
            # Wait for new content to load
            await asyncio.sleep(scroll_pause_time)
            
            if check_for_new_content and direction == "down":
                # Check if new content loaded
                new_height = await page.evaluate("document.body.scrollHeight")
                
                if new_height > last_height:
                    stats["new_content_loaded"] = True
                    scrolls_without_change = 0
                    logger.info(f"New content loaded: {new_height} > {last_height}")
                else:
                    scrolls_without_change += 1
                    logger.info(f"No new content after scroll {scroll_num + 1}")
                
                last_height = new_height
                
                # Stop if no new content for multiple scrolls
                if scrolls_without_change >= max_scrolls_without_change:
                    logger.info("Reached end of content (infinite scroll)")
                    break
        
        # Get final height
        final_height = await page.evaluate("document.body.scrollHeight")
        stats["content_height_end"] = final_height
        
        return stats
    
    async def navigate_with_retry(
        self,
        url: str,
        max_retries: int = 3,
        handle_popups: bool = True,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Navigate to URL with automatic retry and error handling.
        
        Args:
            url: Target URL
            max_retries: Number of retry attempts
            handle_popups: Auto-close popups after navigation
            timeout: Navigation timeout in milliseconds
            
        Returns:
            Dict with navigation result
        """
        page: Page = self.page
        await self._ensure_page()
        
        result = {
            "success": False,
            "url": url,
            "attempts": 0,
            "error": None
        }
        
        for attempt in range(max_retries):
            result["attempts"] = attempt + 1
            
            try:
                logger.info(f"Navigation attempt {attempt + 1}/{max_retries} to {url}")
                
                # Try to navigate
                response = await page.goto(
                    url,
                    timeout=timeout,
                    wait_until="domcontentloaded"  # More forgiving than "load"
                )
                
                # Wait a bit for JavaScript to initialize
                await asyncio.sleep(1)
                
                # Handle popups if requested
                if handle_popups:
                    await self._handle_common_popups()
                
                result["success"] = True
                result["status_code"] = response.status if response else None
                logger.info(f"Successfully navigated to {url}")
                break
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Navigation attempt {attempt + 1} failed: {error_msg}")
                result["error"] = error_msg
                
                # Don't retry certain errors
                if "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                    logger.error(f"DNS resolution failed for {url}, not retrying")
                    break
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        return result
    
    async def get_viewport_elements_with_bbox(self) -> List[Dict[str, Any]]:
        """
        Extract all interactive elements in viewport with their bounding boxes.
        This enables Vision-Enhanced Navigation for precise clicking.
        
        Returns:
            List of elements with text, tag, position, and bounding box coordinates
        """
        page: Page = self.page
        await self._ensure_page()
        
        elements = await page.evaluate("""() => {
            const elements = [];
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            
            // Select all interactive elements
            const selectors = 'a, button, input, textarea, select, [role="button"], [onclick], [tabindex]:not([tabindex="-1"])';
            const allElements = document.querySelectorAll(selectors);
            
            for (const el of allElements) {
                const rect = el.getBoundingClientRect();
                
                // Check if element is in viewport and has dimensions
                if (rect.width > 0 && rect.height > 0 &&
                    rect.top >= 0 && rect.top <= viewportHeight &&
                    rect.left >= 0 && rect.left <= viewportWidth) {
                    
                    const style = window.getComputedStyle(el);
                    if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                        elements.push({
                            tag: el.tagName.toLowerCase(),
                            text: el.innerText || el.textContent || el.value || el.alt || el.title || '',
                            type: el.type || null,
                            href: el.href || null,
                            bbox: {
                                x: Math.round(rect.left),
                                y: Math.round(rect.top),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                centerX: Math.round(rect.left + rect.width / 2),
                                centerY: Math.round(rect.top + rect.height / 2)
                            }
                        });
                    }
                }
            }
            
            return elements;
        }""")
        
        return elements
    
    async def click_by_bbox(
        self,
        x: int,
        y: int,
        wait_after: float = 0.5
    ) -> Dict[str, Any]:
        """
        Click at specific coordinates using bounding box information.
        More reliable than element selectors for dynamic SPAs.
        
        Args:
            x: X coordinate
            y: Y coordinate
            wait_after: Seconds to wait after click
            
        Returns:
            Dict with click result
        """
        page: Page = self.page
        await self._ensure_page()
        
        result = {
            "success": False,
            "error": None
        }
        
        try:
            await page.mouse.click(x, y)
            await asyncio.sleep(wait_after)
            result["success"] = True
            logger.info(f"Clicked at coordinates ({x}, {y})")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Failed to click at ({x}, {y}): {e}")
        
        return result
