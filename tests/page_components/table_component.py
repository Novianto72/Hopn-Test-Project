from playwright.sync_api import Page, expect
from typing import List, Dict, Optional

class TableComponent:
    def __init__(self, page: Page, table_selector: str = 'table[data-slot="table"]'):
        self.page = page
        self.table_selector = table_selector
        self.table = page.locator(table_selector)
        
    def get_rows(self):
        """Get all data rows from the table body, excluding the header row"""
        # First wait for the table body to be present
        self.page.locator('tbody[data-slot="table-body"]').wait_for(state='visible')
        
        # Get all rows with the data-slot="table-row" attribute
        rows = self.page.locator('tr[data-slot="table-row"]').all()
        
        # If no rows found, try alternative selector
        if not rows:
            rows = self.page.locator('tbody[data-slot="table-body"] > tr').all()
            
        # Filter out any header rows that might be included
        def is_data_row(row):
            try:
                attr = row.get_attribute('data-slot') or ''
                return 'table-head' not in attr
            except:
                return True  # If we can't check, assume it's a data row
        
        rows = [row for row in rows if is_data_row(row)]
        return rows
    
    def get_row_by_text(self, text: str):
        """Get the first row that contains the specified text"""
        return self.table.locator('tbody tr').filter(has_text=text).first
    
    def get_row_data(self, row_element) -> Dict[str, str]:
        """Get data from a table row as a dictionary with unique identifier"""
        # Default values
        name = ''
        cost_center = ''
        created_at = ''
        
        try:
            # Get name from first cell with font-medium class
            name_elem = row_element.locator('td:nth-child(1) div.font-medium').first
            if name_elem.count() > 0:
                name = name_elem.inner_text().strip()
            
            # Get cost center from second cell
            cost_center_elem = row_element.locator('td:nth-child(2) div.text-gray-700').first
            if cost_center_elem.count() > 0:
                cost_center = cost_center_elem.inner_text().strip()
            
            # Get created_at from third cell
            created_at_elem = row_element.locator('td:nth-child(3) div.text-gray-700').first
            if created_at_elem.count() > 0:
                created_at = created_at_elem.inner_text().strip()
            
            # Fallback if any field is empty
            if not all([name, cost_center, created_at]):
                # Get all cells in the row
                cells = row_element.locator('td').all()
                cell_texts = [cell.inner_text().strip() for cell in cells[:3] if cell]
                
                if cell_texts:
                    name = name or (cell_texts[0] if len(cell_texts) > 0 else '')
                    cost_center = cost_center or (cell_texts[1] if len(cell_texts) > 1 else '')
                    created_at = created_at or (cell_texts[2] if len(cell_texts) > 2 else '')
                    
        except Exception as e:
            print(f"Error extracting row data: {e}")
            # If any error occurs, try to get text directly from cells as last resort
            try:
                cells = row_element.locator('td').all()
                cell_texts = [cell.inner_text().strip() for cell in cells[:3] if cell]
                if cell_texts:
                    name = cell_texts[0] if len(cell_texts) > 0 else ''
                    cost_center = cell_texts[1] if len(cell_texts) > 1 else ''
                    created_at = cell_texts[2] if len(cell_texts) > 2 else ''
            except Exception as e:
                print(f"Failed to extract row data with fallback: {e}")
        
        # Create a unique key by combining all fields
        unique_key = f"{name}||{cost_center}||{created_at}"
        
        return {
            'name': name,
            'cost_center': cost_center,
            'created_at': created_at,
            '_key': unique_key  # Add a unique key for comparison
        }
    
    def get_all_rows_data(self) -> List[Dict[str, str]]:
        """Get data from all rows in the table"""
        rows = self.get_rows()
        return [self.get_row_data(row) for row in rows]
    
    def is_row_visible(self, text: str) -> bool:
        """Check if a row with the given text is visible"""
        return self.get_row_by_text(text).is_visible()
    
    def get_row_count(self) -> int:
        """Get the total number of rows across all pages"""
        try:
            # First try to get the count from pagination text
            pagination_text = self.page.locator('div.bg-gray-50.px-6.py-4.border-t.border-gray-200')
            if pagination_text.is_visible():
                text = pagination_text.inner_text()
                if 'of' in text:
                    # Extract the total count from text like "Showing 1-10 of 35 expense types"
                    count_text = text.split('of')[-1].split()[0]
                    return int(count_text)
            
            # If pagination text not found or parsing failed, count visible rows
            return len(self.get_rows())
        except Exception as e:
            print(f"Error getting row count: {e}")
            # Fallback to counting visible rows
            return len(self.get_rows())
    
    def wait_for_row_with_text(self, text: str, timeout: float = 10000):
        """Wait for a row containing the specified text to appear"""
        row = self.get_row_by_text(text)
        expect(row).to_be_visible(timeout=timeout)
        return row
