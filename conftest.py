import pytest
from playwright.sync_api import Playwright, sync_playwright, Page

def pytest_addoption(parser):
    parser.addoption("--headless", action="store_true", default=False, help="Run tests in headless mode")

def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: mark test as smoke test")
    config.addinivalue_line("markers", "regression: mark test as regression test")

def pytest_generate_tests(metafunc):
    if "browser" in metafunc.fixturenames:
        browsers = metafunc.config.getoption("browser")
        if browsers:
            metafunc.parametrize("browser", browsers.split(","))

def pytest_exception_interact(node, call, report):
    if call.excinfo:
        print(f"\nTest failed: {call.excinfo.value}")
        print(f"Traceback: {call.excinfo.traceback}")

def pytest_sessionfinish(session, exitstatus):
    print(f"\nTest session finished. Exit status: {exitstatus}")

# Configuration for login tests
LOGIN_URL = "https://wize-invoice-dev-front.octaprimetech.com/login"
VALID_CREDENTIALS = {
    "email": "mamado.2000@gmail.com",
    "password": "Abc@1234"
}

# Test data for various scenarios
INVALID_CREDENTIALS = [
    {"email": "invalid@user.com", "password": "wrongpass"},
    {"email": "", "password": "Abc@1234"},
    {"email": "mamado.2000@gmail.com", "password": ""},
    {"email": "invalid", "password": "Abc@1234"},
    {"email": "mamado.2000@gmail.com", "password": "123456"}
]

EDGE_CASE_CREDENTIALS = [
    {"email": "mamado.2000@gmail.com    ", "password": "Abc@1234"},  # trailing spaces
    {"email": "mamado.2000@gmail.com", "password": "Abc@1234    "},  # trailing spaces
    {"email": "mamado.2000@gmail.com", "password": "Abc@1234\n"},  # newline
    {"email": "mamado.2000@gmail.com", "password": "Abc@1234\t"},  # tab
    {"email": "mamado.2000@gmail.com", "password": "Abc@1234\r"}   # carriage return
]
