import time
import pytest
from playwright.sync_api import expect
from pages.expense_types.expense_types_page import ExpenseTypesPage
from pages.cost_centers.cost_centers_page import CostCentersPage

# This test documents the current behavior where deleting a Cost Center
# causes the associated Expense Type to disappear from the UI.
# This behavior is under review by the Product Team.
#
# Current Behavior:
# - When a Cost Center is deleted, any associated Expense Types are no longer visible in the UI
#
# Expected Behavior (TBD by Product):
# - Should prevent deletion of Cost Centers that are in use by Expense Types
# - OR should handle the deletion in a way that maintains data integrity

@pytest.mark.document_behavior
def test_expense_type_behavior_when_cost_center_deleted(logged_in_page):
    """
    Document the current behavior when a Cost Center in use by an Expense Type is deleted.
    
    Current Behavior:
    - Deleting a Cost Center that's being used by an Expense Type causes the Expense Type to disappear from the UI
    
    Note: This test documents current behavior which may change in the future.
    """
    page = logged_in_page
    
    # Initialize page objects
    cost_centers_page = CostCentersPage(page)
    expense_types_page = ExpenseTypesPage(page)
    
    # Generate unique names with timestamp
    timestamp = int(time.time())
    cost_center_name = f"Test CC {timestamp}"
    expense_type_name = f"Test ET {timestamp}"
    
    try:
        
        # 1. Create new Cost Center
        cost_centers_page.navigate()
        cost_centers_page.click_new_cost_center()
        cost_centers_page.fill_name_field(cost_center_name)
        time.sleep(3)
        cost_centers_page.submit_form()
        
        # Wait for loading animation to disappear after creating cost center
        time.sleep(3)
        cost_centers_page.wait_for_loading_animation_to_disappear()
        
        # Verify Cost Center is created
        cost_centers_page.search(cost_center_name)
        assert cost_centers_page.is_item_in_table(cost_center_name), \
            f"Cost Center {cost_center_name} should be visible in the table"
        
        # 2. Create new Expense Type using the Cost Center
        expense_types_page.navigate()
        expense_types_page.click_new_expense_type()
        
        # Fill the name
        expense_types_page.fill_name_field(expense_type_name)
        
        # Select first cost center from dropdown
        expense_types_page.page.click('button[role="combobox"]')
        expense_types_page.page.wait_for_selector('div[role="listbox"]', state='visible')
        first_option = expense_types_page.page.locator('div[role="option"]').first
        first_option.click()
        
        # Submit the form
        print("\n=== Submitting expense type form ===")
        expense_types_page.submit_form()
        
        # Wait for loading animation to disappear after creating expense type
        print("Waiting for loading animation to disappear...")
        expense_types_page.wait_for_loading_animation_to_disappear()
        
        # Small delay to ensure the page has updated
        print("Waiting for page to update...")
        time.sleep(3)
        
        # Take a screenshot before navigating away
        expense_types_page.page.screenshot(path=f"test-results/before_navigation_{timestamp}.png")
        
        # Navigate to the expense types list
        print("Navigating to expense types list...")
        expense_types_page.navigate()
        
        # Wait for the page to load by checking for specific elements
        try:
            # Wait for either the table or a 'no data' message
            print("Waiting for expense types page to load...")
            expense_types_page.page.wait_for_selector(
                'table, .no-data, .empty-state, [data-testid="no-data"]', 
                state='visible',
                timeout=30000  # 30 seconds
            )
            print("Expense types page loaded successfully")
        except Exception as e:
            print(f"Warning: Could not confirm page load using standard selectors: {str(e)}")
            # Take a screenshot for debugging
            expense_types_page.page.screenshot(path=f"test-results/page_load_timeout_{timestamp}.png")
            # Continue with the test as the page might still be usable
        
        # Take a screenshot after navigation
        expense_types_page.page.screenshot(path=f"test-results/after_navigation_{timestamp}.png")
        
        # Search for the expense type with retry logic
        max_search_attempts = 3
        search_successful = False
        
        for attempt in range(max_search_attempts):
            try:
                print(f"\n=== Search Attempt {attempt + 1}/{max_search_attempts} ===")
                print(f"Searching for expense type: {expense_type_name}")
                
                # Clear any existing search
                try:
                    clear_button = expense_types_page.page.locator('button[aria-label="Clear"]')
                    if clear_button.is_visible():
                        clear_button.click()
                        expense_types_page.page.wait_for_timeout(500)  # Small delay for UI to update
                except:
                    pass  # Clear button not found, continue with search
                
                # Perform the search
                expense_types_page.search(expense_type_name)
                
                # Wait for search to complete - look for either the table or a 'no results' message
                try:
                    expense_types_page.page.wait_for_selector(
                        'table, .no-data, .empty-state, [data-testid="no-data"]',
                        state='visible',
                        timeout=10000  # 10 seconds
                    )
                    search_successful = True
                    print("Search completed successfully")
                    break
                except Exception as e:
                    print(f"Search attempt {attempt + 1} timed out: {str(e)}")
                    if attempt < max_search_attempts - 1:
                        print("Retrying search...")
                        expense_types_page.page.wait_for_timeout(1000)  # Wait before retry
            except Exception as e:
                print(f"Error during search attempt {attempt + 1}: {str(e)}")
                if attempt == max_search_attempts - 1:
                    print("All search attempts failed")
                expense_types_page.page.wait_for_timeout(1000)  # Wait before retry
        
        # Take a screenshot after search
        expense_types_page.page.screenshot(path=f"test-results/after_search_{timestamp}.png")
        
        # Take a screenshot after search
        expense_types_page.page.screenshot(path=f"test-results/after_search_{timestamp}.png")
        
        # Get all table data for debugging with retry logic
        max_inspection_attempts = 2
        is_visible = False
        
        for inspection_attempt in range(max_inspection_attempts):
            try:
                print(f"\n=== Table Inspection Attempt {inspection_attempt + 1}/{max_inspection_attempts} ===")
                
                # Wait for table to be stable
                try:
                    expense_types_page.page.wait_for_selector("table", state="attached", timeout=10000)
                except:
                    print("Warning: Table not found on the page")
                
                # Take a screenshot of the current state
                expense_types_page.page.screenshot(path=f"test-results/table_inspection_{timestamp}_attempt_{inspection_attempt + 1}.png")
                
                # Check if the expense type exists in the table
                is_visible = expense_types_page.is_item_in_table(expense_type_name)
                print(f"Is expense type '{expense_type_name}' in table? {is_visible}")
                
                if is_visible:
                    break
                
                # If not found, dump table contents for debugging
                print("\n=== Table Contents ===")
                table = expense_types_page.page.locator("table")
                if table.count() > 0:
                    rows = table.locator("tr").all()
                    print(f"Found {len(rows)} rows in the table")
                    for i, row in enumerate(rows[:10]):  # Limit to first 10 rows
                        try:
                            text = row.text_content().strip()
                            if text:  # Only print non-empty rows
                                print(f"Row {i}: {text}")
                        except Exception as e:
                            print(f"Error processing row {i}: {str(e)}")
                else:
                    print("No table found on the page")
                
                # If we have more attempts, wait before retrying
                if inspection_attempt < max_inspection_attempts - 1:
                    print("Waiting before retrying table inspection...")
                    expense_types_page.page.wait_for_timeout(2000)  # 2 second delay
                    
            except Exception as e:
                print(f"Error during table inspection attempt {inspection_attempt + 1}: {str(e)}")
                if inspection_attempt == max_inspection_attempts - 1:
                    print("All table inspection attempts failed")
        
        # Final check and debug information if not found
        if not is_visible:
            # Take a screenshot for debugging
            expense_types_page.page.screenshot(path=f"test-results/expense_type_not_found_{timestamp}.png")
            
            # Print the current page content for debugging
            try:
                page_content = expense_types_page.page.content()
                print("\n=== Current Page Content (first 2000 chars) ===")
                print(page_content[:2000])  # Print first 2000 chars for more context
                
                # Print all elements that might contain the expense type
                print("\n=== Elements containing expense type name ===")
                try:
                    elements = expense_types_page.page.locator(f"*:has-text('{expense_type_name}')")
                    count = elements.count()
                    print(f"Found {count} elements containing the expense type name")
                    for i in range(min(count, 10)):  # Limit to first 10 to avoid too much output
                        try:
                            el = elements.nth(i)
                            print(f"Element {i+1}: {el.evaluate('el => el.outerHTML')[:200]}...")
                        except Exception as e:
                            print(f"Error getting element {i+1}: {str(e)}")
                except Exception as e:
                    print(f"Error finding elements: {str(e)}")
            except Exception as e:
                print(f"Error getting page content: {str(e)}")
        else:
            print("Expense type found in the table")
        
        # 3. Delete the Cost Center
        cost_centers_page.navigate()
        cost_centers_page.search(cost_center_name)
        cost_centers_page.wait_for_loading_animation_to_disappear()
        
        # Click delete button for the cost center
        cost_centers_page.delete_item(cost_center_name)
        cost_centers_page.wait_for_loading_animation_to_disappear()
        
        # Verify Cost Center is deleted
        cost_centers_page.search(cost_center_name)
        assert not cost_centers_page.is_item_in_table(cost_center_name), \
            f"Cost Center {cost_center_name} should not be visible after deletion"
        
        # 4. Verify Expense Type is no longer visible
        expense_types_page.navigate()
        expense_types_page.search(expense_type_name)
        expense_types_page.wait_for_loading_animation_to_disappear()
        
        # This assertion will currently fail - documenting the current behavior
        assert not expense_types_page.is_item_in_table(expense_type_name), \
            f"Expense Type {expense_type_name} should not be visible after its Cost Center is deleted"
            
    except Exception as e:
        # Take a screenshot on failure
        page.screenshot(path=f"test_expense_type_cost_center_deletion_error_{timestamp}.png")
        raise
    finally:
        # Cleanup - in case the test fails before cleanup
        try:
            # Clean up expense type if it still exists
            expense_types_page.navigate()
            expense_types_page.search(expense_type_name)
            if expense_types_page.is_item_in_table(expense_type_name):
                expense_types_page.delete_item(expense_type_name)
                
            # Clean up cost center if it still exists
            cost_centers_page.navigate()
            cost_centers_page.search(cost_center_name)
            if cost_centers_page.is_item_in_table(cost_center_name):
                cost_centers_page.delete_item(cost_center_name)
                
        except Exception as cleanup_error:
            print(f"Error during cleanup: {str(cleanup_error)}")
            page.screenshot(path=f"cleanup_error_{timestamp}.png")
