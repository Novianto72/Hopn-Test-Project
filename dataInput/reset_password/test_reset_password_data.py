def get_test_user():
    return {
        "email": "testingtito09+test01@gmail.com",
        "new_password": "NewSecurePassword123!",
        "invalid_password": "weak"
    }

def get_password_validation_messages():
    return {
        "min_length": "Password must be at least 8 characters",
        "uppercase": "Password must contain at least one uppercase letter",
        "number": "Password must contain at least one number",
        "special_char": "Password must contain at least one special character",
        "mismatch": "Passwords do not match"
    }
