import pytest
import os
import time
import random
import string
import shutil
from pathlib import Path
from playwright.sync_api import Page, expect
from tests.Invoices.page_object import invoices_page
from tests.Invoices.page_object.invoices_page import InvoicesPage
from pages.expense_types.expense_types_page import ExpenseTypesPage
from tests.config.test_config import URLS

# Get the absolute path to the sample documents
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SAMPLE_DOC_DIR = os.path.join(BASE_DIR, "sample_doc")
SAMPLE_DOC_ORIGINAL = os.path.join(SAMPLE_DOC_DIR, "InvoiceExample_1_SmallSize.pdf")
LARGE_FILE_2MB = os.path.join(SAMPLE_DOC_DIR, "LargeFile2MB.jpg")
LARGE_FILE_15MB = os.path.join(SAMPLE_DOC_DIR, "LargeFile15MB.jpg")

# Verify the sample documents exist
for file_path in [SAMPLE_DOC_ORIGINAL, LARGE_FILE_2MB, LARGE_FILE_15MB]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required file not found at: {file_path}")

# Generate a unique sample document path for this test run
timestamp = int(time.time())
# Keep the same file extension as the original
file_ext = os.path.splitext(SAMPLE_DOC_ORIGINAL)[1]
SAMPLE_DOC_PATH = os.path.join(SAMPLE_DOC_DIR, f"invoice_sample_{timestamp}{file_ext}")

# Path to the large test file
LARGE_TEST_FILE = os.path.join(SAMPLE_DOC_DIR, "Large-Sample-Image-download-for-Testing.jpg")

# Create a copy of the original file with the new unique name
shutil.copy2(SAMPLE_DOC_ORIGINAL, SAMPLE_DOC_PATH)

