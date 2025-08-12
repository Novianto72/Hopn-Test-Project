"""Test data for Cost Centers tests."""
import re
import random
import string
from datetime import datetime, timedelta

def random_string(length: int) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(length))

def random_number(length: int) -> str:
    """Generate a random numeric string of fixed length."""
    numbers = string.digits
    return ''.join(random.choice(numbers) for _ in range(length))

# Common test data
# Credentials for tests with existing data
credentials = {
    "email": "noviantotito72+test12@gmail.com",
    "password": "Test@12"
}

# Credentials for empty state tests
empty_state_credentials = {
    "email": "noviantotito72+test11@gmail.com",
    "password": "Test@11"
}

# Credentials for non-empty state tests (same as default credentials for now)
non_empty_state_credentials = credentials

# Cost Center test data
cost_center_test_data = {
    # Basic cost center data
    "basic_cost_center": {
        "name": f"Test CC {random_string(5)}",
        "description": f"Test Description {random_string(10)}",
        "code": f"CC-{random_number(4)}",
        "is_active": True
    },
    
    # Cost center with special characters
    "special_chars_cost_center": {
        "name": f"Test CC !@#${random_string(3)}",
        "description": f"Special chars description {random_string(5)}!@#$",
        "code": f"SP-{random_number(4)}",
        "is_active": True
    },
    
    # Cost center with long text
    "long_text_cost_center": {
        "name": f"Long Name {'x' * 50}",
        "description": f"Long description {'x' * 200}",
        "code": f"LG-{random_number(4)}",
        "is_active": True
    },
    
    # Inactive cost center
    "inactive_cost_center": {
        "name": f"Inactive CC {random_string(5)}",
        "description": "Inactive test cost center",
        "code": f"IN-{random_number(4)}",
        "is_active": False
    }
}

# Navigation test data
navigation_test_data = {
    "expected_url": "https://wize-invoice-dev-front.octaprimetech.com/cost-center",
    "page_title": "Cost Centers",
    "elements_to_verify": [
        {"selector": "button:has-text('New Cost Center')", "description": "New Cost Center button"},
        {"selector": "[placeholder='Search cost centers...']", "description": "Search input field"},
        {"selector": "table", "description": "Cost centers table"}
    ]
}

# Search test data
search_test_data = {
    # Common search terms that should return results
    "valid_search_terms": ["test", "Center", "Cost", "CC", "Active"],
    
    # Search terms that should return no results
    "invalid_search_terms": ["nonexistent123", "xyz123", "!@#$"],
    
    # Special characters search terms
    "special_char_search_terms": ["!@#$", "%^&*", "()_+"],
    
    # Long search terms
    "long_search_terms": ["a" * 100, "1" * 100],
    
    # Search result messages
    "messages": {
        "no_results": "No cost centers found.",  # Note the period at the end to match the actual message
        "search_placeholder": "Search cost centers..."
    },
    
    # Search result verification
    "result_verification": {
        "timeout_ms": 10000,  # 10 seconds timeout for search operations
        "retry_attempts": 3,  # Number of retry attempts for flaky tests
        "retry_delay_seconds": 2  # Delay between retry attempts
    }
}

# Refresh test data
refresh_test_data = {
    "timeouts": {
        "page_load": 15000,  # 15 seconds timeout for page load
        "element_visibility": 5000,  # 5 seconds timeout for element visibility
        "counter_refresh": 10000  # 10 seconds timeout for counter refresh
    },
    "expected_elements": [
        "h1:has-text('Cost Centers')",
        "div.text-2xl",
        "button:has-text('Refresh')"
    ]
}

# Edit/Delete test data
edit_delete_test_data = {
    "menu_options": {
        "edit": {
            "name": "Edit",
            "expected_modal_title": "Edit Cost Center",
            "expected_modal_description": "Fill in the details",
            "fields": ["Name"],
            "buttons": ["Cancel", "Edit cost center"]
        },
        "delete": {
            "name": "Delete",
            "confirmation_text": "Are you sure you want to delete this cost center?",
            "button_class": "text-red-600"
        }
    },
    "timeouts": {
        "element_visibility": 10000  # 10 seconds timeout for element visibility
    }
}

