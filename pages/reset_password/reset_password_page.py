import time
from playwright.sync_api import Page, expect

class ResetPasswordPage:
    def __init__(self, page: Page):
        self.page = page
        
        # Locators for Reset Password Page
        self.email_input = page.locator("input#email[type='email']")
        self.send_code_btn = page.get_by_role("button", name="Send Code")
        self.back_to_login_link = page.get_by_text("Back to Login")
        
        # Success and loading messages
        self.success_message = page.locator("p.text-sm.font-medium")
        self.loading_message = page.locator("div.bg-green-50.border-green-200.text-green-700 p.font-medium")
        
        # OTP Verification Locators
        self.otp_input = page.locator("input#otp")
        self.verify_btn = page.get_by_role("button", name="Verify")
        
        # New Password Locators
        self.new_password_input = page.locator("input#newPassword")
        self.confirm_password_input = page.locator("input#confirmPassword")
        self.reset_password_btn = page.get_by_role("button", name="Reset Password")
        
        # Success message after password reset
        self.reset_success_message = page.locator("p.text-sm.font-medium:has-text('Password has been reset successfully')")

    def navigate_to_reset_password(self, base_url: str = None):
        """Navigate to the reset password page.
        
        Args:
            base_url: The base URL of the application (e.g., https://example.com)
        """
        if base_url:
            reset_url = f"{base_url}/reset-password"
        else:
            reset_url = "/reset-password"
            
        self.page.goto(reset_url)
        return self
        
    def request_reset_code(self, email: str):
        """Request a reset code by entering email and clicking Send Code button."""
        self.email_input.fill(email)
        self.send_code_btn.click()
        
    def wait_for_otp_field(self, max_retries: int = 6, retry_delay: int = 5) -> bool:
        """Wait for OTP field to be visible with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            bool: True if OTP field is visible within retry attempts, False otherwise
        """
        for attempt in range(1, max_retries + 1):
            if self.otp_input.is_visible():
                return True
            print(f"OTP field not visible yet, attempt {attempt}/{max_retries}. Waiting {retry_delay} seconds...")
            time.sleep(retry_delay)
        return False
    
    def verify_otp(self, otp: str):
        """Enter OTP for password reset verification.
        
        Args:
            otp: 6-digit OTP code as string
        """
        if not self.otp_input.is_visible():
            raise ValueError("OTP input field is not visible")
            
        if len(otp) != 6:
            raise ValueError("OTP must be 6 digits long")
            
        self.otp_input.fill(otp)
        
    def click_verify_button(self):
        """Click the Verify button after entering OTP."""
        self.verify_btn.click()
        
    def set_new_password(self, new_password: str, confirm_password: str):
        """Set new password and confirm password.
        
        Args:
            new_password: New password to set
            confirm_password: Confirmation of new password
        """
        self.new_password_input.fill(new_password)
        self.confirm_password_input.fill(confirm_password)
        
    def submit_new_password(self):
        """Click the Reset Password button to submit the new password."""
        self.reset_password_btn.click()
        
    def is_reset_successful(self) -> bool:
        """Check if password reset was successful.
        
        Returns:
            bool: True if success message is visible, False otherwise
        """
        return self.reset_success_message.is_visible()
