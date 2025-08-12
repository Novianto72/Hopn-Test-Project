Feature: Expense Types Page
  As an authenticated user
  I want to view the expense types page
  So that I can manage expense types

  Scenario: Loading the expense types page
    Given I am logged into the application
    When I navigate to the expense types page
    Then I should see the page title "Invoice AI"
    And I should see the main heading "Expense Types"
    And I should see the "New Expense Type" button
    And I should see the search input field
