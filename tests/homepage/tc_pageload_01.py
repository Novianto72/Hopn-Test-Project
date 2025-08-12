from playwright.sync_api import expect

def test_page_load(home_page):
    """
    Verify the landing page loads correctly by checking:
    1. Page title is correct
    2. Page contains expected text content
    3. Page has interactive elements
    """
    # 1. Check page title
    expect(home_page).to_have_title("Invoice AI")
    
    # 2. Wait for page to be fully loaded (with timeout)
    home_page.wait_for_load_state('networkidle', timeout=10000)  # 10 seconds timeout
    
    # 3. Check for expected text content (case insensitive, more flexible)
    expected_texts = [
        'Invoice AI',
        'invoice',  # Common word that should be on the page
        'get started'  # Common CTA text
    ]
    
    for text in expected_texts:
        try:
            expect(home_page.get_by_text(text, exact=False).first).to_be_visible(timeout=5000)
            break  # If any text is found, that's sufficient
        except:
            continue
    else:
        # If no expected text is found, the test will fail here
        assert False, "None of the expected text content was found on the page"
    
    # 4. Verify the page has interactive elements (links, buttons, etc.)
    interactive_elements = home_page.locator('a, button, [role="button"], [tabindex]')
    assert interactive_elements.count() > 0, "No interactive elements found on the page"
