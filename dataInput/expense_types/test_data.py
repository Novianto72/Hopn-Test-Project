"""Test data for Expense Types tests."""

# Common test data
# Credentials for tests with existing data
credentials = {
    "email": "test.withdata@example.com",
    "password": "test123"
}

# Credentials for tests with empty state
empty_state_credentials = {
    "email": "test.empty@example.com",
    "password": "test123"
}

# Credentials for non-empty state tests (same as default credentials for now)
non_empty_state_credentials = credentials

# Empty state message
empty_state_message = "No expense types found."

# Test data for refresh functionality
refresh_test_data = {
    "timeouts": {
        "page_load": 30000,  # 30 seconds
        "element_visibility": 10000  # 10 seconds
    },
    "expected_elements": [
        "h1:has-text('Expense Types')",
        "button:has-text('New Expense Type')",
        "button:has-text('Refresh')",
        "table"
    ]
}
