import os
import re

def update_imports_in_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Update the import statement
    new_content = re.sub(
        r'from\s+tests\.cost_centers\.pages\.cost_centers_page',
        'from pages.cost_centers.cost_centers_page',
        content
    )
    
    if new_content != content:
        with open(file_path, 'w') as file:
            file.write(new_content)
        print(f"Updated: {file_path}")
        return True
    return False

def main():
    test_dir = 'tests/cost_centers/test_cases'
    
    for file in os.listdir(test_dir):
        if file.startswith('test_') and file.endswith('.py'):
            file_path = os.path.join(test_dir, file)
            update_imports_in_file(file_path)

if __name__ == "__main__":
    main()
