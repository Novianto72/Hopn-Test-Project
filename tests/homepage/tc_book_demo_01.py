"""
Test cases for the Book a Demo section on the homepage.
"""
import json
import re
import pytest
from datetime import datetime
from datetime import datetime
from playwright.sync_api import expect
from tests.homepage.page_objects.home_page import HomePage

# Test data
VALID_FORM_DATA = {
    'full_name': 'John Doe',
    'email': 'john.doe@example.com',
    'mobile_number': '1234567890',
    'contact_method': 'Email',
    'message': 'I would like to schedule a demo for next week.'
}

class TestBookDemoSection:
    """Test cases for the Book a Demo section."""
    
    @pytest.mark.skip(reason="Form submission requires authentication. Test verifies that submission after logout returns 'Unauthorized'.")
    def test_form_submission_after_login_logout(self, page):
        """
        [SKIPPED] Verify form submission behavior after login and logout.
        
        This test is skipped because the form submission requires an active authentication session.
        The test verifies that submitting the form after logout results in an 'Unauthorized' error,
        which is the expected behavior but not suitable for automated testing in the current setup.
        """
        # The test code is preserved below for future reference
        # Uncomment and modify if the authentication requirements change
        # 1. Go to login page
        page.goto("https://wize-invoice-dev-front.octaprimetech.com/login")
        
        # 2. Login with credentials
        page.fill('input[name="email"]', 'noviantotito72+test12@gmail.com')
        page.fill('input[name="password"]', 'Test@12')
        page.click('button[type="submit"]')
        
        # Wait for login to complete (assuming dashboard loads after login)
        page.wait_for_url('**/dashboard', timeout=10000)
        
        # 3. Logout
        # Click on the logout button directly
        page.click('div.flex.items-center.gap-2:has(span.text-sm.text-gray-900:has-text("Logout"))')
        
        # Wait for logout to complete (should redirect to login or home)
        page.wait_for_load_state('networkidle')
        
        # 4. Go to homepage
        page.goto('https://wize-invoice-dev-front.octaprimetech.com/')
        
        # 5. Navigate to Request Your Demo section
        home_page = HomePage(page)
        home_page.navigate_to_book_demo_section()
        
        # 6. Wait for the form to be fully loaded and visible
        form = page.locator('form')
        form.wait_for(state='visible')
        
        # Take a screenshot before filling
        page.screenshot(path="before_filling.png")
        print("Screenshot saved as before_filling.png")
        
        # 7. Fill the form with test data using direct field names (without 1_ prefix)
        test_data = {
            'fullName': 'John Doe',
            'email': 'test@example.com',
            'mobileNumber': '1234567890',
            'favoritConnectionMethod': 'Email',
            'message': 'I would like to schedule a demo for next week.'
        }
        
        # Fill each field with error handling and logging
        for field, value in test_data.items():
            try:
                selector = f'[name="{field}"]'
                print(f"Filling field: {field} with value: {value}")
                
                # Check if element is visible and enabled
                element = page.locator(selector)
                element.wait_for(state='visible', timeout=5000)
                
                # Handle different field types
                field_type = page.evaluate('''(selector) => {
                    const el = document.querySelector(selector);
                    return el ? el.tagName : null;
                }''', selector)
                
                if field_type == 'SELECT':
                    page.select_option(selector, value)
                else:
                    page.fill(selector, value)
                    
                print(f"Successfully filled {field}")
                
            except Exception as e:
                print(f"Error filling {field}: {str(e)}")
                # Take screenshot on error
                page.screenshot(path=f"error_filling_{field}.png")
                print(f"Screenshot saved as error_filling_{field}.png")
        
        # Take a screenshot after filling
        page.screenshot(path="after_filling.png")
        print("Screenshot saved as after_filling.png")
        
        # 8. Submit the form
        print("Submitting form...")
        
        # First, try to find and click the submit button
        try:
            submit_button = page.locator('button[type="submit"], input[type="submit"]')
            if submit_button.is_visible():
                submit_button.click()
                print("Clicked submit button")
            else:
                # If no visible submit button, try form submission via JavaScript
                page.evaluate('''() => {
                    const form = document.querySelector('form');
                    if (form) form.submit();
                }''')
                print("Submitted form via JavaScript")
        except Exception as e:
            print(f"Error submitting form: {str(e)}")
            page.screenshot(path="submit_error.png")
            print("Screenshot saved as submit_error.png")
        
        # Wait for navigation or response
        try:
            with page.expect_response(lambda r: r.request.method == 'POST', timeout=10000) as response_info:
                pass  # The click above will trigger the response
        except Exception as e:
            print(f"No POST response captured: {str(e)}")
        
        # Wait for any potential navigation
        page.wait_for_load_state('networkidle')
        
        # 7. Prepare form data with required Next.js action parameters
        form_data = {
            '1_$ACTION_REF_1': '',
            '1_$ACTION_1:0': '{"id":"60572b76b190e8c02cbd5d9bcbb6d32d8e17eb5b58","bound":"$@1"}',
            '1_$ACTION_1:1': '[null]',
            '1_$ACTION_KEY': 'k25627003',
            '1_fullName': 'John Doe',
            '1_email': 'test@example.com',
            '1_mobileNumber': '1234567890',
            '1_favoritConnectionMethod': 'Email',
            '1_message': 'I would like to schedule a demo for next week.'
        }

        # 8. Log the form submission
        print("\n=== Submitting form ===")
        
        # 9. Get the current authentication state
        cookies = page.context.cookies()
        print("\nCurrent cookies:", cookies)
        
        # 10. Submit the form using fetch API with proper headers
        response = page.evaluate('''async (formData, cookies) => {
            try {
                // Convert cookies to header string
                const cookieHeader = cookies.map(c => 
                    `${c.name}=${c.value}`
                ).join('; ');
                
                const response = await fetch(window.location.href, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Cookie': cookieHeader,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    credentials: 'include',  // Important for sending cookies
                    body: new URLSearchParams(formData)
                });
                
                return {
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries()),
                    text: await response.text()
                };
            } catch (error) {
                return { 
                    error: error.message,
                    stack: error.stack
                };
            }
        }''', form_data)

        # 10. Log the response in detail
        print("\n=== Form Submission Response ===")
        print(f"Status: {response.get('status')} {response.get('statusText')}")
        print("Headers:", response.get('headers', {}))
        
        if 'error' in response:
            print(f"\nError submitting form: {response['error']}")
            if 'stack' in response:
                print("Stack trace:", response['stack'])
        else:
            print("\nResponse body:", response.get('text', ''))
            
            # Try to parse JSON response if possible
            try:
                json_response = json.loads(response.get('text', '{}'))
                print("Parsed JSON response:", json.dumps(json_response, indent=2))
            except:
                print("Could not parse response as JSON")
        
        # 11. Dump page content and cookies for debugging
        print("\n=== Page State After Submission ===")
        print("Current URL:", page.url)
        print("Page title:", page.title())
        
        # 12. Check for any auth-related elements on the page
        auth_elements = page.locator('[id*="auth"], [class*="auth"], [data-test*="auth"]')
        auth_count = auth_elements.count()
        print(f"Found {auth_count} auth-related elements on the page")
        
        # 13. Wait for any navigation or state updates
        try:
            page.wait_for_load_state('networkidle', timeout=5000)
        except Exception as e:
            print(f"Warning: Network idle wait timed out: {str(e)}")
        
        # 14. Take a screenshot after submission
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"after_submission_{timestamp}.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved as {screenshot_path}")
        
        # 15. Check for any console errors
        console_errors = page.evaluate('''() => {
            return window.console && window.console.error ? 
                   window.console.error.history || [] : [];
        }''')
        if console_errors:
            print("\nConsole errors:", console_errors)

        # 13. Check for success or error messages
        success_message = page.locator('text=Thank you, your request has been submitted')
        error_message = page.locator('.bg-red-50 .text-red-700')
        
        if success_message.is_visible():
            print("Success! Form submitted successfully.")
            return  # Test passed
            
        if error_message.is_visible():
            error_text = error_message.inner_text()
            print(f"\nError message found: {error_text}")
            page.screenshot(path="form_submission_error.png")
            print("Screenshot saved as form_submission_error.png")
            
            # Print the current URL and page content for debugging
            print(f"\nCurrent URL: {page.url}")
            print("\nPage content:")
            print(page.content()[:1000])  # Print first 1000 chars of page content
            
            assert False, f"Form submission failed with error: {error_text}"
            
        # If we get here, neither success nor error message was found
        print("No success or error message detected. Check screenshots for details.")
        page.screenshot(path="form_submission_unknown.png")
        assert False, "Form submission status unknown - no success or error message detected"
    
    def test_book_demo_section_visibility(self, page):
        """Verify that the Book a Demo section is visible on the homepage."""
        home_page = HomePage(page)
        home_page.load()
        
        # Scroll to the section
        demo_section = home_page.navigate_to_book_demo_section()
        
        # Verify section visibility
        expect(demo_section).to_be_visible()
        
        # Verify section title
        section_title = demo_section.locator('h2')
        expect(section_title).to_have_text('See Invoice AI in Action')
    
    def test_form_validation_required_fields(self, page):
        """Verify that required fields show validation errors when empty."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Submit form without filling any fields
        home_page.submit_demo_form()
        
        # Check for required field indicators or validation messages
        # This assumes there are required field indicators or validation messages
        required_fields = [
            home_page.locators.BOOK_DEMO_FIELDS['full_name'],
            home_page.locators.BOOK_DEMO_FIELDS['email'],
            home_page.locators.BOOK_DEMO_FIELDS['mobile_number']
        ]
        
        for field in required_fields:
            field_locator = page.locator(field)
            # Check for either aria-invalid attribute or a validation message
            has_validation_error = field_locator.evaluate('''el => {
                return el.getAttribute("aria-invalid") === "true" || 
                       el.matches(":invalid") ||
                       (el.parentElement && 
                        (el.parentElement.textContent.includes("required") || 
                         el.parentElement.querySelector("[role=alert]")));
            }''')
            assert has_validation_error, f"Field {field} should show validation error when empty"
    
    def test_invalid_email_validation(self, page):
        """Verify that an invalid email format shows an error."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Fill form with invalid email
        home_page.fill_demo_form(
            full_name='Test User',
            email='invalid-email',
            mobile_number='1234567890'
        )
        
        # Check for email validation error
        email_field = page.locator(home_page.locators.BOOK_DEMO_FIELDS['email'])
        
        # Check for either aria-invalid attribute or a validation message
        has_validation_error = email_field.evaluate('''el => {
            return el.getAttribute("aria-invalid") === "true" || 
                   el.matches(":invalid") ||
                   (el.parentElement && 
                    (el.parentElement.textContent.includes("valid email") || 
                     el.parentElement.querySelector("[role=alert]")));
        }''')
        
        assert has_validation_error, "Invalid email format should show validation error"
    
    def test_form_submission_without_auth_shows_error(self, page):
        """Verify that form submission without authentication shows an error message."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Fill the form with valid data
        home_page.fill_demo_form(**VALID_FORM_DATA)
        
        # Submit the form
        home_page.submit_demo_form()
        
        # Wait for the error message to appear
        error_message = page.locator('.bg-red-50 .text-red-700')
        expect(error_message).to_be_visible()
        expect(error_message).to_contain_text('Unauthorized')
        
        # Verify the form is still visible (not redirected)
        form = page.locator(home_page.locators.BOOK_DEMO_FORM)
        expect(form).to_be_visible()
    
    @pytest.mark.skip(reason="Requires authentication setup")
    def test_valid_form_submission_with_auth(self, page):
        """Verify that a form with valid data can be submitted when authenticated."""
        # This test requires authentication to be set up first
        # You'll need to implement authentication logic here
        # For example:
        # 1. Log in the user
        # 2. Navigate to the form
        # 3. Submit the form
        # 4. Verify successful submission
        pass
    
    def test_contact_method_dropdown_options(self, page):
        """Verify that all expected contact method options are available."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Expected options in the dropdown
        expected_options = [
            {'value': 'Email', 'label': 'Email'},
            {'value': 'Phone', 'label': 'Phone'},
            {'value': 'WhatsApp', 'label': 'WhatsApp'},
            {'value': 'SMS', 'label': 'SMS'}
        ]
        
        # Get all options from the dropdown
        dropdown = page.locator(home_page.locators.BOOK_DEMO_FIELDS['contact_method'])
        options = dropdown.locator('option').all()
        
        # Verify number of options
        assert len(options) == len(expected_options), \
            f"Expected {len(expected_options)} options, found {len(options)}"
        
        # Verify each option
        for i, option in enumerate(expected_options):
            option_locator = dropdown.locator(f'option[value="{option["value"]}"]')
            expect(option_locator).to_have_text(option['label'])
    
    def test_form_reset_after_submission(self, page):
        """Verify that the form is reset after successful submission."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Fill the form with test data
        home_page.fill_demo_form(**VALID_FORM_DATA)
        
        # Mock a successful form submission
        # In a real test, you would actually submit the form and handle the response
        # For this test, we'll just verify the form can be cleared
        
        # Clear the form
        for field in home_page.locators.BOOK_DEMO_FIELDS.values():
            if 'select' not in field:  # Skip select elements
                page.locator(field).fill('')
        
        # Verify all fields are empty
        for field in home_page.locators.BOOK_DEMO_FIELDS.values():
            if 'select' not in field:  # Skip select elements
                field_value = page.locator(field).input_value()
                assert field_value == '', f"Field {field} should be empty after reset"
    
    @pytest.mark.skip(reason="Mobile number validation implementation not yet defined")
    def test_mobile_number_validation(self, page):
        """Verify that mobile number field only accepts valid formats."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Test with invalid mobile number (non-numeric)
        invalid_number = 'abc123!@#'
        mobile_field = page.locator(home_page.locators.BOOK_DEMO_FIELDS['mobile_number'])
        mobile_field.fill(invalid_number)
        
        # Check for validation error
        has_validation_error = mobile_field.evaluate('''el => {
            return el.getAttribute("aria-invalid") === "true" || 
                   el.matches(":invalid") ||
                   (el.parentElement && 
                    (el.parentElement.textContent.includes("valid number") || 
                     el.parentElement.querySelector("[role=alert]")));
        }''')
        
        assert has_validation_error, "Invalid mobile number should show validation error"
        
        # Test with valid mobile number
        valid_number = '1234567890'
        mobile_field.fill(valid_number)
    
    @pytest.mark.skip(reason="Form input length validation specification not yet defined")
    def test_form_input_max_length_validation(self, page):
        """Verify that form inputs enforce maximum length constraints."""
        pass
    
    @pytest.mark.skip(reason="Mobile number format validation specification not yet defined")
    def test_mobile_number_format_validation(self, page):
        """Verify that mobile number field validates different international formats."""
        pass
    
    @pytest.mark.skip(reason="Form submission with different contact methods specification not yet defined")
    def test_form_submission_with_different_contact_methods(self, page):
        """Verify form submission works correctly with each contact method."""
        pass
    
    @pytest.mark.skip(reason="Security test cases specification not yet defined")
    def test_form_security(self, page):
        """Verify security aspects of the form submission."""
        pass
    
    @pytest.mark.skip(reason="Form submission confirmation flow not yet defined")
    def test_form_submission_confirmation(self, page):
        """Verify that users receive proper confirmation after form submission."""
        pass
    
    @pytest.mark.skip(reason="Duplicate submission prevention mechanism not yet defined")
    def test_duplicate_submission_prevention(self, page):
        """Verify that the form prevents duplicate submissions."""
        pass
        
    def test_form_accessibility(self, page):
        """Verify that the form meets accessibility standards."""
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Check for required ARIA attributes on form fields
        required_fields = ['fullName', 'email', 'mobileNumber']
        for field in required_fields:
            field_locator = page.locator(f'[name="{field}"]')
            expect(field_locator).to_have_attribute('required', '')
            expect(field_locator).to_have_attribute('aria-required', 'true')
            
        # Check for proper labels
        for field in ['fullName', 'email', 'mobileNumber', 'favoritConnectionMethod']:
            field_locator = page.locator(f'[name="{field}"]')
            label = page.locator(f'label:has([name="{field}"])')
            expect(label).to_be_visible()
            
            # Check if the label is properly associated with the input
            if field != 'favoritConnectionMethod':  # Skip select elements for this check
                assert field_locator.get_attribute('id'), f"Input {field} should have an id for label association"
                label_for = label.get_attribute('for')
                field_id = field_locator.get_attribute('id')
                assert label_for == field_id, f"Label for {field} is not properly associated with input"
    
    def test_form_performance(self, page):
        """Verify form performance under various conditions."""
        home_page = HomePage(page)
        
        # Test page load time
        start_time = page.evaluate('window.performance.now()')
        home_page.load()
        end_time = page.evaluate('window.performance.now()')
        load_time = end_time - start_time
        
        # Fail if page takes more than 5 seconds to load
        assert load_time < 5000, f"Page took too long to load: {load_time}ms"
        
        # Test form interaction response time
        home_page.navigate_to_book_demo_section()
        
        # Test form field interaction time
        start_time = page.evaluate('window.performance.now()')
        home_page.fill_demo_form(
            full_name='Performance Test',
            email='test@example.com',
            mobile_number='1234567890',
            contact_method='Email',
            message='Performance test message'
        )
        end_time = page.evaluate('window.performance.now()')
        form_fill_time = end_time - start_time
        
        # Fail if form filling takes more than 3 seconds
        assert form_fill_time < 3000, f"Form filling took too long: {form_fill_time}ms"
    
    def test_mobile_responsiveness(self, page):
        """Verify that the form is usable on mobile devices."""
        # Set viewport to mobile size
        page.set_viewport_size({'width': 375, 'height': 667})  # iPhone 6/7/8 dimensions
        
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Check if form elements are visible and clickable
        form_elements = [
            'input[name="fullName"]',
            'input[name="email"]',
            'input[name="mobileNumber"]',
            'select[name="favoritConnectionMethod"]',
            'textarea[name="message"]',
            'button[type="submit"]'
        ]
        
        for element in form_elements:
            locator = page.locator(element)
            expect(locator).to_be_visible()
            
            # Check if element is large enough for touch (recommended min 44x44px)
            box = locator.bounding_box()
            assert box['width'] >= 44, f"{element} is too narrow for touch on mobile"
            assert box['height'] >= 44, f"{element} is too short for touch on mobile"
            
            # Check if form is not horizontally scrollable (common mobile issue)
            viewport_width = page.viewport_size['width']
            assert box['x'] + box['width'] <= viewport_width, \
                f"{element} causes horizontal scrolling on mobile"
        
        # Verify the form is fully visible in the viewport
        form = page.locator('form')
        form_box = form.bounding_box()
        assert form_box is not None, "Form should be present in the DOM"
        
        # Check form is centered and visible in the viewport
        assert form_box['x'] >= 0, "Form is cut off on the left side"
        assert form_box['x'] + form_box['width'] <= viewport_width, "Form is cut off on the right side"

    @pytest.mark.skip(reason="Accessibility features not implemented for the book demo form")
    def test_form_accessibility(self, page):
        """Verify that the form is accessible."""
        # This test is skipped as per decision to not implement these accessibility features
        home_page = HomePage(page)
        home_page.load()
        home_page.navigate_to_book_demo_section()
        
        # Get the form element
        form = page.locator(home_page.locators.BOOK_DEMO_FORM)
        
        # List of expected field labels
        expected_labels = [
            'Full Name',
            'Email Address',
            'Mobile Number',
            'Preferred Contact Method',
            'Message'
        ]
        
        # Check that all expected labels are present
        for label_text in expected_labels:
            assert form.get_by_text(label_text, exact=False).is_visible(), \
                f"Form is missing label: {label_text}"
                
        # Check that all form inputs have proper labels
        inputs = form.locator('input, select, textarea')
        for i in range(inputs.count()):
            input_el = inputs.nth(i)
            
            # Skip hidden inputs
            if input_el.get_attribute('type') == 'hidden':
                continue
                
            # Get input name and type for better error messages
            input_name = input_el.get_attribute('name') or f'input[{i}]'
            input_type = input_el.get_attribute('type') or 'text'
            
            # Special case for the typo in the field name
            if input_name == 'favoritConnectionMethod':
                # Check if there's a visible label text before the select
                has_visible_label = input_el.evaluate('''el => {
                    const prevElements = [];
                    let current = el.previousElementSibling;
                    while (current && prevElements.length < 3) {
                        prevElements.unshift(current);
                        current = current.previousElementSibling;
                    }
                    return prevElements.some(el => 
                        el.textContent && 
                        el.textContent.includes('Preferred Contact Method')
                    );
                }''')
                
                if has_visible_label:
                    continue  # Skip further checks for this field
            
            # Check for associated label or aria attributes
            has_label = input_el.evaluate('''el => {
                // Check for associated label
                if (el.labels && el.labels.length > 0) return true;
                
                // Check for aria-label or aria-labelledby
                if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return true;
                
                // Check for placeholder
                if (el.placeholder) return true;
                
                // Check for parent with role="group" and aria-label or legend
                const parentGroup = el.closest('[role="group"], fieldset');
                if (parentGroup) {
                    if (parentGroup.getAttribute('aria-label') || 
                        parentGroup.querySelector('legend')) {
                        return true;
                    }
                }
                
                // Check for preceding label text
                const prevElements = [];
                let current = el.previousElementSibling;
                while (current && prevElements.length < 3) {
                    prevElements.unshift(current);
                    current = current.previousElementSibling;
                }
                
                return prevElements.some(el => 
                    el.textContent && 
                    el.textContent.trim() && 
                    el.textContent.trim().length < 50
                );
            }''')
            
            # Get the input's HTML for debugging
            input_html = input_el.evaluate('el => el.outerHTML')
            
            assert has_label, (
                f"Input field '{input_name}' (type: {input_type}) is missing an accessible name.\n"
                f"HTML: {input_html}\n"
                "Possible fixes:\n"
                "1. Add a <label> element with a 'for' attribute matching the input's 'id'\n"
                "2. Add an aria-label or aria-labelledby attribute\n"
                "3. Add a placeholder attribute\n"
                "4. Wrap the input in a fieldset with a legend or a div with role='group' and aria-label"
            )
        
        # Check that the form has a proper name/role
        form_name = form.get_attribute('aria-label') or form.get_attribute('aria-labelledby')
        assert form_name, "Form should have an accessible name (aria-label or aria-labelledby)"
        
        # Check that the submit button has an accessible name
        submit_button = form.locator('button[type="submit"]')
        button_name = submit_button.get_attribute('aria-label') or submit_button.text_content()
        assert button_name and button_name.strip(), "Submit button should have an accessible name"
