from typing import List, Dict

def get_email_test_cases() -> List[Dict[str, str]]:
    """
    Returns a list of test cases for email validation.
    Each test case is a dictionary with 'email' and 'valid' keys.
    """
    base_email = "testingtito"
    domain = "example.com"
    
    test_cases = [
        # Valid email formats (kept for reference, but not used in invalid tests)
        {"email": f"{base_email}@{domain}", "valid": True},
        {"email": f"{base_email}.test@{domain}", "valid": True},
        {"email": f"{base_email}+test@{domain}", "valid": True},
        {"email": f"{base_email}-test@{domain}", "valid": True},
        {"email": f"{base_email}_test@{domain}", "valid": True},
        {"email": f"{base_email}.test.123@{domain}", "valid": True},
        {"email": f"{base_email}@sub.{domain}", "valid": True},
        {"email": f" {base_email}@{domain}", "valid": True},  # Leading space (auto-trimmed)
        {"email": f"{base_email}@{domain}.", "valid": True},  # Trailing dot (accepted by some systems)
        {"email": f'"{base_email}"@{domain}', "valid": True},  # Quotes around local part (valid per RFC)
        
        # Invalid email formats
        {"email": f"{base_email}", "valid": False},  # No @ or domain
        {"email": f"{base_email}@", "valid": False},  # No domain
        {"email": f"@{domain}", "valid": False},  # No local part
        {"email": f"{base_email}@domain", "valid": False},  # No TLD
        {"email": f"{base_email}@domain.", "valid": False},  # TLD cannot end with dot
        {"email": f"{base_email}@@{domain}", "valid": False},  # Double @
        {"email": f"{base_email} @{domain}", "valid": False},  # Space in local part
        {"email": f"{base_email}@{domain} ", "valid": False, "description": "Trailing space"},  # Trailing space
        {"email": f"{base_email}@ {domain}", "valid": False, "description": "Space after @"},
        {"email": f"{base_email}@ {domain.replace('.', ' .')}", "valid": False, "description": "Space before dot in domain"},
        {"email": f"{base_email}@{domain.replace('.', ' . ')}", "valid": False, "description": "Spaces around dot in domain"},
        {"email": f".{base_email}@{domain}", "valid": False},  # Leading dot
        {"email": f"{base_email}..test@{domain}", "valid": False},  # Consecutive dots
        {"email": f"{base_email}@[123.123.123.123]", "valid": False},  # IP address as domain
        {"email": f"{base_email}@{domain}..com", "valid": False},  # Multiple dots in domain
    ]
    
    return test_cases

def get_valid_emails() -> List[str]:
    """Returns a list of valid email addresses for testing."""
    return [tc["email"] for tc in get_email_test_cases() if tc["valid"]]

def get_invalid_emails() -> List[str]:
    """Returns a list of invalid email addresses for testing.
    
    This includes all test cases marked as invalid in the test_cases list.
    """
    # Get all test cases and filter only the invalid ones
    return [tc["email"] for tc in get_email_test_cases() if not tc["valid"]]

# Example usage:
if __name__ == "__main__":
    print("Valid email test cases:")
    for email in get_valid_emails():
        print(f"- {email}")
        
    print("\nInvalid email test cases:")
    for email in get_invalid_emails():
        print(f"- {email}")
