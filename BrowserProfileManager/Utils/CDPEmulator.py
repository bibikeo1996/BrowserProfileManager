import logging

logger = logging.getLogger(__name__)

class CDPEmulator:
    """Helper class to configure mobile emulation and auto-resize OS window via CDP."""
    
    @staticmethod
    def apply_mobile(page, width: int = 375, height: int = 715, user_agent: str = None):
        """
        Applies mobile emulation to the given Playwright page and auto-resizes the physical OS window 
        to perfectly fit the viewport without gray borders (macOS minimum width limits apply).
        
        Args:
            page: A connected Playwright Page object.
            width: Target viewport width (default 375 for iPhone).
            height: Target viewport height (default 715 for iPhone).
            user_agent: Optional custom User-Agent string.
        """
        # Default iPhone UA if not provided
        if not user_agent:
            user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
            
        try:
            # 1. Measure UI Chrome thickness (Toolbar, Borders)
            page.wait_for_load_state("domcontentloaded")
            ui_chrome_width = page.evaluate("window.outerWidth - window.innerWidth")
            ui_chrome_height = page.evaluate("window.outerHeight - window.innerHeight")
            logger.debug("Measured UI Chrome thickness: width=%dpx, height=%dpx", ui_chrome_width, ui_chrome_height)
            
            context = page.context
            client = context.new_cdp_session(page)
            
            # 2. Force resize physical OS window
            try:
                window_info = client.send("Browser.getWindowForTarget")
                client.send("Browser.setWindowBounds", {
                    "windowId": window_info["windowId"],
                    "bounds": {
                        "width": width + ui_chrome_width,
                        "height": height + ui_chrome_height
                    }
                })
                logger.info("Auto-resized physical OS window to %dx%d", width + ui_chrome_width, height + ui_chrome_height)
            except Exception as e:
                logger.warning("Could not auto-resize OS window via CDP: %s", e)
                
            # 3. Activate Simulator & Viewport
            client.send("Emulation.setDeviceMetricsOverride", {
                "width": width,
                "height": height,
                "deviceScaleFactor": 2.0,
                "mobile": True
            })
            
            client.send("Emulation.setTouchEmulationEnabled", {
                "enabled": True,
                "maxTouchPoints": 5
            })
            
            client.send("Emulation.setUserAgentOverride", {
                "userAgent": user_agent
            })
            
            logger.info("Successfully applied mobile emulation (%dx%d).", width, height)
            
        except Exception as e:
            logger.error("Failed to apply mobile emulation: %s", e)
            raise