# Required validation test data
required_validation_test_data = {
    "modal": {
        "title": "New Cost Center",
        "description": "Fill in the details",
        "fields": ["Name"],
        "buttons": ["Cancel", "Add cost center"]
    },
    "timeouts": {
        "modal_visibility": 10000,  # 10 seconds timeout for modal visibility
        "validation_check": 5000  # 5 seconds timeout for validation check
    }
}

# Cancel button test data
cancel_button_test_data = {
    "modal": {
        "title": "New Cost Center",
        "close_methods": [
            {
                "type": "cancel_button",
                "selector": "Cancel",  # Text content of the button
                "timeout": 4500  # 4.5 seconds to wait for modal to close
            },
            {
                "type": "close_button",
                "selector": "svg.lucide-x.w-4.h-4",
                "timeout": 4500  # 4.5 seconds to wait for modal to close
            }
        ]
    }
}

# Multiple creations test data
multiple_creations_test_data = {
    "iterations": 5,  # Number of cost centers to create and delete
    "base_name": "Test Cost Center",  # Base name for cost centers
    "timeouts": {
        "page_load": 30000,  # 30 seconds timeout for page load
        "modal_visibility": 10000,  # 10 seconds timeout for modal visibility
        "element_visibility": 5000,  # 5 seconds timeout for element visibility
        "search_delay": 1000  # 1 second delay after search
    },
    "confirmation_dialog": {
        "timeout": 5,  # 5 seconds timeout for dialog handling
        "retry_interval": 0.1  # 100ms retry interval
    }
}

# New button test data
new_button_test_data = {
    "test_cost_center_name_prefix": "Test Cost Center",
    "modal_selectors": {
        'title': [
            {'type': 'role', 'role': 'heading', 'name': re.compile('New Cost Center', re.IGNORECASE)},
            {'type': 'xpath', 'selector': '//*[contains(@class, "modal")]//h1|h2|h3'},
            {'type': 'xpath', 'selector': '//*[contains(text(), "Cost Center") and (self::h1 or self::h2 or self::h3)]'}
        ],
        'name_input': [
            {'type': 'label', 'text': 'Name *'},
            {'type': 'placeholder', 'text': 'Name of your Cost Center...'},
            {'type': 'xpath', 'selector': '//input[@name="name"]'}
        ],
        'submit_button': [
            {'type': 'role', 'role': 'button', 'name': re.compile('Add Cost Center', re.IGNORECASE)},
            {'type': 'role', 'role': 'button', 'name': re.compile('Submit', re.IGNORECASE)},
            {'type': 'xpath', 'selector': '//button[contains(., "Add") or contains(., "Submit")]'}
        ],
        'cancel_button': [
            {'type': 'role', 'role': 'button', 'name': re.compile('Cancel', re.IGNORECASE)},
            {'type': 'xpath', 'selector': '//button[contains(., "Cancel")]'}
        ],
        'overlay': [
            {'type': 'css', 'selector': '.modal-overlay, [role=dialog] + .backdrop, .MuiBackdrop-root, .backdrop-blur'}
        ]
    },
    "timeouts": {
        "navigation_retry": 3,  # Number of navigation retry attempts
        "retry_delay_ms": 2000,  # 2 seconds delay between retries
        "element_visibility": 10000,  # 10 seconds timeout for element visibility
        "modal_visibility": 10000,  # 10 seconds timeout for modal visibility
        "page_load": 30000  # 30 seconds timeout for page load
    },
    "test_directories": {
        "screenshots": "test-results"
    }
}

# Pagination test data
pagination_test_data = {
    "selectors": {
        # More specific selector that targets the pagination container at the bottom of the table
        "pagination_container": "div.bg-gray-50.px-6.py-4.border-t.border-gray-200.flex.items-center.justify-between",
        "rows_per_page_selector": "select.border",  # The rows per page dropdown
        "current_page_info": "div.text-sm.font-medium.text-gray-900:has-text('Page')",  # Page X of Y text
        "navigation_buttons": "div.flex.items-center.gap-1",  # Container with all navigation buttons
        "table_rows": "tbody tr",
        "current_page": "[aria-current='page']"
    },
    "records_per_page_options": [5, 10, 25, 50],
    "labels": {
        "next_button": "Next",
        "prev_button": "Previous"
    },
    "timeouts": {
        "page_load": 10000,  # 10 seconds
        "element_visibility": 5000  # 5 seconds
    }
}
