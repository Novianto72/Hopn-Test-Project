from playwright.sync_api import Page, expect

class SignUpPage:
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://wize-invoice-dev-front.octaprimetech.com/create-account"
        
        # Form fields
        self.first_name = page.locator("input#firstName")
        self.last_name = page.locator("input#lastName")
        self.email = page.locator("input#email")
        self.verify_email_btn = page.locator('//label[text()="Email"]/../div/button')
        self.country_code = page.locator("input#countryCode")
        self.phone_number = page.locator("input#phoneNumber")
        self.verify_phone_btn = page.locator('//label[text()="Phone Number"]/../div/div/div/button')
        self.password = page.locator("input#password")
        self.confirm_password = page.locator("input#confirmPassword")
        self.create_account_btn = page.locator("button[type='submit']")
    
    def navigate(self):
        self.page.goto(self.url)
        return self
    
    def is_loaded(self):
        return all([
            self.first_name.is_visible(),
            self.last_name.is_visible(),
            self.email.is_visible(),
            self.verify_email_btn.is_visible(),
            self.country_code.is_visible(),
            self.phone_number.is_visible(),
            self.verify_phone_btn.is_visible(),
            self.password.is_visible(),
            self.confirm_password.is_visible(),
            self.create_account_btn.is_visible()
        ])
    
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