@pytest.mark.invoices
class TestCreateNewInvoice:
    """Test cases for creating a new invoice."""

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        # Setup
        self.page = logged_in_page
        self.invoices_page = InvoicesPage(logged_in_page)
        self.expense_types_page = ExpenseTypesPage(logged_in_page)
        
        # Navigate to the invoices page
        self.page.goto(URLS["INVOICES"])
        
        # Wait for the page to load completely
        self.page.wait_for_load_state("domcontentloaded")
        
        # Verify we're on the invoices page
        expect(self.page).to_have_title("Invoice AI")
        
        # Store the current number of invoices (for later verification)
        self.initial_invoice_count = self.invoices_page.get_total_invoices()
        
        # This is where the test will run
        yield
        
        # Teardown
        try:
            # Close any open modals
            if self.invoices_page.is_overlay_visible():
                self.invoices_page.close_new_invoice_overlay()
        finally:
            # Clean up the temporary file after test
            if os.path.exists(SAMPLE_DOC_PATH):
                os.remove(SAMPLE_DOC_PATH)
    
    def create_test_expense_type(self):
        """Create a test expense type and return its name."""
        # Generate a unique name for the test expense type
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        expense_type_name = f"TestExpense_{random_suffix}"
        
        # Navigate to expense types page
        self.expense_types_page.navigate()
        
        # Click on New Expense Type button
        self.expense_types_page.click_new_expense_type()
        
        # Fill in the form
        self.expense_types_page.fill_expense_type_form(expense_type_name)
        
        # Submit the form
        self.expense_types_page.submit_form()
        
        # Navigate back to invoices page
        self.invoices_page.navigate()
        
        return expense_type_name

    def test_create_new_invoice_with_required_fields(self):
        """Test creating a new invoice with all required fields filled."""
        # Create a test expense type first
        test_expense_type = self.create_test_expense_type()
        
        # Test data
        invoice_type = "debit"  # 'debit' or 'credit'
        
        # Step 1: Click the New Invoice button
        self.invoices_page.open_new_invoice_overlay()
        
        # Verify the overlay is visible
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # Step 2: Fill in the required fields
        # Select the first available cost center
        selected_cost_center = self.invoices_page.select_cost_center()
        
        # Select the test expense type we just created
        self.invoices_page.select_expense_type(test_expense_type)
        self.invoices_page.select_invoice_type(invoice_type)
        
        # Step 5: Upload the sample document
        self.invoices_page.upload_invoice_file(SAMPLE_DOC_PATH)
        
        # Verify the file was uploaded (check if the file name is displayed)
        # This might need adjustment based on actual UI behavior
        # file_name = os.path.basename(SAMPLE_DOC_PATH)
        # expect(self.invoices_page.overlay['file_upload']['drop_zone']).to_contain_text(file_name)
        
        # Get the filename we're using for this test
        expected_filename = os.path.basename(SAMPLE_DOC_PATH)
        print(f"Looking for uploaded file: {expected_filename}")
        
        # Step 6: Click the Add Invoice button
        self.invoices_page.click_add_invoice()
        
        # Check that the modal is closed after submission
        try:
            # Wait for the modal to be hidden (should happen quickly if submission is successful)
            self.page.wait_for_selector('div[data-slot="card"]', state='hidden', timeout=10000)
            print("✅ Invoice submission modal closed successfully")
        except Exception as e:
            # If modal is still visible, take a screenshot and check for validation errors
            screenshot_path = os.path.join(os.getcwd(), "test_results", f"invoice_submission_failed_{int(time.time())}.png")
            self.page.screenshot(path=screenshot_path, full_page=True)
            
            # Check for any visible error messages in the modal
            error_message = ""
            try:
                error_element = self.page.locator('div[role="alert"], .text-red-500, .text-destructive')
                if error_element.count() > 0:
                    error_message = "\n  - " + "\n  - ".join([error.text_content().strip() for error in error_element.all() if error.text_content().strip()])
            except:
                pass
                
            error_msg = f"❌ Invoice submission failed - modal did not close.{error_message}"
            print(error_msg)
            print(f"  Screenshot saved to: {screenshot_path}")

        # Wait for the invoice to appear in the table with retry logic
        max_wait_time = 300  # 5 minutes
        check_interval = 10  # seconds
        start_time = time.time()
        invoice_found = False
        last_status_update = 0
        
        print(f"Waiting for invoice '{expected_filename}' to appear in the table (max {max_wait_time} seconds)...")
        
        while time.time() - start_time < max_wait_time and not invoice_found:
            current_time = time.time()
            elapsed = int(current_time - start_time)
            remaining = max(0, max_wait_time - elapsed)
            
            # Show status update every 30 seconds
            if current_time - last_status_update >= 30:
                print(f"  - Still waiting... {elapsed} seconds elapsed, {remaining} seconds remaining")
                last_status_update = current_time
            
            try:
                # Refresh the page to get the latest data
                self.page.reload()
                self.page.wait_for_load_state("networkidle")
                
                # Check if the invoice exists in the table
                invoice_row = self.page.locator(f'tr:has-text("{expected_filename}")')
                if invoice_row.is_visible():
                    print(f"✅ Found invoice '{expected_filename}' in the table after {elapsed} seconds!")
                    invoice_found = True
                    break
                    
            except Exception as e:
                print(f"⚠️ Error checking for invoice: {str(e)}")
            
            # Wait for the check interval or remaining time, whichever is smaller
            time.sleep(min(check_interval, max_wait_time - elapsed))
        
        # Final verification with clear messaging
        if not invoice_found:
            print(f"\n❌ Invoice processing timed out after {max_wait_time} seconds")
            print("Possible reasons:")
            print("1. The backend is still processing the invoice")
            print("2. There was an error processing the invoice")
            print("3. The invoice was not created successfully")
            print("\nNext steps:")
            print(f"- Check the backend logs for invoice: {expected_filename}")
            print("- Verify the file processing queue status")
            print("- Check for any error messages in the application logs")
            
            # Take a screenshot for debugging
            screenshot_path = f"invoice_not_found_{int(time.time())}.png"
            self.page.screenshot(path=screenshot_path)
            print(f"\n📸 Screenshot saved to: {screenshot_path}")
            
            # Check if the form submission was successful
            try:
                success_message = self.page.locator("text=success")
                if success_message.is_visible():
                    print("✅ Form was submitted successfully - invoice is still processing")
                else:
                    error_message = self.page.locator("text=error,text=failed")
                    if error_message.is_visible():
                        print(f"❌ Error message found: {error_message.inner_text()}")
            except Exception as e:
                print(f"ℹ️ Could not determine form submission status: {str(e)}")
            
            # Final assertion with clear error message
            assert False, f"Invoice '{expected_filename}' did not appear in the table after {max_wait_time} seconds. Form was submitted but invoice is still processing or failed."
        
        # Verify the overlay is closed
        assert not self.invoices_page.is_overlay_visible(), "New Invoice overlay is still visible after submission"
        
        # Wait for any loading to complete
        self.invoices_page.wait_for_loading_animation_to_disappear()
        

    def test_cancel_new_invoice(self):
        """Test that clicking the Cancel button closes the New Invoice modal."""
        # Step 1: Open the New Invoice modal
        self.invoices_page.open_new_invoice_overlay()
        
        # Verify the overlay is visible
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # Step 2: Click the Cancel button
        self.invoices_page.cancel_new_invoice()
        
        # Verify the overlay is no longer visible
        assert not self.invoices_page.is_overlay_visible(), \
            "New Invoice overlay should be closed after clicking Cancel"
        
    def test_close_new_invoice_modal(self):
        """Test that clicking the Close (X) button closes the New Invoice modal."""
        # Step 1: Open the New Invoice modal
        self.invoices_page.open_new_invoice_overlay()
        
        # Verify the overlay is visible
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # Step 2: Click the Close (X) button
        self.invoices_page.close_new_invoice_overlay()
        
        # Verify the overlay is no longer visible
        assert not self.invoices_page.is_overlay_visible(), \
            "New Invoice overlay should be closed after clicking Close"
    
    def test_upload_file_exceeding_size_limit(self):
        """Test that uploading a file larger than 10MB shows an error message and keeps the modal open."""
        # Skip if the large test file doesn't exist
        if not os.path.exists(LARGE_TEST_FILE):
            pytest.skip(f"Large test file not found at: {LARGE_TEST_FILE}")
            
        # Get the file size in MB for the assertion message
        file_size_mb = os.path.getsize(LARGE_TEST_FILE) / (1024 * 1024)
        print(f"\nTesting with file: {os.path.basename(LARGE_TEST_FILE)}")
        print(f"File size: {file_size_mb:.2f} MB")
        

        # Create a test expense type first
        test_expense_type = self.create_test_expense_type()
        
        # Test data
        invoice_type = "debit"  # 'debit' or 'credit'
        
        # Step 1: Click the New Invoice button
        self.invoices_page.open_new_invoice_overlay()
        
        # Verify the overlay is visible
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # Step 2: Fill in the required fields
        # Select the first available cost center
        selected_cost_center = self.invoices_page.select_cost_center()
        
        # Select the test expense type we just created
        self.invoices_page.select_expense_type(test_expense_type)
        self.invoices_page.select_invoice_type(invoice_type)
        
        # Step 5: Upload the sample document
        self.invoices_page.upload_invoice_file(LARGE_TEST_FILE)
           
        # Step 6: Submit the form
        self.invoices_page.click_add_invoice()
        self.page.pause()
                
        # Check that the modal is still open
        try:
            self.page.wait_for_selector('div[data-slot="card"]', state='visible', timeout=5000)
            print("✅ Modal remains open after file size validation error")
        except Exception as e:
            screenshot_path = os.path.join(os.getcwd(), "test_results", "large_file_modal_closed_error.png")
            self.page.screenshot(path=screenshot_path, full_page=True)
            raise AssertionError(f"Modal should remain open after file size validation error. Screenshot saved to: {screenshot_path}")
        
        # Check for the error message
        error_selector = 'div.bg-red-50.border-red-200.text-red-800:has-text("File size must be less than 10MB")'
        try:
            error_message = self.page.wait_for_selector(
                error_selector,
                state='visible',
                timeout=5000
            )
            error_text = error_message.text_content().strip()
            print(f"✅ Found error message: {error_text}")
            
            # Verify the error message contains the expected text
            assert "File size must be less than 10MB" in error_text, \
                f"Error message does not contain expected text. Found: {error_text}"
                
        except Exception as e:
            screenshot_path = os.path.join(os.getcwd(), "test_results", "large_file_error_message_missing.png")
            self.page.screenshot(path=screenshot_path, full_page=True)
            raise AssertionError(
                f"Expected error message not found. Error: {str(e)}. Screenshot saved to: {screenshot_path}"
            )
            
        # Try to find and click the Dismiss button if it exists
        dismiss_button = self.page.locator('button:has-text("Dismiss")')
        if dismiss_button.is_visible():
            try:
                dismiss_button.click()
                # Wait for the error message to be hidden after clicking dismiss
                self.page.wait_for_selector(error_selector, state='hidden', timeout=3000)
                print("✅ Dismiss button works as expected")
            except Exception as e:
                print(f"⚠️ Error with dismiss button: {str(e)}")
        else:
            print("ℹ️ Dismiss button not found or not visible")
