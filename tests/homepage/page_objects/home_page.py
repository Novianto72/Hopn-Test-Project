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
        
        # Book a Demo Section
        BOOK_DEMO_SECTION = "section#book-a-demo"
        BOOK_DEMO_FORM = "section#book-a-demo form"
        BOOK_DEMO_FIELDS = {
            'full_name': "input[name='fullName']",
            'email': "input[type='email']",
            'mobile_number': "input[name='mobileNumber']",
            'contact_method': "select[name='favoritConnectionMethod']",
            'message': "textarea[name='message']"
        }
        
        # Success message locators
        SUCCESS_MESSAGE = {
            'container': "div.text-center.py-12",
            'title': "h3.text-3xl.font-bold.text-gray-900.mb-4",
            'description': "p.text-xl.text-gray-600.mb-8",
            'confirmation_banner': r"div.inline-flex.items-center.px-6.py-3.bg-blue-50.rounded-lg.text-\[\#11A193\].font-medium.mb-6"
        }
        BOOK_DEMO_BUTTON = "section#book-a-demo button[type='submit']"
        
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
        # Set the URL using the centralized configuration
        from tests.config.test_config import URLS
        self.URL = page.url if page.url != 'about:blank' else URLS['HOME']
    
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
    
    def is_login_button_visible(self, timeout: int = 5000) -> bool:
        """
        Check if the login button is visible.
        
        Args:
            timeout: Maximum time to wait for the button to be visible (in ms)
            
        Returns:
            bool: True if the login button is visible, False otherwise
        """
        try:
            # First check if we're on the login page (which would mean we're not logged in)
            if 'login' in self.page.url.lower():
                return False
                
            # Try to find the login button with a reasonable timeout
            login_button = self.page.locator(self.locators.BUTTONS['login']).first
            login_button.wait_for(state='visible', timeout=timeout)
            return True
            
        except Exception as e:
            print(f"Login button not found or not visible: {str(e)}")
            print(f"Current URL: {self.page.url}")
            print(f"Page title: {self.page.title()}")
            try:
                # Take a screenshot for debugging
                self.page.screenshot(path='test-results/login_button_not_found.png')
                print("Screenshot saved to test-results/login_button_not_found.png")
            except:
                pass
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
        
    # Book Demo Section Methods
    def navigate_to_book_demo_section(self):
        """Scroll to the Book a Demo section."""
        demo_section = self.page.locator(self.locators.BOOK_DEMO_SECTION)
        demo_section.scroll_into_view_if_needed()
        return demo_section
        
    def fill_demo_form(self, **form_data):
        """Fill out the demo request form.
        
        Args:
            **form_data: Dictionary containing form field data
                Expected keys: full_name, email, mobile_number, contact_method, message
        """
        fields = self.locators.BOOK_DEMO_FIELDS
        
        if 'full_name' in form_data:
            self.page.locator(fields['full_name']).fill(form_data['full_name'])
        if 'email' in form_data:
            self.page.locator(fields['email']).fill(form_data['email'])
        if 'mobile_number' in form_data:
            self.page.locator(fields['mobile_number']).fill(str(form_data['mobile_number']))
        if 'contact_method' in form_data:
            self.page.locator(fields['contact_method']).select_option(form_data['contact_method'])
        if 'message' in form_data:
            self.page.locator(fields['message']).fill(form_data['message'])
    
    def submit_demo_form(self):
        """Submit the demo request form."""
        self.page.locator(self.locators.BOOK_DEMO_BUTTON).click()
        
    def is_form_valid(self):
        """Check if the form is valid (all required fields are filled correctly)."""
        # Check required fields
        required_fields = [
            self.locators.BOOK_DEMO_FIELDS['full_name'],
            self.locators.BOOK_DEMO_FIELDS['email'],
            self.locators.BOOK_DEMO_FIELDS['mobile_number']
        ]
        
        for field in required_fields:
            if not self.page.locator(field).input_value().strip():
                return False
                
        # Basic email validation
        email = self.page.locator(self.locators.BOOK_DEMO_FIELDS['email']).input_value()
        if '@' not in email or '.' not in email:
            return False
            
        return True
