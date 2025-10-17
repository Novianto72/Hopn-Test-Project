import os
import uuid

def get_test_user():
    """Generate test user data with random values."""
    random_id = str(uuid.uuid4())[:8]
    return {
        "first_name": f"Test_{random_id}",
        "last_name": f"User_{random_id}",
        "email": f"testuser+{random_id}@example.com",
        "password": "ValidPass123!"
    }

def get_payment_method_data():
    """Generate test payment method data."""
    return {
        "card_number": "4242 4242 4242 4242",
        "expiry_date": "09/28",
        "cvc": "010",
        "cardholder_name": "Test Test",
        "phone_number": "082212341234"
    }
