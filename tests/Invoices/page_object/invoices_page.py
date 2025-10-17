import os
import time
from playwright.sync_api import Page, expect
from tests.page_components.table_component import TableComponent

class InvoicesPage:
    def __init__(self, page: Page):
        self.page = page
        from tests.config.test_config import URLS
        self.url = URLS["INVOICES"]
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
                'select_files_btn': page.locator('button:has-text("Select Files")'),
                'uploaded_files_section': page.locator('//div[@class="mt-4 space-y-2"]'),
                'drop_zone': page.locator('label[for="file"]'),
                'drop_text': page.locator('label[for="file"] span:has-text("Click to upload or drag and drop")'),
                'selected_files_section': page.locator('div.text-sm.font-medium:has-text("Selected Files") + div'),
                'selected_files': page.locator('div.flex.items-center.justify-between.p-2.bg-blue-50.rounded-md'),
                'file_name': page.locator('div.text-sm.font-medium.text-blue-700'),
                'file_size': page.locator('div.text-xs.text-blue-600'),
                'remove_file_btn': page.locator('button:has(svg.lucide-trash-2)'),
                'file_icon': page.locator('svg.lucide-file-text')
            },
            'warning_messages': {
                'file_already_selected': page.locator('div.bg-red-50.border-red-200.text-red-800:has-text("File already selected")')
            },
            'cancel_btn': page.locator('button:has-text("Cancel")'),
            'add_invoice_btn': page.locator('button:has-text("Add Invoice")'),
            'error_message': page.locator('div.bg-red-50.border-red-200.text-red-800:has-text("Failed to fetch")')
        }

    def navigate(self, url=None):
        """
        Navigate to the invoices page
        
        Args:
            url: (Optional) URL to navigate to. If not provided, uses the default invoices URL.
        """
        target_url = url if url is not None else self.url
        self.page.goto(target_url)
        
    def open_new_invoice_overlay(self, timeout=30000):
        """
        Click the New Invoice button to open the overlay
        
        Args:
            timeout: Maximum time to wait for the overlay to appear (in milliseconds)
        """
        try:
            # Wait for the button to be visible and enabled
            button = self.page.locator('button:has-text("New Invoice")')
            button.wait_for(state='visible', timeout=timeout/1000)
            
            # Scroll the button into view using Playwright's built-in method
            button.scroll_into_view_if_needed()
            
            # Click the button
            button.click()
            
            # Wait for the overlay to be fully visible
            self.page.wait_for_selector('div[data-slot="card"]', state='visible', timeout=timeout/1000)
            
            # Additional check for the title
            expect(self.overlay['title']).to_be_visible(timeout=timeout/1000)
            
        except Exception as e:
            # Take a screenshot for debugging
            screenshot_path = os.path.join(os.getcwd(), "test_results", "open_modal_error.png")
            self.page.screenshot(path=screenshot_path, full_page=True)
            
            # Get page content for debugging
            page_content = self.page.content()
            debug_path = os.path.join(os.getcwd(), "test_results", "page_content.html")
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(page_content)
                
            print(f"Error opening New Invoice overlay: {str(e)}")
            print(f"Screenshot saved to: {screenshot_path}")
            print(f"Page content saved to: {debug_path}")
            raise
        
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
            
    def is_invoice_creation_overlay_visible(self, max_attempts=3, wait_time=5):
        """
        Check if the invoice creation overlay is visible with retry logic.
        
        Args:
            max_attempts (int): Maximum number of attempts to check
            wait_time (int): Time to wait between attempts in seconds
            
        Returns:
            bool: True if overlay is visible, False if not visible after max_attempts
        """
        print("\nChecking if invoice creation overlay is visible...")
        for attempt in range(max_attempts):
            try:
                # More specific locator for the invoice creation overlay
                overlay = self.page.locator('div[data-slot="card"]:has(h2:has-text("New Invoice"))')
                is_visible = overlay.is_visible()
                print(f"Attempt {attempt + 1}/{max_attempts}: Overlay visible = {is_visible}")
                
                if is_visible:
                    return True
                
                # If we're not on the last attempt, wait before trying again
                if attempt < max_attempts - 1:
                    print(f"Waiting {wait_time} seconds before next attempt...")
                    self.page.wait_for_timeout(wait_time * 1000)  # Convert to milliseconds
                    
            except Exception as e:
                print(f"Error checking overlay visibility: {str(e)}")
                # If there's an error checking visibility, consider it as not visible
                return False
                
        print("Overlay not found after all attempts")
        return False
        
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
    
    def click_add_invoice(self, expected_file_count: int = None):
        """
        Click the Add Invoice button, handling both single and multiple file uploads.
        
        Args:
            expected_file_count: The expected number of files being uploaded. If None,
                              will use the current count of uploaded files.
        """
        if expected_file_count is None:
            # Get the current count of uploaded files if not provided
            expected_file_count = self.get_uploaded_files_count()
        
        # Determine the expected button text based on file count
        if expected_file_count == 1:
            button_text = "Add Invoice"
        else:
            button_text = f"Upload {expected_file_count} Files"
        
        # Create a dynamic locator for the button with the expected text
        add_invoice_btn = self.page.locator(f'button:has-text("{button_text}")')
        expect(add_invoice_btn).to_be_visible(timeout=30000)  # 30 seconds timeout
        
        # Scroll the button into view and click it
        add_invoice_btn.scroll_into_view_if_needed()
        
        # Wait for the button to be clickable
        self.page.wait_for_timeout(1000)  # Small delay to ensure button is ready
        
        # Click the button
        add_invoice_btn.click()
        
        # Wait for the overlay to be hidden with a timeout
        try:
            # Wait for the overlay to be hidden
            self.overlay['title'].wait_for(state='hidden', timeout=30000)  # 30 seconds timeout
            print("Successfully waited for overlay to be hidden")
        except Exception as e:
            print(f"Warning: Overlay did not hide after clicking Add Invoice: {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path="overlay_not_hidden.png")
        
        # Additional wait to ensure everything is settled
        self.page.wait_for_load_state('networkidle')
        self.page.wait_for_timeout(1000)  # Small delay for any final UI updates
        
    def is_overlay_visible(self):
        """Check if the new invoice overlay is visible"""
        return self.overlay['title'].is_visible()
        
    def upload_invoice_files(self, file_paths):
        """
        Upload multiple invoice files
        
        Args:
            file_paths (list): List of file paths to upload
        """
        # Get the absolute path of the test files directory
        test_files_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'test_data',
            'invoices'
        )
        
        # Upload each file
        for file_name in file_paths:
            file_path = os.path.join(test_files_dir, file_name)
            with self.page.expect_file_chooser() as fc_info:
                self.page.get_by_role('button', name='Upload Files').click()
            file_chooser = fc_info.value
            file_chooser.set_files(file_path)
            
            # Wait for the file to be processed
            self.page.wait_for_selector(f'text={file_name}')
            
        return len(file_paths)
        
    def is_upload_timeout_error_visible(self):
        """Check if the upload timeout error message is visible
        
        Returns:
            bool: True if the upload timeout error is visible, False otherwise
        """
        try:
            error_locator = self.page.locator('div.bg-red-50:has-text("Upload timeout")')
            return error_locator.is_visible()
        except Exception as e:
            print(f"Error checking for upload timeout: {str(e)}")
            return False
            
    def get_file_locator_by_name(self, file_name):
        """Get locator for a file in the selected files section by its name
        
        Args:
            file_name (str): Name of the file to locate
            
        Returns:
            Locator: Playwright locator for the file element
        """
        return self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            
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
            print("Clicking expense type dropdown...")
            # Wait for the dropdown to be clickable and click it
            self.overlay['expense_type_dropdown']['trigger'].click()
            
            # Wait for the dropdown options to be visible with a longer timeout
            listbox = self.page.locator('div[role="listbox"]')
            listbox.wait_for(state='visible', timeout=30000)
            
            # Wait a moment for options to load
            self.page.wait_for_timeout(1000)
            
            # Get all available options with better error handling
            options = self.page.locator('div[role="option"]').all()
            if not options:
                available_text = self.page.locator('div[role="listbox"]').text_content()
                raise ValueError(f"No expense type options found in dropdown. Available text: {available_text}")
            
            # Log all available options for debugging
            option_texts = [el.text_content().strip() for el in options]
            print(f"Available expense types: {option_texts}")
            
            # If no specific name provided, select the first option
            if expense_type_name is None:
                option = options[0]
                expense_type_name = option.text_content().strip()
                print(f"Selecting first available expense type: {expense_type_name}")
            else:
                # Try to find the specific option (case insensitive)
                option = self.page.locator(f'div[role="option"]').filter(has_text=expense_type_name).first
                if not option.is_visible():
                    print(f"Expense type '{expense_type_name}' not found. Available options: {option_texts}")
                    # Fall back to first option if specific one not found
                    option = options[0]
                    expense_type_name = option.text_content().strip()
                    print(f"Falling back to first available expense type: {expense_type_name}")
            
            # Click the option with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Attempt {attempt + 1} to select expense type: {expense_type_name}")
                    option.scroll_into_view_if_needed()
                    option.click(force=True)
                    # Verify selection was successful
                    self.page.wait_for_selector('div[role="listbox"]', state='hidden', timeout=5000)
                    print(f"Successfully selected expense type: {expense_type_name}")
                    break
                except Exception as click_error:
                    if attempt == max_retries - 1:  # Last attempt
                        print(f"Failed to select expense type after {max_retries} attempts: {str(click_error)}")
                        raise
                    print(f"Retrying selection (attempt {attempt + 1}): {str(click_error)}")
                    self.page.wait_for_timeout(1000)  # Wait before retry
            
            # Small delay to ensure the selection is processed
            self.page.wait_for_timeout(500)
            
            return expense_type_name.strip()
            
        except Exception as e:
            # Take a screenshot for debugging
            screenshot_path = f"expense_type_selection_error_{int(time.time())}.png"
            self.page.screenshot(path=screenshot_path)
            print(f"Screenshot saved as: {screenshot_path}")
            
            # Log detailed error information
            print(f"Error selecting expense type: {str(e)}")
            print(f"Available options: {[el.text_content().strip() for el in self.page.locator('div[role="option"]').all()]}")
            print(f"Page URL: {self.page.url}")
            print(f"Page title: {self.page.title()}")
            
            raise
            
    # ===== Multiple File Upload Methods =====
    
    def get_uploaded_files_count(self) -> int:
        """
        Get the count of currently uploaded files.
        
        Returns:
            int: Number of files currently uploaded
        """
        return self.overlay['file_upload']['selected_files'].count()
    
    def get_uploaded_file_names(self) -> list[str]:
        """
        Get the list of uploaded file names from the UI.
        
        Returns:
            list[str]: List of uploaded file names
        """
        return [el.text_content().strip() 
               for el in self.page.locator('div.text-sm.font-medium.text-blue-700').all()]
        
    def get_delete_button_by_filename(self, filename: str):
        """
        Get the delete button locator for a specific file name.
        
        Args:
            filename (str): The name of the file to find the delete button for
            
        Returns:
            Locator: The delete button locator for the specified file
        """
        return self.page.locator(f'//div[text()="{filename}"]/../../../button')
    
    def remove_uploaded_file(self, filename: str):
        """
        Remove an uploaded file by its filename.
        
        Args:
            filename (str): Name of the file to remove
        """
        try:
            # Get the delete button for the specified file
            delete_btn = self.get_delete_button_by_filename(filename)
            
            # Verify the delete button is visible and click it
            expect(delete_btn).to_be_visible(timeout=10000)
            delete_btn.click()
            
            # Wait for the file to be removed from the UI
            self.page.wait_for_timeout(1000)  # Small delay for UI update
            
            # Verify the file is no longer in the list
            uploaded_files = self.get_uploaded_file_names()
            if filename in uploaded_files:
                raise Exception(f"File {filename} was not removed after clicking delete button")
                
        except Exception as e:
            print(f"Error removing file {filename}: {str(e)}")
            # Take a screenshot for debugging
            self.page.screenshot(path=f"remove_file_error_{filename}.png")
            raise

    def get_uploaded_file_sizes(self) -> list:
        """
        Get the sizes of all currently uploaded files.
        
        {{ ... }}
            list: List of uploaded file sizes as strings
        """
        return [size.text_content().strip() for size in self.overlay['file_upload']['file_size'].all()]
    
    def is_file_uploaded(self, filename: str) -> bool:
        """
        Check if a file with the given name is uploaded.
        
        Args:
            filename: Name of the file to check
            
        Returns:
            bool: True if file is found in the upload list, False otherwise
        """
        return filename in self.get_uploaded_file_names()
        
    def get_file_type_error_message(self, filename: str):
        """
        Get the error message element for invalid file type upload.
        
        Args:
            filename: Name of the file that caused the error
            
        Returns:
            Locator: The error message element
        """
        return self.page.locator(f'div.bg-red-50:has-text("{filename}: File type not supported. Please use PDF, JPEG, or PNG.")')
    
    def upload_multiple_files(self, *file_paths: str, wait_for_complete: bool = True) -> bool:
        """
        Upload multiple files to the invoice form.
        
        Args:
            *file_paths: One or more file paths to upload
            wait_for_complete: Whether to wait for all uploads to complete
            
        Returns:
            bool: True if all files were uploaded successfully, False otherwise
        """
        if not file_paths:
            return False
            
        try:
            # Store the current count of uploaded files
            initial_count = self.get_uploaded_files_count()
            
            # Upload each file
            for file_path in file_paths:
                self.upload_invoice_file(file_path, wait_for_complete=wait_for_complete)
                
            # Verify all files were added
            expected_count = initial_count + len(file_paths)
            actual_count = self.get_uploaded_files_count()
            
            if actual_count != expected_count:
                print(f"Warning: Expected {expected_count} files, but found {actual_count} files after upload")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error uploading multiple files: {str(e)}")
            return False
    
    def is_error_message_visible(self, expected_text: str = None) -> bool:
        """
        Check if an error message is visible, optionally with specific text.
        
        Args:
            expected_text: (Optional) Specific text to look for in the error message
            
        Returns:
            bool: True if matching error message is visible, False otherwise
        """
        try:
            if expected_text:
                error_element = self.overlay['error_message'].filter(has_text=expected_text)
            else:
                error_element = self.overlay['error_message'].first
                
            return error_element.is_visible()
        except:
            return False
    
    def get_total_upload_size_mb(self) -> float:
        """
        Calculate the total size of all uploaded files in MB.
        
        Returns:
            float: Total size in MB, or 0 if no files or error
        """
        try:
            total_size = 0.0
            for size_text in self.get_uploaded_file_sizes():
                # Extract numeric value and unit (e.g., "2.5 MB" -> 2.5)
                if 'MB' in size_text:
                    value = float(size_text.replace('MB', '').strip())
                    total_size += value
                elif 'KB' in size_text:
                    # Convert KB to MB
                    value = float(size_text.replace('KB', '').strip()) / 1024
                    total_size += value
                elif 'B' in size_text and 'KB' not in size_text and 'MB' not in size_text:
                    # Convert bytes to MB
                    value = float(size_text.replace('B', '').strip()) / (1024 * 1024)
                    total_size += value
                    
            return round(total_size, 2)
        except Exception as e:
            print(f"Error calculating total upload size: {str(e)}")
            return 0.0
