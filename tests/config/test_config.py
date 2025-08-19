"""Test configuration and URL constants for the test suite."""
from typing import Dict, Any

# Base URL configuration
BASE_URL = "https://wize-invoice-dev-front.octaprimetech.com"

# Application URLs
URLS = {
    "LOGIN": f"{BASE_URL}/login",
    "HOME": f"{BASE_URL}/",
    "DASHBOARD": f"{BASE_URL}/dashboard",
    "COST_CENTERS": f"{BASE_URL}/cost-center"
}

# Test credentials
CREDENTIALS = {
    "DEFAULT": {
        "email": "noviantotito72+test12@gmail.com",
        "password": "Test@12"
    },
    "EMPTY_STATE": {
        "email": "noviantotito72+test11@gmail.com",
        "password": "Test@11"
    }
}

# Test execution configuration
class TestConfig:
    """Test execution configuration."""
    HEADLESS = False
    SLOW_MO = 100  # milliseconds
    TIMEOUT = 30000  # milliseconds
    VIEWPORT = {"width": 1440, "height": 900}  # MacBook Pro 14-inch friendly viewport

# Environment-specific configurations
ENVIRONMENTS = {
    "dev": {
        "base_url": "https://wize-invoice-dev-front.octaprimetech.com",
        "api_url": "https://api-dev.example.com"
    },
    "staging": {
        "base_url": "https://wize-invoice-staging.example.com",
        "api_url": "https://api-staging.example.com"
    },
    "prod": {
        "base_url": "https://wize-invoice.example.com",
        "api_url": "https://api.example.com"
    }
}

# Default environment to use
CURRENT_ENV = "dev"

def get_environment_config(env: str = None) -> Dict[str, Any]:
    """Get configuration for the specified environment.
    
    Args:
        env: Environment name (dev, staging, prod). If None, uses CURRENT_ENV.
        
    Returns:
        Dict containing the environment configuration.
    """
    env = env or CURRENT_ENV
    return ENVIRONMENTS.get(env, ENVIRONMENTS[CURRENT_ENV])
