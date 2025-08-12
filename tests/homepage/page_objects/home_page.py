"""
Page Object Model (POM) for the Homepage.
Contains all the locators and page interactions for the homepage.
"""
from playwright.sync_api import Page, expect

class HomePage:
    """Page Object Model for the Homepage."""
    
    # URL will be set in __init__ using the page's base URL
    URL = None
    
    # Locators
    class Locators:
        """All locators for the homepage."""
        # Header
        LOGIN_BUTTON = "button:has-text('Login')"
        
        # Navigation
        NAV_LINKS = {
            'home': "a[href='/']",
            'features': "a[href='#features']",
            'pricing': "a[href='#pricing']",
            'contact': "a[href='#contact']",
            'get_started': "button:has-text('Get started')"
        }
        
        # Main Content
        MAIN_HEADER = "h1"
        MAIN_SUBHEADER = "h2"
        
        # Sections
        SECTIONS = {
            'hero': "section.hero",
            'features': "section#features",
            'how_it_works': "section#how-it-works",
            'testimonials': "section#testimonials",
            'pricing': "section#pricing",
            'cta': "section.cta"
        }
        
        # Buttons
        BUTTONS = {
            'login': "button:has-text('Login')",
            'get_started': "button:has-text('Get started')",
            'contact_sales': "button:has-text('Contact Sales')"
        }
        
        # Forms
        EMAIL_INPUT = "input[type='email']"
        
        # Footer
        FOOTER_LINKS = {
            'privacy': "footer a[href*='privacy']",
            'terms': "footer a[href*='terms']",
            'cookies': "footer a[href*='cookies']"
        }
    
    def __init__(self, page: Page):
        """Initialize with page object."""
        self.page = page
        self.locators = self.Locators()
        # Set the URL using the page's base URL
        self.URL = page.url if page.url != 'about:blank' else 'https://wize-invoice-dev-front.octaprimetech.com/'
    
    # Navigation
    def load(self):
        """Navigate to the homepage."""
        self.page.goto(self.URL)
        self.page.wait_for_load_state('networkidle')
    
    # Actions
    def click_login(self):
        """Click the login button."""
        self.page.locator(self.locators.BUTTONS['login']).first.click()
        self.page.wait_for_load_state('networkidle')
    
    def click_get_started(self):
        """Click the get started button."""
        self.page.locator(self.locators.BUTTONS['get_started']).first.click()
        self.page.wait_for_load_state('networkidle')
    
    # Assertions
    def is_loaded(self) -> bool:
        """Check if the homepage is loaded."""
        try:
            expect(self.page).to_have_title("Invoice AI")
            return True
        except:
            return False
    
    def is_login_button_visible(self) -> bool:
        """Check if the login button is visible."""
        try:
            expect(self.page.locator(self.locators.BUTTONS['login']).first).to_be_visible()
            return True
        except:
            return False
    
    def get_focusable_elements(self):
        """Get all focusable elements on the page."""
        focusable_selectors = [
            'a[href]', 'button', 'input', 'select', 'textarea',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable]',
            'button:not([disabled])',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="textbox"]'
        ]
        return self.page.locator(','.join(focusable_selectors)).all()
    
    # Responsive Helpers
    def set_viewport_size(self, width: int, height: int):
        """Set the viewport size."""
        self.page.set_viewport_size({"width": width, "height": height})
        self.page.wait_for_load_state('networkidle')
    
    def take_screenshot(self, path: str):
        """Take a screenshot of the current viewport."""
        self.page.screenshot(path=path)

    # Performance
    def get_performance_metrics(self):
        """Get page performance metrics."""
        return self.page.evaluate("""() => {
            const [pageNav] = performance.getEntriesByType('navigation');
            return {
                loadTime: pageNav.loadEventEnd - pageNav.startTime,
                domContentLoaded: pageNav.domContentLoadedEventEnd - pageNav.startTime,
                firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
                largestContentfulPaint: performance.getEntriesByName('largest-contentful-paint')[0]?.startTime || 0,
                timeToInteractive: performance.timing.domInteractive - performance.timing.navigationStart
            };
        }""")
