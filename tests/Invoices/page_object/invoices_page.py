import os
import time
from playwright.sync_api import Page, expect
from tests.page_components.table_component import TableComponent

class InvoicesPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/invoices"
        self.table = TableComponent(page, table_selector='table[data-slot="table"]')
        
        # Common locators based on DOM
        self.search_input = page.locator("input[placeholder='Search invoices...']")
        self.refresh_btn = page.get_by_role("button", name="Refresh")
        self.new_invoice_btn = page.get_by_role("button", name="New Invoice")
        
        # Counter locator based on DOM
        self.total_invoices_counter = page.locator("div:has-text('Total Invoices') + div.text-2xl.font-bold")
        
        # Table headers based on DOM
        self.table_headers = {
            "name": "Name",
            "expense_type": "Expense Type",
            "type": "Type",
            "date_added": "Date Added",
            "actions": "Actions"
        }
        
        # New Invoice Overlay locators
        self.overlay = {
            'container': page.locator('div[data-slot="card"]').filter(has_text='New Invoice'),
            'title': page.locator('div[data-slot="card-title"]:has-text("New Invoice")'),
            'close_btn': page.locator('div[data-slot="card-title"] svg.lucide-x'),
            'description': page.locator('div[data-slot="card-description"]'),
            'cost_center_dropdown': {
                'trigger': page.locator('button[aria-controls^="radix-"][aria-expanded]').nth(0),
                'value': 'Select a cost center'
            },
            'expense_type_dropdown': {
                'trigger': page.locator('button[aria-controls^="radix-"][aria-expanded]').nth(1),
                'value': 'Select a cost center first',
                'disabled': True
            },
            'type_radio': {
                'debit': page.locator('input[type="radio"][value="Debit"]'),
                'credit': page.locator('input[type="radio"][value="Credit"]')
            },
            'file_upload': {
                'input': page.locator('input[type="file"]'),
                'drop_zone': page.locator('label[for="file"]'),
                'drop_text': page.locator('label[for="file"] span:has-text("Click to upload or drag and drop")')
            },
            'cancel_btn': page.locator('button:has-text("Cancel")'),
            'add_invoice_btn': page.locator('button:has-text("Add Invoice")')
        }

    def navigate(self):
        """Navigate to the invoices page"""
        self.page.goto(self.url)
        
    def open_new_invoice_overlay(self):
        """Click the New Invoice button to open the overlay"""
        self.new_invoice_btn.click()
        expect(self.overlay['title']).to_be_visible()
        
    def close_new_invoice_overlay(self):
        """Close the New Invoice overlay using the close button"""
        try:
            if self.overlay['close_btn'].is_visible():
                self.overlay['close_btn'].click()
                # Wait for the overlay to be hidden with a timeout
                try:
                    self.overlay['title'].wait_for(state='hidden', timeout=10000)  # 10 seconds timeout
                except Exception as e:
                    print("Warning: Overlay did not close cleanly:", str(e))
                    # Try to close the modal by clicking outside if the close button didn't work
                    self.page.mouse.click(x=10, y=10)
        except Exception as e:
            print("Warning: Could not close overlay:", str(e))
        
    def cancel_new_invoice(self):
        """Click the Cancel button in the New Invoice overlay"""
        self.overlay['cancel_btn'].click()
        expect(self.overlay['title']).to_be_hidden()
    
    def wait_for_upload_complete(self, filename: str, timeout: float = 30000):
        """
        Wait for file upload to complete by checking multiple indicators
        
        Args:
            filename: Name of the file being uploaded (without path)
            timeout: Maximum time to wait in milliseconds (default: 30 seconds)
            
        Returns:
            bool: True if upload is complete, False if timeout
        """
        timeout_seconds = timeout / 1000  # Convert to seconds
        start_time = time.time()
        
        # Try multiple ways to detect successful upload
        while (time.time() - start_time) < timeout_seconds:
            try:
                # Check if the file input has the file set
                file_input = self.page.locator('input[type="file"]#file')
                input_value = file_input.input_value()
                if filename in input_value:
                    print(f"File upload complete: {filename}")
                    return True
                    
                # Check if the filename appears in the UI
                filename_element = self.page.get_by_text(filename, exact=True).first
                if filename_element.is_visible():
                    print(f"File upload complete (UI indicator): {filename}")
                    return True
                    
                # Check for any success/upload complete indicators
                success_indicators = [
                    'upload complete',
                    'file uploaded',
                    'successfully uploaded'
                ]
                
                for indicator in success_indicators:
                    if self.page.get_by_text(indicator, exact=False).is_visible():
                        print(f"File upload complete (success indicator): {indicator}")
                        return True
                        
                # Small delay before next check
                self.page.wait_for_timeout(500)
                
            except Exception as e:
                # If any check fails, continue trying until timeout
                print(f"Upload check failed, retrying... Error: {str(e)}")
                self.page.wait_for_timeout(500)
        
        print(f"Timeout waiting for file upload to complete: {filename}")
        return False

    def upload_invoice_file(self, file_path: str, wait_for_complete: bool = True):
        """
        Upload a file to the invoice form using Playwright's file chooser pattern
        
        Args:
            file_path: Path to the file to upload
            wait_for_complete: Whether to wait for the upload to complete
        """
        try:
            # Get the file size for logging
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            filename = os.path.basename(file_path)
            print(f"Uploading file: {filename} ({file_size:.2f} MB)")
            
            # Use Playwright's file chooser pattern with a more specific locator
            with self.page.expect_file_chooser() as fc_info:
                # Click the specific drop zone element that has the text about drag and drop
                drop_zone = self.page.locator('label[for="file"].cursor-pointer')
                drop_zone.wait_for(state='visible')
                drop_zone.click()
            
            # Get the file chooser and set the file
            file_chooser = fc_info.value
            file_chooser.set_files(file_path)
            
            if wait_for_complete:
                # Adjust timeout based on file size (1 second per MB, minimum 5 seconds)
                timeout = max(5000, file_size * 1000)  # Convert MB to ms
                if not self.wait_for_upload_complete(filename, timeout):
                    raise TimeoutError(f"File upload did not complete within {timeout/1000} seconds")
            
            return True
            
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            # Screenshot on failure is handled by the test framework
            # self.page.screenshot(path="file_upload_error.png")
            raise
            
    def select_invoice_type(self, invoice_type='debit'):
        """
        Select the invoice type (debit or credit)
        
        Args:
            invoice_type (str): 'debit' or 'credit'
        """
        if invoice_type.lower() == 'credit':
            self.overlay['type_radio']['credit'].check()
        else:
            self.overlay['type_radio']['debit'].check()
    
    def click_add_invoice(self):
        """Click the Add Invoice button"""
        self.overlay['add_invoice_btn'].click()
        
    def is_overlay_visible(self):
        """Check if the New Invoice overlay is visible"""
        return self.overlay['title'].is_visible()
        
    def is_upload_timeout_error_visible(self):
        """Check if the upload timeout error message is visible"""
        try:
            error_locator = self.page.locator('div.bg-red-50:has-text("Upload timeout")')
            return error_locator.is_visible()
        except Exception as e:
            print(f"Error checking for upload timeout: {str(e)}")
            return False
            
    def wait_for_upload_button_state(self, expected_text: str, timeout: int = 120000):
        """
        Wait for the upload button to have the expected text
        
        Args:
            expected_text: The text to wait for (e.g., 'Uploading...' or 'Add Invoice')
            timeout: Maximum time to wait in milliseconds (default: 120 seconds)
            
        Returns:
            bool: True if the button with expected text is found, False otherwise
        """
        # First try to find by role and name
        button = self.page.get_by_role('button', name=expected_text, exact=True)
        try:
            button.wait_for(state='visible', timeout=timeout/1000)
            return True
        except Exception:
            # Fallback: Try to find any button containing the text
            try:
                button = self.page.locator(f'button:has-text("{expected_text}")')
                button.wait_for(state='visible', timeout=5000)  # Shorter timeout for fallback
                return True
            except Exception:
                return False
        self.page.goto(self.url)
        self.page.wait_for_selector("h1:has-text('Invoices')")

    def click_refresh(self):
        """Click the refresh button"""
        try:
            self.refresh_btn.click()
            return self.wait_for_loading_animation_to_disappear()
        except Exception as e:
            print(f"Error clicking refresh: {str(e)}")
            raise

    def click_new_invoice(self):
        """Click the New Invoice button"""
        try:
            self.new_invoice_btn.click()
            # Wait for modal to appear
            self.page.wait_for_selector("div[role='dialog']")
        except Exception as e:
            print(f"Error clicking new invoice: {str(e)}")
            raise

    def get_total_invoices(self):
        """Get the total invoices count"""
        try:
            return self.total_invoices_counter.text_content().strip()
        except Exception as e:
            print(f"Error getting total invoices: {str(e)}")
            raise

    def wait_for_loading_animation_to_disappear(self, max_retries: int = 3, retry_timeout: int = 5000):
        """Wait for the loading animation to disappear with retry logic
        
        Args:
            max_retries: Maximum number of times to retry checking
            retry_timeout: Timeout in milliseconds for each retry
            
        Returns:
            bool: True if loading animation disappeared, False if retries exceeded
        """
        loading_animation = self.page.locator("svg.lucide-loader-circle")
        
        for attempt in range(max_retries):
            try:
                # First try to wait for the loading animation to disappear
                loading_animation.wait_for(state="hidden", timeout=retry_timeout)
                return True
            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"Loading animation still visible after {max_retries} retries")
                    return False
                print(f"Loading animation still visible, retrying ({attempt + 1}/{max_retries})...")
                self.page.wait_for_timeout(1000)  # Small delay before next retry
        return False

    def search_invoices(self, search_term: str):
        """Search for invoices using the search input
        
        Args:
            search_term: Term to search for
        """
        try:
            self.search_input.fill(search_term)
            self.wait_for_loading_animation_to_disappear()
        except Exception as e:
            print(f"Error searching invoices: {str(e)}")
            raise
            
    def select_cost_center(self, cost_center_name: str = None):
        """
        Select a cost center from the dropdown. If no name is provided, selects the first available option.
        
        Args:
            cost_center_name: (Optional) Name of the cost center to select. If None, selects the first option.
        """
        try:
            # Click the cost center dropdown
            dropdown_trigger = self.overlay['cost_center_dropdown']['trigger']
            dropdown_trigger.click()
            
            # Wait for the dropdown items to appear with a longer timeout
            listbox = self.page.locator('div[role="listbox"]')
            listbox.wait_for(state='visible', timeout=10000)
            
            # Get all available options
            options = self.page.locator('div[role="option"]').all()
            if not options:
                raise ValueError("No cost center options available in the dropdown")
                
            # If no specific name provided, select the first option
            if cost_center_name is None:
                option = options[0]
                cost_center_name = option.text_content()
                print(f"Selecting first available cost center: {cost_center_name}")
            else:
                # Try to find the specific option
                option = self.page.locator(f'div[role="option"]:has-text("{cost_center_name}")').first
                
            # Click the option
            option.scroll_into_view_if_needed()
            option.click(force=True)
            
            # Wait for the dropdown to close
            listbox.wait_for(state='hidden', timeout=10000)
            
            # Small delay to ensure the selection is processed
            self.page.wait_for_timeout(500)
            
            return cost_center_name
            
        except Exception as e:
            # Screenshot on failure is handled by the test framework
            # self.page.screenshot(path="cost_center_selection_error.png")
            print(f"Error selecting cost center: {str(e)}")
            print(f"Available options: {[el.text_content() for el in self.page.locator('div[role="option"]').all()]}")
            raise
            
    def select_expense_type(self, expense_type_name: str = None):
        """
        Select an expense type from the dropdown. If no name is provided, selects the first available option.
        
        Args:
            expense_type_name: (Optional) Name of the expense type to select. If None, selects the first option.
        """
        try:
            # Click the expense type dropdown
            dropdown_trigger = self.overlay['expense_type_dropdown']['trigger']
            dropdown_trigger.click()
            
            # Wait for the dropdown items to appear with a longer timeout
            listbox = self.page.locator('div[role="listbox"]')
            listbox.wait_for(state='visible', timeout=10000)
            
            # Get all available options
            options = self.page.locator('div[role="option"]').all()
            if not options:
                raise ValueError("No expense type options available in the dropdown")
                
            # If no specific name provided, select the first option
            if expense_type_name is None:
                option = options[0]
                expense_type_name = option.text_content()
                print(f"Selecting first available expense type: {expense_type_name}")
            else:
                # Try to find the specific option
                option = self.page.locator(f'div[role="option"]:has-text("{expense_type_name}")').first
            
            # Click the option
            option.scroll_into_view_if_needed()
            option.click(force=True)
            
            # Wait for the dropdown to close
            listbox.wait_for(state='hidden', timeout=10000)
            
            # Small delay to ensure the selection is processed
            self.page.wait_for_timeout(500)
            
            return expense_type_name
            
        except Exception as e:
            # Screenshot on failure is handled by the test framework
            # self.page.screenshot(path="expense_type_selection_error.png")
            print(f"Error selecting expense type: {str(e)}")
            print(f"Available options: {[el.text_content() for el in self.page.locator('div[role="option"]').all()]}")
            raise
