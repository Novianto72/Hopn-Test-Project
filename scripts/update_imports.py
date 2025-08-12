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
        return True
    return False

def main():
    test_dir = 'tests/cost_centers/test_cases'
    updated_files = []
    
    for root, _, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if update_imports_in_file(file_path):
                    updated_files.append(file_path)
    
    if updated_files:
        print("Updated imports in the following files:")
        for file in updated_files:
            print(f"- {file}")
    else:
        print("No files needed updating.")

if __name__ == "__main__":
    main()
