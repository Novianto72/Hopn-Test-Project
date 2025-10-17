from playwright.sync_api import Page, expect, TimeoutError
import time
import re

class CostCentersPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/cost-center"
        
        # Common locators
        # Search input locator using exact placeholder match
        self.search_input = page.get_by_placeholder("Search cost centers...", exact=True)
        
        # Action buttons with exact text matching
        self.new_cost_center_btn = page.get_by_role("button", name="New Cost Center", exact=True)
        self.edit_cost_center_btn = page.get_by_role("button", name="Edit cost center", exact=True)
        self.refresh_btn = page.get_by_role("button", name="Refresh")
        
        # Status messages
        self.no_data_message = page.get_by_text("No cost centers found.")
        
        # Form fields
        # Using data-slot attribute for more reliable element selection
        self.name_input = page.locator('input[data-slot="input"]#name')
        
        # Counter locators based on actual DOM structure
        self.total_counter = page.locator("div:has-text('Total Cost Centers') + div.text-2xl.font-bold")
        self.active_counter = page.locator("div:has-text('Active Centers') + div.text-2xl.font-bold.text-green-600")
        self.inactive_counter = page.locator("div:has-text('Inactive Centers') + div.text-2xl.font-bold")
        
        # Simpler counter locators from File 2
        self.simple_total_counters = page.locator("div:has-text('Total Cost Centers') + div")
        self.simple_active_counters = page.locator("div:has-text('Active Centers') + div.text-green-600")
        self.simple_inactive_counters = page.locator("div:has-text('Inactive Centers') + div.text-red-600")
        
        # Debug: Save a screenshot of the entire page
        page.screenshot(path="test-results/full_page.png")
        
        # Pagination locators
        self.pagination = page.locator(".pagination")
    
    def navigate(self):
        self.page.goto(self.url)
        self.page.wait_for_load_state("domcontentloaded")
        return self
        
    def search(self, query: str):
        """Search for a cost center by name"""
        try:
            # Wait for the search input to be visible and enabled
            search_input = self.page.get_by_placeholder("Search cost centers...", exact=True)
            search_input.wait_for(state='visible', timeout=10000)
            
            # Clear any existing text and type the query
            search_input.fill('')  # Clear first
            search_input.type(query, delay=100)  # Type with small delay
            
            # Wait a moment for the search to complete
            self.page.wait_for_timeout(500)
            
            # Press Enter to submit the search
            search_input.press("Enter")
            
            # Wait for the table to update after search
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)  # Additional small delay
            
            return self
            
        except Exception as e:
            # Take a screenshot for debugging
            self._screenshot("search_error")
            raise Exception(f"Error in search method: {str(e)}")
        
    def is_item_in_table(self, name: str, timeout: int = 5000) -> bool:
        """Check if a cost center exists in the table"""
        try:
            self.page.wait_for_selector(f"tr:has-text('{name}')", timeout=timeout)
            return True
        except TimeoutError:
            return False
            
    def delete_item(self, name: str):
        """
        Delete a cost center by name using the triple dot menu
        
        Args:
            name: Name of the cost center to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            # Find the row containing the cost center name
            row = self.page.locator(f"tr:has-text('{name}')")
            
            # Click the triple dot menu button
            menu_button = row.locator("button[aria-haspopup='menu']")
            menu_button.click()
            
            # Set up a dialog handler to accept the confirmation
            def handle_dialog(dialog):
                print(f"Dialog message: {dialog.message}")
                dialog.accept()  # Clicks 'OK' or 'Delete' on the dialog
            
            # Listen for the dialog before clicking delete
            self.page.on('dialog', handle_dialog)
            
            # Click the Delete option from the menu
            self.page.get_by_role("menuitem", name="Delete").click()
            
            # Wait for the operation to complete
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)  # Small delay for the update
            
            print(f"Successfully deleted cost center: {name}")
            return True
            
        except Exception as e:
            print(f"Error deleting cost center '{name}': {str(e)}")
            return False
            
    def fill_name_field(self, name: str):
        """Fill the name field in the cost center form"""
        self.page.fill('input#name', name)
        return self
        
    def submit_form(self):
        """Submit the cost center form"""
        # Using exact button text match for reliability
        submit_button = self.page.get_by_role("button", name="Add cost center", exact=True)
        submit_button.click()
        self.page.wait_for_load_state("domcontentloaded")
        return self
        
    def click_new_cost_center(self):
        """Click the New Cost Center button with improved reliability"""
        try:
            print("Attempting to click New Cost Center button...")
            
            # Take a screenshot before clicking
            self.page.screenshot(path="test-results/before_click_new_cost_center.png")
            
            # Try the most reliable locator first
            try:
                self.new_cost_center_btn.wait_for(state="visible", timeout=5000)
                self.new_cost_center_btn.click()
                print("Clicked New Cost Center button using exact locator")
            except Exception as e:
                print(f"Primary locator failed, falling back to alternatives: {str(e)}")
                
                # Fallback to alternative locators if needed
                button_selectors = [
                    self.page.get_by_role("button", name=re.compile(r"New Cost Center", re.IGNORECASE)),
                    self.page.locator("button:has-text('New Cost Center')"),
                    self.page.locator("button:has-text('New')")
                ]
                
                clicked = False
                for btn in button_selectors:
                    try:
                        if btn.is_visible():
                            print(f"Found button with text: {btn.text_content()}")
                            btn.click(timeout=5000)
                            clicked = True
                            break
                    except Exception as e:
                        print(f"Button not found with selector: {e}")
                
                if not clicked:
                    # Last resort: use JavaScript to find and click the button
                    print("Using JavaScript fallback to click the button")
                    self.page.evaluate('''() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const btn = buttons.find(b => 
                            b.textContent.trim() === 'Add cost center' || 
                            b.textContent.includes('New Cost Center') || 
                            b.textContent.includes('New')
                        );
                        if (btn) btn.click();
                    }''')
            
            # Wait for the form to appear
            try:
                self.page.wait_for_selector("[role=dialog] form, .modal form, [data-testid=modal] form", timeout=5000)
                print("Form detected after button click")
            except Exception as e:
                print(f"Warning: Form not detected after clicking New Cost Center: {str(e)}")
                # Take a screenshot for debugging
                self.page.screenshot(path="test-results/after_click_new_cost_center.png")
                
            return True
            
        except Exception as e:
            print("Error in click_new_cost_center:", str(e))
            self.page.screenshot(path="test-results/click_new_cost_center_error.png")
            raise
            
    def simple_search(self, query: str):
        """Simpler implementation of search with the given query"""
        try:
            self.search_input.fill(query)
            self.page.wait_for_load_state("domcontentloaded")
            # Add a small delay to ensure search completes
            self.page.wait_for_timeout(1000)
        except Exception as e:
            print(f"Error during simple search for '{query}': {e}")
            raise
    
    def get_counter_values(self):
        """Returns a dictionary with total, active, and inactive counters as strings
        with detailed error information for debugging.
        """
        result = {'total': '0', 'active': '0', 'inactive': '0'}
        
        def get_counter_value(counter_locator, counter_name):
            try:
                print(f"\n=== Checking {counter_name} counter ===")
                print(f"Locator: {counter_locator}")
                
                # Check if element is visible
                is_visible = counter_locator.is_visible()
                print(f"Is visible: {is_visible}")
                
                if is_visible:
                    # Get the text content
                    text = counter_locator.text_content().strip()
                    print(f"Raw text content: {text}")
                    return text if text else '0'
                else:
                    print(f"Warning: {counter_name} counter is not visible")
                    return '0'
                    
            except Exception as e:
                print(f"Error getting {counter_name} counter: {str(e)}")
                # Take a screenshot of just this counter's container if possible
                try:
                    counter_locator.screenshot(path=f"test-results/{counter_name.lower()}_error.png")
                    print(f"Screenshot saved: test-results/{counter_name.lower()}_error.png")
                except:
                    pass
                return 'error'
        
        try:
            # Get each counter value individually
            result['total'] = get_counter_value(self.total_counter, "Total")
            result['active'] = get_counter_value(self.active_counter, "Active")
            result['inactive'] = get_counter_value(self.inactive_counter, "Inactive")
            
            # Print final results
            print("\n=== Final Counter Values ===")
            for name, value in result.items():
                print(f"{name}: {value}")
                
            return result
            
        except Exception as e:
            print(f"\n=== Critical Error in get_counter_values ===")
            print(f"Error: {str(e)}")
            # Take a full page screenshot   
            self.page.screenshot(path="test-results/critical_counter_error.png")
            print("Full page screenshot saved: test-results/critical_counter_error.png")
            return result
            
    def get_simple_counter_values(self):
        """Simpler implementation of counter value retrieval that handles hidden elements"""
        try:
            # First, try to get the text directly from the page
            page_content = self.page.content()
            
            # Look for the "Showing X of Y" pattern in the entire page
            import re
            showing_match = re.search(r'Showing \d+ of (\d+)', page_content)
            if showing_match:
                total = showing_match.group(1)
                print(f"Found total cost centers from 'Showing' text: {total}")
                return {
                    'total': total,
                    'active': total,  # Assuming all are active if we can't determine
                    'inactive': '0'   # Assuming none are inactive if we can't determine
                }
                
            # If that fails, try to find the element with JavaScript
            print("Could not find 'Showing' text, trying JavaScript fallback...")
            counters = {'total': '0', 'active': '0', 'inactive': '0'}
            
            # Try to get the counter values using JavaScript
            try:
                # Get all text content from the page
                all_text = self.page.evaluate('document.body.innerText')
                
                # Look for the "Showing X of Y" pattern
                showing_match = re.search(r'Showing (\d+) of (\d+)', all_text)
                if showing_match:
                    showing = showing_match.group(1)
                    total = showing_match.group(2)
                    print(f"\n=== Counter Values Found ===")
                    print(f"Currently showing: {showing} of {total} cost centers")
                    print(f"Active: {showing} (assumed same as showing)")
                    print(f"Inactive: 0 (assumed)")
                    print("==========================\n")
                    return {
                        'total': total,
                        'active': showing,
                        'inactive': '0'
                    }
                    
                # If we still can't find it, try to find the counters by their labels
                counter_selectors = {
                    'total': "div:has-text('Total Cost Centers')",
                    'active': "div:has-text('Active Centers')",
                    'inactive': "div:has-text('Inactive Centers')"
                }
                
                for counter_type, selector in counter_selectors.items():
                    try:
                        # Use JavaScript to find the element
                        value = self.page.evaluate(f'''() => {{
                            const element = Array.from(document.querySelectorAll('div'))
                                .find(el => el.textContent.includes('{counter_type.split()[0]}'));
                            return element ? element.nextElementSibling?.textContent?.trim() : '0';
                        }}''')
                        if value and value.isdigit():
                            counters[counter_type] = value
                            print(f"Found {counter_type} counter: {value}")
                    except Exception as e:
                        print(f"Error getting {counter_type} counter with JS: {str(e)}")
                
                print(f"All counters found: {counters}")
                return counters
                
            except Exception as js_e:
                print(f"JavaScript fallback failed: {str(js_e)}")
                raise
                
        except Exception as e:
            print(f"Error in get_simple_counter_values: {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path="test-results/counter_error.png")
            # Return default values
            return {'total': '0', 'active': '0', 'inactive': '0'}

    def click_refresh(self):
        """Click the refresh button and wait for the page to update"""
        try:
            # Find the refresh button by role and text
            refresh_button = self.page.get_by_role("button", name="Refresh", exact=True)
            refresh_button.wait_for(state="visible", timeout=10000)
            
            # Get current counter values before refresh
            before_refresh = self.get_counter_values()
            print("Counters before refresh:", before_refresh)
            
            # Click the refresh button
            refresh_button.click()
            
            # Wait for the page to update - wait for a network request to complete
            with self.page.expect_response(lambda response: "cost-centers" in response.url, timeout=10000) as response_info:
                pass  # Wait for any cost-centers related request to complete
                
            # Wait for the counters to be updated
            self.page.wait_for_timeout(1000)  # Small delay for UI to update
            
            # Get new counter values
            after_refresh = self.get_counter_values()
            print("Counters after refresh:", after_refresh)
            
            return before_refresh, after_refresh
            
        except Exception as e:
            print(f"Error in click_refresh: {str(e)}")
            self.page.screenshot(path="refresh_error.png")
            raise
    
    def click_new_cost_center(self):
        """Click the New Cost Center button"""
        try:
            # Add debug information
            print("Clicking New Cost Center button...")
            print(f"Button is visible: {self.new_cost_center_btn.is_visible()}")
            print(f"Button is enabled: {self.new_cost_center_btn.is_enabled()}")
            
            # Take a screenshot before clicking
            self.page.screenshot(path="before_click_new_cost_center.png")
            
            # Just click the button without waiting for modal
            self.new_cost_center_btn.click()
            print("Button clicked, returning True")
            return True
            
        except Exception as e:
            self._handle_error(e, "error_clicking_new_cost_center.png")
    
    def set_page_size(self, size: int):
        """Set the number of records per page
        
        Args:
            size: Number of records to show per page (5, 10, 25, 50)
        """
        try:
            # Use XPath locator with exact class matching
            select_selector = '//select[@class="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white"]'
            
            print("Waiting for page size selector to be visible...")
            select_element = self.page.locator(select_selector)
            select_element.wait_for(state="visible", timeout=10000)
            
            # Log the current state before changing
            current_value = select_element.input_value()
            print(f"Current page size: {current_value}")
            
            # Get available options
            options = select_element.evaluate('''select => {
                return Array.from(select.options).map(option => ({
                    value: option.value,
                    text: option.text,
                    selected: option.selected
                }));
            }''')
            print(f"Available page size options: {options}")
            
            # Check if the requested size is available
            available_sizes = [str(opt['value']) for opt in options]
            if str(size) not in available_sizes:
                raise ValueError(f"Page size {size} is not available. Available sizes: {', '.join(available_sizes)}")
            
            # Select the desired option
            print(f"Setting page size to {size}...")
            select_element.select_option(str(size))
            
            # Wait for the selection to take effect
            self.page.wait_for_timeout(1000)  # Small delay for UI to update
            
            # Verify the selection was successful
            new_value = select_element.input_value()
            print(f"New page size: {new_value}")
            
            if str(new_value) != str(size):
                raise ValueError(f"Failed to set page size to {size}. Current value: {new_value}")
                
            print(f"Successfully set page size to {size} records per page")
            
            # Wait for the table to update
            self.page.wait_for_load_state("networkidle")
            return self.get_pagination_info()
            
        except Exception as e:
            print(f"Error in set_page_size({size}): {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path="debug_page_size_error.png")
            self._handle_error(e, "page_size_error.png")
    
    def get_pagination_info(self):
        """Returns current page and total pages"""
        try:
            # Wait for pagination section to be visible
            pagination_section = self.page.locator(
                "div:has-text('Rows per page') >> div.bg-gray-50"
            )
            pagination_section.wait_for(state="visible", timeout=5000)
            
            # Get the specific element with the page numbers
            page_element = pagination_section.evaluate("""
                () => {
                    const elements = document.querySelectorAll('div');
                    for (const el of elements) {
                        if (el.className === 'text-sm font-medium text-gray-900') {
                            const text = el.textContent.trim();
                            if (text.includes('Page') && text.includes('of')) {
                                return text;
                            }
                        }
                    }
                    return null;
                }
            """)
            
            if not page_element:
                raise ValueError("Could not find pagination element")
            
            # Extract current and total pages from the text
            parts = page_element.split('of')
            if len(parts) != 2:
                raise ValueError("Invalid pagination format")
                
            # Remove "Page " from the start and get the number
            current_page = int(parts[0].replace('Page ', '').strip())
            total_pages = int(parts[1].strip())
            
            return {
                'current': current_page,
                'total': total_pages
            }
        except Exception as e:
            print(f"Error in get_pagination_info: {str(e)}")
            self.page.screenshot(path="pagination_error.png")
            raise
            
            if current_page is None or total_pages is None:
                raise ValueError("Could not find pagination information")
                
            return {
                'current': current_page,
                'total': total_pages
            }
        except Exception as e:
            print(f"Error in get_pagination_info: {str(e)}")
            self.page.screenshot(path="pagination_error.png")
            raise

    def wait_for_loading_animation_to_disappear(self, timeout: int = 10000):
        """Wait for the loading animation to disappear
        
        Args:
            timeout: Maximum time to wait in milliseconds (default: 10000ms)
        """
        try:
            # Wait for the loading animation to be hidden or removed
            loading_selector = "svg.lucide-loader-circle.animate-spin"
            self.page.wait_for_selector(loading_selector, state='hidden', timeout=timeout)
        except:
            # If the loading element is not found at all, that's also fine
            pass
            
    def _screenshot(self, name: str):
        """Take a screenshot and save it to the test-results directory"""
        import os
        os.makedirs("test-results", exist_ok=True)
        screenshot_path = f"test-results/{name}.png"
        self.page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        return screenshot_path
        
    def _handle_error(self, e, screenshot_name):
        """Helper method to handle errors consistently"""
        self._screenshot(screenshot_name)
        raise e
