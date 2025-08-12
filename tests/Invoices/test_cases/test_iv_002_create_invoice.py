import pytest
import os
import time
from pathlib import Path
from playwright.sync_api import Page, expect
from tests.Invoices.page_object import invoices_page
from tests.Invoices.page_object.invoices_page import InvoicesPage

# Get the absolute path to the sample documents
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SAMPLE_DOC_PATH = os.path.join(BASE_DIR, "sample_doc", "57a3.jpg")
LARGE_FILE_2MB = os.path.join(BASE_DIR, "sample_doc", "LargeFile2MB.jpg")
LARGE_FILE_15MB = os.path.join(BASE_DIR, "sample_doc", "LargeFile15MB.jpg")

# Verify the sample documents exist
for file_path in [SAMPLE_DOC_PATH, LARGE_FILE_2MB, LARGE_FILE_15MB]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required file not found at: {file_path}")

@pytest.mark.invoices
class TestCreateNewInvoice:
    """Test cases for creating a new invoice."""

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        self.page = logged_in_page
        self.invoices_page = InvoicesPage(logged_in_page)
        
        # Navigate to the invoices page
        self.invoices_page.navigate()
        
        # Wait for the page to load completely
        self.page.wait_for_load_state("domcontentloaded")
        
        # Verify we're on the invoices page
        expect(self.page).to_have_title("Invoice AI")
        
        # Store the current number of invoices (for later verification)
        self.initial_invoice_count = self.invoices_page.get_total_invoices()
        
        yield
        
        # Teardown: Close any open modals
        if self.invoices_page.is_overlay_visible():
            self.invoices_page.close_new_invoice_overlay()

    def test_create_new_invoice_with_required_fields(self):
        """Test creating a new invoice with all required fields filled."""
        # Test data
        invoice_type = "debit"  # 'debit' or 'credit'
        
        # Step 1: Click the New Invoice button
        self.invoices_page.open_new_invoice_overlay()
        
        # Verify the overlay is visible
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # Step 2: Fill in the required fields
        # Using first available options for dropdowns
        selected_cost_center = self.invoices_page.select_cost_center()
        selected_expense_type = self.invoices_page.select_expense_type()
        self.invoices_page.select_invoice_type(invoice_type)
        
        # Step 5: Upload the sample document
        self.invoices_page.upload_invoice_file(SAMPLE_DOC_PATH)
        
        # Verify the file was uploaded (check if the file name is displayed)
        # This might need adjustment based on actual UI behavior
        # file_name = os.path.basename(SAMPLE_DOC_PATH)
        # expect(self.invoices_page.overlay['file_upload']['drop_zone']).to_contain_text(file_name)
        
        # Step 6: Click the Add Invoice button
        self.invoices_page.click_add_invoice()
        
        # Wait for the overlay to close
        self.page.wait_for_selector('div[data-slot="card"]', state='hidden', timeout=10000)
        
        # Verify the overlay is closed
        assert not self.invoices_page.is_overlay_visible(), "New Invoice overlay is still visible after submission"
        
        # Wait for any loading to complete
        self.invoices_page.wait_for_loading_animation_to_disappear()
        
        # TODO: Uncomment and update this section when the feature is complete
        # Verify the new invoice appears in the table
        # new_invoice_count = self.invoices_page.get_total_invoices()
        # assert new_invoice_count == self.initial_invoice_count + 1, "Invoice count should increase by 1"
        # print(f"Created invoice with Cost Center: {selected_cost_center}, Expense Type: {selected_expense_type}")
        # assert int(new_invoice_count) == int(self.initial_invoice_count) + 1, \
        #     f"Expected invoice count to increase by 1, but got {new_invoice_count} (was {self.initial_invoice_count})"
            
        # Verify the new invoice is in the table
        # Note: This will need to be updated based on the actual table structure and data
        # and how the new invoice is identified in the table
        # For example, if the file name is displayed in the table:
        # file_name = os.path.basename(SAMPLE_DOC_PATH)
        # expect(self.invoices_page.table.get_row_by_text(file_name)).to_be_visible()
        
        """
        # For now, just print a message that the test completed without errors
        print("Test completed. Note: Invoice table verification is commented out as the feature is not yet complete.")
        """

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
    
    def test_upload_large_file_2mb(self):
        """Test uploading a 2MB file to the invoice form and verify timeout error."""
        # Test data
        invoice_type = "debit"
        max_wait_seconds = 300  # 5 minutes max for the entire test
        
        try:
            # Step 1: Open the New Invoice modal
            self.invoices_page.open_new_invoice_overlay()
            
            # Verify the overlay is visible
            assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
            
            # Step 2: Fill in the required fields
            selected_cost_center = self.invoices_page.select_cost_center()
            selected_expense_type = self.invoices_page.select_expense_type()
            self.invoices_page.select_invoice_type(invoice_type)
            
            # Step 3: Upload the 2MB file
            self.invoices_page.upload_invoice_file(LARGE_FILE_2MB)
            
            # Take a screenshot before submission
            self.page.screenshot(path="test-results/before_submit_2mb.png")
            
            # Step 4: Submit the form
            self.invoices_page.click_add_invoice()
            
            # Step 5: Wait for 'Uploading...' button to appear
            if self.invoices_page.wait_for_upload_button_state("Uploading..."):
                print("Found 'Uploading...' button")
                # Take a screenshot when Uploading... is visible
                self.page.screenshot(path="test-results/uploading_2mb.png")
            else:
                print("Warning: Did not see 'Uploading...' button")
            
            # Step 6: Wait for button to revert to 'Add Invoice' or error to appear
            # Give it up to 2 minutes to complete
            start_time = time.time()
            while time.time() - start_time < 120:  # 2 minutes
                # Check for error message first
                if self.invoices_page.is_upload_timeout_error_visible():
                    print("Found upload timeout error message")
                    break
                # Check if button reverted to 'Add Invoice'
                if self.invoices_page.wait_for_upload_button_state("Add Invoice", 5000):
                    print("Button reverted to 'Add Invoice'")
                    break
                time.sleep(2)  # Check every 2 seconds
            else:
                # Take a screenshot if we timed out
                self.page.screenshot(path="test-results/upload_timeout_2mb.png")
                raise TimeoutError("Timed out waiting for upload to complete or error to appear")
            
            # Step 7: Verify the error message is shown
            assert self.invoices_page.is_upload_timeout_error_visible(), \
                "Expected upload timeout error message not found"
            
            # Take a screenshot for verification
            self.page.screenshot(path="test-results/2mb_upload_timeout.png")
            
            # Close the modal
            self.invoices_page.close_new_invoice_overlay()
            
        except Exception as e:
            # Take a screenshot on error
            self.page.screenshot(path="test-results/2mb_upload_error.png")
            print(f"Test failed with error: {str(e)}")
            # Re-raise the exception to fail the test
            raise
        
    @pytest.mark.skip(reason="15MB file upload test is skipped as it takes too long to run")
    def test_upload_large_file_15mb(self):
        """Test uploading a 15MB file to the invoice form and verify timeout error.
        
        This test is skipped by default as it takes too long to run.
        To run it, remove the @pytest.mark.skip decorator.
        """
        pass  # Test is skipped
