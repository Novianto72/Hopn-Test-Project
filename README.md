# Playwright Test Automation Framework

A comprehensive end-to-end test automation framework built with Playwright for testing a modern web application. This framework includes tests for various modules including Cost Centers, Expense Types, and Invoices.

## 🚀 Technologies Used

- **Playwright**: For reliable end-to-end testing
- **Python**: Primary programming language
- **Pytest**: Test framework for writing and running tests
- **Page Object Model (POM)**: Design pattern for better test maintenance
- **Git**: Version control

## 🧪 Key Features Tested

### Cost Centers Module
- Create, edit, and delete cost centers
- Search and filter functionality
- Input validation and error handling
- Pagination and sorting
- XSS protection in input fields

### Expense Types Module
- Create, edit, and delete expense types
- Form validations
- Search functionality
- Integration with cost centers

### Invoices Module
- Create new invoices
- Form validations
- File uploads
- Modal interactions

### Authentication
- Login with valid/invalid credentials
- Session management
- Error handling

## 🛠️ Setup Instructions

1. **Prerequisites**
   - Python 3.8+
   - Node.js (for Playwright browsers)
   - Git

2. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd playwright-test-automation
   ```

3. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements-test.txt
   playwright install
   ```

## 🚦 Running Tests

### Run all tests
```bash
pytest -v
```

### Run tests for a specific module
```bash
# Run cost center tests
pytest tests/cost_centers/ -v

# Run expense type tests
pytest tests/expense_types/ -v

# Run invoice tests
pytest tests/Invoices/ -v
```

### Run with specific browser
```bash
pytest --browser=chromium  # or firefox, webkit
```

### Run with headed mode
```bash
pytest --headed
```

## 📋 Test Cases

### Cost Centers
1. **Basic Operations**
   - Create new cost center
   - Edit existing cost center
   - Delete cost center
   - Input validation

2. **Search & Filter**
   - Search by name
   - Case-insensitive search
   - Special character handling

3. **Security**
   - XSS prevention in input fields
   - Input sanitization
   - Session management

### Expense Types
1. **Basic Operations**
   - Create new expense type
   - Edit existing expense type
   - Delete expense type
   - Required field validation

2. **Integration**
   - Association with cost centers
   - Data consistency

## 📝 Usage Examples

### Example Test: Create New Cost Center
```python
def test_create_cost_center(cost_centers_page):
    test_data = {
        "name": "Test Cost Center",
        "code": "TCC001"
    }
    
    # Open new cost center form
    cost_centers_page.click_new_button()
    
    # Fill and submit form
    cost_centers_page.fill_form(test_data)
    cost_centers_page.submit_form()
    
    # Verify success message
    assert cost_centers_page.is_success_message_visible()
    
    # Verify in the list
    assert cost_centers_page.is_item_in_list(test_data["name"])
```

### Example Test: Login
```python
def test_login(login_page):
    login_page.navigate()
    login_page.login("test@example.com", "secure_password")
    assert login_page.is_logged_in()
```

## 📂 Project Structure

```
playwright-test-automation/
├── dataInput/                  # Test data
├── pages/                      # Page object models
├── scripts/                    # Utility scripts
├── tests/                      # Test suites
│   ├── cost_centers/          # Cost center tests
│   ├── expense_types/         # Expense type tests
│   ├── Invoices/              # Invoice tests
│   └── utils/                 # Test utilities
├── .gitignore
├── README.md
├── conftest.py
├── pyproject.toml
└── requirements-test.txt
```

## 📊 Reporting

Test reports are generated in the `test_reports` directory after each test run. The framework includes:
- Detailed test execution logs
- Screenshots on failure
- Network traffic logs
- Performance metrics

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<div align="center">
  Made with ❤️ for quality assurance
</div>
