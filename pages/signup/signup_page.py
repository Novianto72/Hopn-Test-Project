from playwright.sync_api import Page, expect
from typing import Optional, Tuple
import os
import time
from dotenv import load_dotenv
from tests.utils.email_utils import get_latest_otp_imap

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../../.env'))

# Email configuration
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_USER = os.getenv("IMAP_USER")
IMAP_PASS = os.getenv("IMAP_PASS")

# Debug IMAP configuration
print(f"IMAP Configuration - Host: {IMAP_HOST}, User: {IMAP_USER}, Password: {'***' if IMAP_PASS else 'Not set'}")

class SignUpPage:
    # Locators
    _FIRST_NAME = "input#firstName"
    _LAST_NAME = "input#lastName"
    _EMAIL = "input#email"
    _VERIFY_EMAIL_BTN = '//label[text()="Email"]/../div/button'
    _PASSWORD = "input#password"
    _CONFIRM_PASSWORD = "input#confirmPassword"
    _CREATE_ACCOUNT_BTN = "button[type='submit']"
    _EMAIL_VERIFICATION_CODE_INPUT = "input#emailOtp"
    _EMAIL_VERIFICATION_CHECK_BTN = '//label[text()="Email Verification Code"]/../div/button[text()="Check"]'

    # Payment method locators
    _CARD_RADIO_BUTTON = "input#payment-method-accordion-item-title-card"
    _CARD_NUMBER_INPUT = "input#cardNumber"
    _CARD_EXPIRY_INPUT = "input#cardExpiry"
    _CARD_CVC_INPUT = "input#cardCvc"
    _CARDHOLDER_NAME_INPUT = "input#billingName"
    _SAVE_INFO_CHECKBOX = "input#enableStripePass"
    _TERMS_CONSENT_CHECKBOX = "input#termsOfServiceConsentCheckbox"
    _SUBMIT_PAYMENT_BUTTON = "button[data-testid='hosted-payment-submit-button']"

    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/create-account"
        
        # Store locator selectors instead of locators to avoid stale element references
        self._first_name_selector = self._FIRST_NAME
        self._last_name_selector = self._LAST_NAME
        self._email_selector = self._EMAIL
        self._verify_email_btn_selector = self._VERIFY_EMAIL_BTN
        self._password_selector = self._PASSWORD
        self._confirm_password_selector = self._CONFIRM_PASSWORD
        self._create_account_btn_selector = self._CREATE_ACCOUNT_BTN
        self._email_verification_code_input_selector = self._EMAIL_VERIFICATION_CODE_INPUT
        self._email_verification_check_btn_selector = self._EMAIL_VERIFICATION_CHECK_BTN

    @property
    def first_name(self):
        return self.page.locator(self._first_name_selector)
        
    @property
    def last_name(self):
        return self.page.locator(self._last_name_selector)
        
    @property
    def email(self):
        return self.page.locator(self._email_selector)
        
    @property
    def verify_email_btn(self):
        return self.page.locator(self._verify_email_btn_selector)
        
    @property
    def password(self):
        return self.page.locator(self._password_selector)
        
    @property
    def confirm_password(self):
        return self.page.locator(self._confirm_password_selector)
        
    @property
    def create_account_btn(self):
        return self.page.locator(self._create_account_btn_selector)
        
    @property
    def email_verification_code_input(self):
        return self.page.locator(self._email_verification_code_input_selector)
        
    @property
    def email_verification_check_btn(self):
        return self.page.locator(self._email_verification_check_btn_selector)
    
        # Payment method properties
    @property
    def card_radio_button(self):
        return self.page.locator(self._CARD_RADIO_BUTTON)
    
    @property
    def card_number_input(self):
        return self.page.locator(self._CARD_NUMBER_INPUT)
    
    @property
    def card_expiry_input(self):
        return self.page.locator(self._CARD_EXPIRY_INPUT)
    
    @property
    def card_cvc_input(self):
        return self.page.locator(self._CARD_CVC_INPUT)
    
    @property
    def cardholder_name_input(self):
        return self.page.locator(self._CARDHOLDER_NAME_INPUT)
    
    @property
    def save_info_checkbox(self):
        return self.page.locator(self._SAVE_INFO_CHECKBOX)
    
    @property
    def terms_consent_checkbox(self):
        return self.page.locator(self._TERMS_CONSENT_CHECKBOX)
    
    @property
    def submit_payment_button(self):
        return self.page.locator(self._SUBMIT_PAYMENT_BUTTON)

    def navigate(self):
        self.page.goto(self.url)
        return self
    
    def is_loaded(self):
        return all([
            self.first_name.is_visible(),
            self.last_name.is_visible(),
            self.email.is_visible(),
            self.verify_email_btn.is_visible(),
            #self.country_code.is_visible(),
            #self.phone_number.is_visible(),
            #self.verify_phone_btn.is_visible(),
            self.password.is_visible(),
            self.confirm_password.is_visible(),
            self.create_account_btn.is_visible()
        ])
        
    def verify_email_otp(self, otp: str):
        """Enter and submit email OTP verification code"""
        self.email_verification_code_input.fill(otp)
        self.email_verification_check_btn.click()
        
    def verify_phone_otp(self, otp: str):
        """Enter and submit phone OTP verification code"""
        self.phone_verification_code_input.fill(otp)
        self.phone_verification_check_btn.click()
    
    def get_otp_from_email(self, email: str, max_attempts: int = 5, poll_interval: int = 5) -> Tuple[bool, str]:
        """
        Retrieve OTP from email using IMAP
        
        Args:
            email: Email address to check for OTP
            max_attempts: Maximum number of attempts to try getting OTP
            poll_interval: Time in seconds to wait between attempts
            
        Returns:
            Tuple of (success: bool, otp: str)
        """
        if not all([IMAP_USER, IMAP_PASS]):
            return False, "IMAP credentials not configured"
            
        for attempt in range(1, max_attempts + 1):
            print(f"Attempt {attempt}/{max_attempts} to retrieve OTP...")
            try:
                otp = get_latest_otp_imap(
                    imap_host=IMAP_HOST,
                    username=IMAP_USER,
                    password=IMAP_PASS,
                    email_to=email,
                    timeout_sec=30
                )
                
                if otp:
                    print(f"Successfully retrieved OTP: {otp}")
                    return True, otp
                    
                print(f"OTP not found yet, waiting {poll_interval} seconds...")
                time.sleep(poll_interval)
                
            except Exception as e:
                print(f"Error retrieving OTP: {str(e)}")
                if attempt == max_attempts:
                    return False, f"Failed to retrieve OTP after {max_attempts} attempts: {str(e)}"
                time.sleep(poll_interval)
                
        return False, f"Failed to retrieve OTP after {max_attempts} attempts"

    def fill_form(self, first_name: str, last_name: str, email: str, 
                 country_code: str, phone: str, password: str, confirm_password: str):
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.email.fill(email)
        self.country_code.fill(country_code)
        self.phone_number.fill(phone)
        self.password.fill(password)
        self.confirm_password.fill(confirm_password)
    
    def submit_form(self):
        self.create_account_btn.click()

    def setup_payment_method(self, payment_data):
        """
        Set up payment method with the provided data.
        """
        print("Setting up payment method...")
        
        # Click the card payment radio button using the provided XPath
        card_radio = self.page.locator('//input[@id="payment-method-accordion-item-title-card"]')
        card_radio.wait_for(state="visible", timeout=5000)
        card_radio.check(force=True)  # Use force=True to click even if not visible
        print("Selected card payment method")
        
        # Wait for card input fields to be visible
        self.card_number_input.wait_for(state="visible", timeout=5000)
        
        # Fill in card details
        self.card_number_input.fill(payment_data["card_number"])
        self.card_expiry_input.fill(payment_data["expiry_date"])
        self.card_cvc_input.fill(payment_data["cvc"])
        self.cardholder_name_input.fill(payment_data["cardholder_name"])
        print("Filled in card details")

        
        # Check checkboxes
        self.save_info_checkbox.check()

        # Fill in phone number
        phone_input = self.page.locator('input#phoneNumber')
        phone_input.wait_for(state="visible", timeout=10000)
        phone_input.fill(payment_data["phone_number"])
        print("Filled in phone number")

        # Check checkboxes
        self.terms_consent_checkbox.check()
        print("Checked required checkboxes")
        
        # Submit the payment form
        with self.page.expect_navigation(timeout=30000):
            self.submit_payment_button.click()
        print("Submitted payment form")
        
        # Verify we're back on the signup page
        #assert "/create-account" in self.page.url
        #print("Successfully completed payment setup and returned to signup page")