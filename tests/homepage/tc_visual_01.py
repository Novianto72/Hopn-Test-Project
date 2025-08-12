import os
import sys
import traceback
from datetime import datetime
from playwright.sync_api import expect, TimeoutError as PlaywrightTimeoutError
import pytest
from PIL import Image, ImageChops, ImageDraw, ImageFile
import io
import shutil
import time

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Directory to store baseline and test screenshots
SCREENSHOT_DIR = "test-results/screenshots"
BASELINE_DIR = os.path.join(SCREENSHOT_DIR, "baseline")
ACTUAL_DIR = os.path.join(SCREENSHOT_DIR, "actual")
DIFF_DIR = os.path.join(SCREENSHOT_DIR, "diff")

# Create directories if they don't exist
for directory in [BASELINE_DIR, ACTUAL_DIR, DIFF_DIR]:
    os.makedirs(directory, exist_ok=True)

def images_are_similar(img1, img2, threshold=0.99):
    """Compare two images and return True if they're similar above the threshold"""
    if img1.size != img2.size or img1.mode != img2.mode:
        return False
    
    # Calculate difference
    diff = ImageChops.difference(img1, img2)
    
    # Convert to grayscale and calculate histogram
    hist = diff.convert('L').histogram()
    
    # Calculate similarity (percentage of identical pixels)
    identical_pixels = hist[0]  # First bin contains identical pixels
    total_pixels = img1.size[0] * img1.size[1]
    similarity = identical_pixels / total_pixels
    
    return similarity >= threshold

def highlight_differences(img1, img2, output_path):
    """Create a visual diff image highlighting the differences"""
    diff = ImageChops.difference(img1, img2)
    diff = diff.convert('L')
    
    # Create a mask of the differences
    threshold = 30
    mask = diff.point(lambda x: 255 if x > threshold else 0)
    
    # Create a red overlay for differences
    overlay = Image.new('RGBA', img1.size, (255, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw red rectangles around differences
    bbox = mask.getbbox()
    if bbox:
        draw.rectangle(bbox, outline='red', width=2)
    
    # Combine original with overlay
    result = img1.convert('RGBA')
    result.alpha_composite(overlay)
    result.save(output_path, 'PNG')

def test_visual_regression(home_page, request):
    """Compare current page appearance with baseline"""
    print("\n=== Starting Visual Regression Test ===")
    
    try:
        # Set viewport size
        home_page.set_viewport_size({"width": 1280, "height": 720})
        
        # Wait for page DOM content to be loaded
        home_page.wait_for_load_state('domcontentloaded')
        # Additional wait for dynamic content and animations
        home_page.wait_for_timeout(2000)  # Using wait_for_timeout instead of time.sleep
        
        # Scroll to ensure all lazy-loaded content is loaded
        print("Scrolling page to load all content...")
        home_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
        
        # Take screenshot
        print("Capturing screenshot...")
        test_name = request.node.name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        actual_path = os.path.join(ACTUAL_DIR, f"{test_name}_{timestamp}.png")
        home_page.screenshot(path=actual_path)
        
        # Get baseline path
        baseline_path = os.path.join(BASELINE_DIR, f"{test_name}.png")
        
        # Compare with baseline
        if not os.path.exists(baseline_path):
            # If no baseline exists, save current as baseline
            home_page.screenshot(path=baseline_path)
            print(f"Created new baseline: {baseline_path}")
            return

        # Load images for comparison
        with Image.open(baseline_path) as baseline_img:
            # Take a new screenshot for comparison
            current_img = home_page.screenshot()
            current_img = Image.open(io.BytesIO(current_img))
            
            # Compare images
            if not images_are_similar(baseline_img, current_img):
                # Create diff image
                diff_path = os.path.join(DIFF_DIR, f"{test_name}_{timestamp}.png")
                highlight_differences(baseline_img, current_img, diff_path)
            if diff_percentage < 1.0:  # Less than 1% difference
                print(f"WARNING: {error_msg}")
                return
                
            assert False, error_msg
        
        print("Visual test passed successfully!")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nStack trace:")
        traceback.print_exc()
        
        # Save page source for debugging
        try:
            page_source_path = os.path.join(DIFF_DIR, f"{test_name}_page_source_{timestamp}.html")
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(authenticated_page.content())
            print(f"\nPage source saved to: {page_source_path}")
        except Exception as e:
            print(f"Failed to save page source: {str(e)}")
        
        # Re-raise the exception to fail the test
        raise
