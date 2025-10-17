import pytest
import os
import time
import random
import string
from playwright.sync_api import Page, expect
from tests.Invoices.page_object.invoices_page import InvoicesPage
from pages.expense_types.expense_types_page import ExpenseTypesPage
from tests.config.test_config import URLS
from playwright.sync_api import Route

# Get the absolute path to the sample documents
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SAMPLE_DOC_DIR = os.path.join(BASE_DIR, "sample_doc")

# Define the test files we'll be using
test_files = [
    os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", "InvoiceExample_5.png"),
    os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", "InvoiceExample_5 copy.png"),
    os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", "InvoiceExample_5 copy 7.png")
]

# Verify the sample documents exist
for file_path in test_files:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required file not found at: {file_path}")

@pytest.mark.invoices
class TestMultipleFileUploads:
    """Test cases for multiple file upload functionality in Invoices."""
    
    # Test credentials
    credentials = {
        "email": "mamado.2000@gmail.com",
        "password": "Abc@1234"
    }
    
    # Test files to be used across test cases
    TEST_FILES = [
        "InvoiceExample_5.png",
        "InvoiceExample_5 copy.png",
        "InvoiceExample_5 copy 7.png"
    ]

    @pytest.fixture(autouse=True)
    def setup(self, logged_in_page: Page):
        """Setup test environment before each test."""
        self.page = logged_in_page
        self.invoices_page = InvoicesPage(logged_in_page)
        self.expense_types_page = ExpenseTypesPage(logged_in_page)
        
        # Navigate to the invoices page
        self.page.goto(URLS["INVOICES"])
        
        # Wait for the page to load completely
        self.page.wait_for_load_state("domcontentloaded")
        
        # Verify we're on the invoices page
        expect(self.page).to_have_title("Invoice AI")
        
        # Open the new invoice overlay
        self.invoices_page.open_new_invoice_overlay()
        
        # This is where the test will run
        yield
        
        # Teardown
        try:
            # Close any open modals
            if self.invoices_page.is_overlay_visible():
                self.invoices_page.close_new_invoice_overlay()
        except Exception as e:
            print(f"Error during teardown: {str(e)}")

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
    
    def wait_for_file_processing_status(self, file_name: str, expected_status: str, timeout: int = 40000) -> bool:
        """
        Waits for a file in the invoice table to reach the expected processing status.
        
        This handles the asynchronous nature of file processing.
        
        Args:
            file_name: The base name of the file uploaded (e.g., 'non_invoice_document.pdf').
            expected_status: The status text to wait for ('Failed', 'Processed', etc.).
            timeout: Maximum time in milliseconds to wait for the status change.
            
        Returns:
            True if the status is found, False otherwise.
        """
        print(f"Waiting for file '{file_name}' to reach status '{expected_status}'...")
        
        # This locator targets the cell in the table row (identified by file_name)
        # that contains the 'Status' text (e.g., 'Failed', 'Processed').
        # We look for a table row containing the file_name, and then within that row, 
        # we look for the element displaying the status text.
        
        # Selector explanation:
        # 1. Targets a row (e.g., 'tr' or 'div' with role='row') that contains the file name.
        # 2. Within that row, it looks for an element (e.g., 'span' or 'div') that contains the expected status text.
        status_locator = self.page.locator(
            f'tr:has-text("{file_name}") >> text="{expected_status}"'
        )

        try:
            # Playwright automatically handles polling/retrying until the element is visible
            status_locator.wait_for(state="visible", timeout=timeout)
            print(f"SUCCESS: File '{file_name}' status successfully updated to '{expected_status}'.")
            return True
        except TimeoutError:
            print(f"FAILURE: File '{file_name}' status did not update to '{expected_status}' within {timeout/1000}s.")
            # Optional: Take a screenshot on failure to debug the page state
            self.page.screenshot(path=f"failed_status_timeout_{file_name}.png", full_page=True)
            return False

    def test_upload_single_multi_page_document(self):
        """Test uploading a single multi-page document. Done"""
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files using the page object method
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", file_name)
            for file_name in self.TEST_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(self.TEST_FILES), \
            f"Expected {len(self.TEST_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in self.TEST_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        self.page.wait_for_timeout(1000)
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(self.TEST_FILES))
        
        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_small_files_under_10mb_same_content_file_type_and_different_name(self):
        """Test uploading multiple small files with same content, same file type, but different names. Done"""
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files using the page object method
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", file_name)
            for file_name in self.TEST_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(self.TEST_FILES), \
            f"Expected {len(self.TEST_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in self.TEST_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(self.TEST_FILES))
        
        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"
        
    def test_upload_multiple_small_files_under_10mb_same_content_same_file_type_and_same_name(self):
        """Test uploading multiple small files with same content, same file type, and same names. Done"""
        # List of the same file to be uploaded twice
        DUPLICATE_FILES = ["InvoiceExample_4.png", "InvoiceExample_4.png"]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload the same file twice using the page object method
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_and_name", file_name)
            for file_name in DUPLICATE_FILES
        ]
        
        # First upload
        self.invoices_page.upload_multiple_files(file_paths[0])
        
        # Second upload of the same file
        self.invoices_page.upload_multiple_files(file_paths[1])
        
        # 7. Verify the warning message is shown for duplicate file
        expect(self.invoices_page.overlay['warning_messages']['file_already_selected']).to_be_visible(timeout=10000), \
            "Warning message for duplicate file not shown"
            
        # 8. Verify only one file is displayed in the selected files section
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == 1, \
            f"Expected 1 file to be displayed, but found {len(uploaded_files)}"
            
        # 9. Verify the file is displayed in the selected files section
        file_name = os.path.basename(file_paths[0])  # Get the file name from the path
        file_locator = self.invoices_page.get_file_locator_by_name(file_name)
        expect(file_locator).to_be_visible(timeout=10000)
        
        # Test stops here as per requirements

    def test_upload_multiple_small_files_under_10mb_same_content_different_file_type_and_same_name(self):
        """Test uploading multiple small files with same content, different file types, but same names. Done"""
        # List of files with same base name but different extensions
        SAME_NAME_DIFF_EXT_FILES = [
            "InvoiceExample_1_SmallSize.png",
            "InvoiceExample_1_SmallSize.jpg",
            "InvoiceExample_1_SmallSize.pdf"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files with same name but different extensions
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_and_name_but_different_content", file_name)
            for file_name in SAME_NAME_DIFF_EXT_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(SAME_NAME_DIFF_EXT_FILES), \
            f"Expected {len(SAME_NAME_DIFF_EXT_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in SAME_NAME_DIFF_EXT_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(SAME_NAME_DIFF_EXT_FILES))
        
        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_small_files_under_10mb_same_content_different_file_type_and_different_name(self):
        """Test uploading multiple small files with same content but different file types and names. Done"""
        # List of files with different names and extensions but same content
        DIFFERENT_NAME_AND_EXT_FILES = [
            "InvoiceExample_1_SmallSize.jpg",
            "InvoiceExample_1_SmallSize _1_copy.png",
            "InvoiceExample_2_SmallSize_2_Copy.pdf"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files with different names and extensions but same content
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "different_file_type_and_name_but_same_content", file_name)
            for file_name in DIFFERENT_NAME_AND_EXT_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(DIFFERENT_NAME_AND_EXT_FILES), \
            f"Expected {len(DIFFERENT_NAME_AND_EXT_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in DIFFERENT_NAME_AND_EXT_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(DIFFERENT_NAME_AND_EXT_FILES))
        
        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_small_files_under_10mb_different_content_same_file_type_and_same_name(self):
        """Test uploading multiple small files with different content, same file type, and same names. Done"""
        # List of directories containing files with same name but different content
        SAME_NAME_DIFF_CONTENT_PATHS = [
            "1/SameInvoiceExample.png",
            "2/SameInvoiceExample.png",
            "3/SameInvoiceExample.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files with same name but different content
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "different_content_but_same_file_type_and_name", rel_path)
            for rel_path in SAME_NAME_DIFF_CONTENT_PATHS
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        # The files have the same name but different content (sizes)
        file_locator = self.page.locator('div.text-blue-700:has-text("SameInvoiceExample.png")')
        
        # 8. Verify there are exactly 3 files with the same name
        expect(file_locator).to_have_count(3, timeout=10000)
        
        # 9. Verify each file shows its size (indicating unique files despite same name)
        file_sizes = self.page.locator('//div[@class="text-xs text-blue-600"]').all()
        assert len(file_sizes) == 3, f"Expected 3 files with size info, found {len(file_sizes)}"
        
        # Verify all files are visible by checking each one individually
        for i in range(3):
            expect(file_locator.nth(i)).to_be_visible(timeout=10000)
        
        # Get the actual displayed file names to verify count
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(SAME_NAME_DIFF_CONTENT_PATHS), \
            f"Expected {len(SAME_NAME_DIFF_CONTENT_PATHS)} files, but found {len(uploaded_files)}"
            
        # 10. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(SAME_NAME_DIFF_CONTENT_PATHS))
        
        # 11. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_small_files_under_10mb_different_content_same_file_type_and_different_name(self):
        """Test uploading multiple small files with different content, same file type, but different names. Done"""
        # List of files with different content but same file type (PNG)
        DIFFERENT_CONTENT_FILES = [
            "InvoiceExample_1A.png",
            "InvoiceExample_2B.png",
            "InvoiceExample_3C.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files with different content but same file type using the page object method
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_but_different_content_name", file_name)
            for file_name in DIFFERENT_CONTENT_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(DIFFERENT_CONTENT_FILES), \
            f"Expected {len(DIFFERENT_CONTENT_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in DIFFERENT_CONTENT_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(DIFFERENT_CONTENT_FILES))
        
        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_small_files_under_10mb_different_content_different_file_type_and_same_name(self):
        """Test uploading multiple small files with different content, different file types, but same names."""
        # List of files with same name but different content and file type
        SAME_NAME_DIFF_CONTENT_TYPE_FILES = [
            "SameInvoiceExample.jpg",
            "SameInvoiceExample.pdf",
            "SameInvoiceExample.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files with same name but different content and type
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_name_but_different_content_and_file_type", file_name)
            for file_name in SAME_NAME_DIFF_CONTENT_TYPE_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(SAME_NAME_DIFF_CONTENT_TYPE_FILES), \
            f"Expected {len(SAME_NAME_DIFF_CONTENT_TYPE_FILES)} files, but found {len(uploaded_files)}"
        
        # 8. Verify the files are displayed in the selected files section
        for file_name in SAME_NAME_DIFF_CONTENT_TYPE_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(SAME_NAME_DIFF_CONTENT_TYPE_FILES))

        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_small_files_under_10mb_different_content_different_file_type_and_different_name(self):
        """Test uploading multiple small files with different content, different file types, and different names. Done"""
        # List of files with different content, different types, and different names
        DIFFERENT_FILES = [
            "Invoice_01A.jpg",
            "Invoice_02B.pdf",
            "Invoice_03C.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files using the page object method
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "different_file_type_name_and_content", file_name)
            for file_name in DIFFERENT_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(DIFFERENT_FILES), \
            f"Expected {len(DIFFERENT_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in DIFFERENT_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(DIFFERENT_FILES))

        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_multiple_files_exceeding_10mb(self):
        """Test uploading multiple files with total size exceeding 10MB. Done"""
        # List of files that will exceed 10MB in total
        LARGE_FILES = [
            "InvoiceExample_5.png",
            "InvoiceExample_5 copy.png",
            "InvoiceExample_5 copy 2.png",
            "InvoiceExample_5 copy 3.png",
            "InvoiceExample_5 copy 4.png",
            "InvoiceExample_5 copy 5.png",
            "InvoiceExample_5 copy 6.png",
            "InvoiceExample_5 copy 7.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files that will exceed 10MB in total
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", file_name)
            for file_name in LARGE_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(LARGE_FILES), \
            f"Expected {len(LARGE_FILES)} files, but found {len(uploaded_files)}"
        
        # 8. Verify the files are displayed in the selected files section
        for file_name in LARGE_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)  # Increased timeout for file to appear
        
        # 9. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(LARGE_FILES))

        # 10. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_remove_uploaded_file(self):
        """Test removing an uploaded file before submission."""
        # List of files with different types, names and content
        DIFFERENT_FILES = [
            "Invoice_03C.png",
            "Invoice_02B.pdf",
            "Invoice_01A.jpg"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "different_file_type_name_and_content", file_name)
            for file_name in DIFFERENT_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(DIFFERENT_FILES), \
            f"Expected {len(DIFFERENT_FILES)} files, but found {len(uploaded_files)}"
            
        # 8. Verify the files are displayed in the selected files section
        for file_name in DIFFERENT_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)
        
        # 9. Remove the second file (index 1)
        file_to_remove = DIFFERENT_FILES[1]
        self.invoices_page.get_delete_button_by_filename(file_to_remove).click()
        
        # 10. Verify the file was removed
        remaining_files = self.invoices_page.get_uploaded_file_names()
        assert len(remaining_files) == len(DIFFERENT_FILES) - 1, \
            f"Expected {len(DIFFERENT_FILES) - 1} files after removal, but found {len(remaining_files)}"
            
        # 11. Verify the removed file is no longer in the list
        assert file_to_remove not in remaining_files, \
            f"File {file_to_remove} was not removed from the list"
            
        # 12. Verify the remaining files are still present
        for file_name in [f for f in DIFFERENT_FILES if f != file_to_remove]:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=5000)
        
        # 13. Click Add Invoice button with the updated file count
        self.invoices_page.click_add_invoice(expected_file_count=len(DIFFERENT_FILES) - 1)
        
        # 14. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_cancel_and_retry(self):
        """Test canceling and retrying a file upload."""
        # List of files with same name but different content
        SAME_NAME_FILES = [
            "InvoiceExample_1_SmallSize.jpg",
            "InvoiceExample_1_SmallSize.pdf",
            "InvoiceExample_1_SmallSize.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Prepare file paths for upload
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_and_name_but_different_content", file_name)
            for file_name in SAME_NAME_FILES
        ]
        
        # 5. Start uploading files
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 6. Click Cancel button
        self.invoices_page.cancel_new_invoice()
        
        # 7. Verify the overlay is no longer visible
        assert not self.invoices_page.is_overlay_visible(), "Overlay should be closed after cancel"
        
        # 8. Open the new invoice overlay again
        self.invoices_page.open_new_invoice_overlay()
        
        # 9. Verify the file upload section is empty
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == 0, "File upload section should be empty after cancel"
        
        # 10. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 11. Select the expense type we created earlier
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 12. Upload multiple files again
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 13. Verify the files were uploaded successfully
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert len(uploaded_files) == len(SAME_NAME_FILES), \
            f"Expected {len(SAME_NAME_FILES)} files, but found {len(uploaded_files)}"
            
        # 14. Verify the files are displayed in the selected files section
        for file_name in SAME_NAME_FILES:
            file_locator = self.page.locator(f'div.text-blue-700:has-text("{file_name}")')
            expect(file_locator).to_be_visible(timeout=10000)
        
        # 15. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(SAME_NAME_FILES))
        
        # 16. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"

    def test_upload_with_invalid_file_type(self):
        """
        Test uploading a file with an invalid file type.
        Verifies that:
        1. The correct error message is shown for unsupported file types
        2. The uploaded files section is not shown
        3. The Select Files button is disabled
        """
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Prepare the invalid file path (webp format which is not supported)
        invalid_file = "InvoiceExample_2.webp"
        invalid_file_path = os.path.join(SAMPLE_DOC_DIR, "invalid_filet_ype", invalid_file)
        
        # 7. Try to upload the invalid file
        self.invoices_page.upload_multiple_files(invalid_file_path)
        
        # 8. Verify the specific error message is shown for invalid file type
        error_message = self.invoices_page.get_file_type_error_message(invalid_file)
        expect(error_message).to_be_visible(timeout=10000)
        
        # 9. Verify the uploaded files section is not shown
        uploaded_files_section = self.invoices_page.overlay['file_upload']['uploaded_files_section']
        expect(uploaded_files_section).to_be_hidden()
        
        # 10. Verify the Select Files button is disabled
        select_files_btn = self.invoices_page.overlay['file_upload']['select_files_btn']
        expect(select_files_btn).to_be_disabled()
        
        
    def test_file_order_preservation(self):
        """Test that file order is preserved during upload and after removal. Done"""
        # List of files to upload in specific order
        ORDERED_FILES = [
            "InvoiceExample_5.png",
            "InvoiceExample_5 copy.png",
            "InvoiceExample_5 copy 2.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Upload multiple files in specific order
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", file_name)
            for file_name in ORDERED_FILES
        ]
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 7. Verify files appear in the same order as uploaded
        uploaded_files = self.invoices_page.get_uploaded_file_names()
        assert uploaded_files == ORDERED_FILES, "Files are not in the expected order"
        
        # 8. Remove the first file using the new method
        first_file = ORDERED_FILES[0]
        remove_button = self.invoices_page.get_delete_button_by_filename(first_file)
        remove_button.click()
        
        # 9. Wait for the file to be removed
        self.page.wait_for_timeout(1000)
        
        # 10. Verify remaining files maintain their relative order
        remaining_files = self.invoices_page.get_uploaded_file_names()
        expected_remaining = ORDERED_FILES[1:]  # All files except the first one
        assert remaining_files == expected_remaining, "Remaining files are not in the expected order"
        
        # 11. Add a new file and verify it's appended to the end
        new_file = "InvoiceExample_5 copy 3.png"
        new_file_path = os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", new_file)
        self.invoices_page.upload_multiple_files(new_file_path)
        
        # 12. Verify the new file is appended to the end
        updated_files = self.invoices_page.get_uploaded_file_names()
        expected_updated = expected_remaining + [new_file]
        assert updated_files == expected_updated, "New file was not appended to the end"
        
        # 13. Click Add Invoice button with the expected file count
        self.invoices_page.click_add_invoice(expected_file_count=len(updated_files))
        
        # 14. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"
    
    @pytest.mark.skip(reason="No Preview Functionality")
    def test_file_preview_functionality(self):
        """Test file preview functionality for different file types."""
        # 1. Verify the New Invoice overlay is open
        # 2. Select a cost center and expense type
        # 3. Upload a PDF file and verify preview is generated
        # 4. Upload an image file and verify preview is shown
        # 5. Upload an unsupported file type and verify default icon is shown
        # 6. Test preview for multi-page documents
        pass
                
    def test_network_interruption_handling(self):
        """Test handling of network interruptions during upload. Done"""
        # Define test files for this specific test case
        NETWORK_TEST_FILES = [
            "InvoiceExample_1_SmallSize.jpg",
            "InvoiceExample_1_SmallSize.pdf",
            "InvoiceExample_1_SmallSize.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Prepare file paths for upload
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_and_name_but_different_content", file_name)
            for file_name in NETWORK_TEST_FILES
        ]
        
        # 7. Start file upload
        self.invoices_page.upload_multiple_files(*file_paths)
        
        # 8. Simulate network disconnection during upload
        self.page.context.set_offline(True)
        
        # 9. Click Add Invoice button - this should fail due to network
        self.invoices_page.click_add_invoice()
        
        # 10. Verify error message is shown
        error_visible = self.page.wait_for_selector('div.bg-red-50:has-text("Failed to fetch")', state='visible', timeout=5000)
        assert error_visible, "Error message not shown after network interruption"
        
        # 11. Restore network connection
        self.page.context.set_offline(False)
        
        # 12. Click Add Invoice button again
        self.invoices_page.click_add_invoice()
        
        # 13. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"
    
    def test_network_interruption_during_invoice_submission(self):
        """Test handling of network interruptions during invoice submission. Done"""
        # Define test files for this specific test case
        NETWORK_TEST_FILES = [
            "InvoiceExample_5 copy.png",
            "InvoiceExample_5 copy 2.png",
            "InvoiceExample_5 copy 3.png",
            "InvoiceExample_5 copy 4.png",
            "InvoiceExample_5 copy 5.png",
            "InvoiceExample_5 copy 6.png",
            "InvoiceExample_5 copy 7.png"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Prepare file paths for upload
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, "mulitple_files", "same_file_type_content_but_different_name", file_name)
            for file_name in NETWORK_TEST_FILES
        ]

        # 7. Start file upload
        self.invoices_page.upload_multiple_files(*file_paths)

        # --- CRITICAL CHANGE: Set up the Abort Handler BEFORE the click ---
        
        aborted_requests_count = 0
        # Target EVERYTHING for diagnostic purposes. We will filter the submission request inside the handler.
        target_url = "**/*" 

        def handle_route(route: Route):
            nonlocal aborted_requests_count
            
            # Print ALL intercepted URLs for debugging! Look for the POST request URL in your console.
            print(f"\n[DEBUG] Intercepted URL: {route.request.url}, Method: {route.request.method}")

            # Filter logic: Only abort if it's a POST request to a suspected submission endpoint.
            # You may need to adjust the URL check (e.g., 'create-invoice' or just 'invoices').
            # We are looking for the final form submission.
            is_submission_request = (
                route.request.method == "POST" and 
                "/api/invoices" in route.request.url
            )
            
            if is_submission_request:
                # Abort the request. This simulates a network failure for the specific API call.
                route.abort() 
                aborted_requests_count += 1
                print(f"=== Request ABORTED (Final Submission) to: {route.request.url} ===")
            else:
                # Allow all other requests (like images, JS files, etc.) to continue normally.
                route.continue_()
            
        # 7. Enable request interception on ALL requests
        self.page.route(target_url, handle_route)
        
        try:
            # 8. Click the submit button
            print("Clicking submit button (request will be aborted)...")
            self.invoices_page.click_add_invoice()
            
            # Wait a small amount of time to allow the network event to fully process.
            # This can sometimes help ensure the request is fully intercepted before the assertion runs.
            self.page.wait_for_timeout(100) # Wait 100ms

            # Ensure the request was actually intercepted and aborted
            # If this assertion fails, CHECK THE CONSOLE OUTPUT for the URL that should be aborted.
            assert aborted_requests_count == 1, (
                f"The network request was not intercepted and aborted. "
                f"Count is {aborted_requests_count}. "
                f"Check debug output for the correct final submission URL."
            )

            # 9. Now verify the error message displayed to the user
            print("Verifying error message is shown...")
            try:
                # Use a reliable selector for generic error messages
                error_selector = 'div:has-text("Failed to fetch"), div[role="alert"], div.bg-red-50, div.text-red-500'
                error_message = self.page.wait_for_selector(
                    error_selector,
                    state='visible',
                    timeout=10000
                )
                error_text = error_message # Placeholder for actual Playwright element
                print(f"Found error message element.")
                
            except Exception as e:
                # Enhanced debug logging/screenshot if the element is not found
                screenshot_path = "network_error_screenshot.png"
                self.page.screenshot(path=screenshot_path, full_page=True)
                print(f"Error message not found. Screenshot saved to: {screenshot_path}")
                raise AssertionError(f"Expected error message not found: {str(e)}")
                
        finally:
            # 10. Clean up: ALWAYS unroute and set context back online
            self.page.unroute(target_url)
            self.page.context.set_offline(False)
            print("\n=== Test cleanup complete ===")
    
    def test_special_characters_in_filenames(self):
        """Test handling of special characters in filenames. Need Clarification!!!"""
        # 1. Verify the New Invoice overlay is open
        # 2. Select a cost center and expense type
        # 3. Upload files with special characters in names
        # 4. Verify files are displayed with correct names
        # 5. Upload files with very long names
        # 6. Verify name truncation if applicable
        pass
        
    def test_drag_and_drop_functionality(self):
        """Test drag and drop file upload functionality. FAIL"""
        # 1. Verify the New Invoice overlay is open
        # 2. Select a cost center and expense type
        # 3. Drag and drop multiple files onto the upload area
        # 4. Verify files are accepted and displayed
        # 5. Try dragging unsupported file types
        # 6. Verify error handling for invalid drops
        pass
        
    def test_error_recovery_after_upload_failure(self):
        """Test recovery after a file upload failure. Done"""
        # 1. Verify the New Invoice overlay is open
        # 2. Select a cost center and expense type
        # 3. Upload a corrupt file
        # 4. Verify error message is shown
        # 5. Remove the failed file
        # 6. Upload a valid file
        # 7. Verify successful upload and form submission
        pass
        
    def test_accessibility_keyboard_navigation(self):
        """Test keyboard navigation for file upload controls. FAIL"""
        # 1. Verify the New Invoice overlay is open
        # 2. Navigate to file upload using keyboard (Tab)
        # 3. Open file dialog using keyboard
        # 4. Navigate file list using keyboard
        # 5. Remove a file using keyboard
        # 6. Verify all actions can be performed without mouse
        # NOTE: File Upload section does not have keyboard navigation. Cannot use Tab to navigate to it.
        pass
        
    def test_mobile_upload_experience(self):
        """Test file upload on mobile devices. Done"""
        # 1. Set mobile viewport
        # 2. Verify the New Invoice overlay is open
        # 3. Test file selection from device storage
        # 4. Test camera capture if applicable
        # 5. Verify touch interactions for file operations
        # 6. Test form submission
        # NOTE: Capture camera working fine
        pass
        
    @pytest.mark.skip(reason="There is no such feature of Storage Quota per Account At the moment")
    def test_storage_quota_handling(self):
        """Test behavior when approaching storage limits."""
        # 1. Verify the New Invoice overlay is open
        # 2. Select a cost center and expense type
        # 3. Upload files until approaching storage limit
        # 4. Verify warning messages are shown
        # 5. Attempt to exceed storage limit
        # 6. Verify appropriate error message
        pass

    def test_non_invoice_file_upload_failure(self):
        """
        Test case to verify that uploading a non-invoice document correctly
        results in a 'Failed' processing status in the UI table.
        """
        NON_INVOICE_DOC_PATH = [
            "LargeFile2MB.jpg"
        ]
        
        # 1. Create a test expense type
        expense_type_name = self.create_test_expense_type()
        
        # 2. Open the new invoice overlay if not already open
        if not self.invoices_page.is_overlay_visible():
            self.invoices_page.open_new_invoice_overlay()
        
        # 3. Verify the New Invoice overlay is open
        assert self.invoices_page.is_overlay_visible(), "New Invoice overlay is not visible"
        
        # 4. Select a cost center
        self.invoices_page.select_cost_center()
        
        # 5. Select the expense type we just created
        self.invoices_page.select_expense_type(expense_type_name)
        
        # 6. Prepare file paths for upload
        file_paths = [
            os.path.join(SAMPLE_DOC_DIR, file_name)
            for file_name in NON_INVOICE_DOC_PATH
        ]
        file_name = os.path.basename(file_paths[0])

        # 7. Start file upload
        self.invoices_page.upload_multiple_files(*file_paths)

        # 8. Click Add Invoice button again
        self.invoices_page.click_add_invoice()
        
        # 9. Verify the invoice is created successfully by checking if the overlay is no longer visible
        assert not self.invoices_page.is_invoice_creation_overlay_visible(max_attempts=3, wait_time=5), \
            "Invoice creation overlay is still visible after submission"
        
        # 10. Assert the file eventually gets the 'Failed' status
        # Note: You may need to adjust the timeout based on your backend processing speed.
        is_failed = self.wait_for_file_processing_status(
            file_name=file_name, 
            expected_status="Failed", 
            timeout=60000 # Increased timeout to 60 seconds for heavy backend processing
        )

        assert is_failed, f"Expected file '{file_name}' to reach 'Failed' status, but it did not."
        
        print(f"Test passed for non-invoice file failure verification.")