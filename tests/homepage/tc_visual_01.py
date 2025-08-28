import os
import sys
import traceback
import time
from datetime import datetime
import pytest
from PIL import Image, ImageChops, ImageDraw, ImageFile
import io
import shutil
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError

# Add markers for this test module
pytestmark = [
    pytest.mark.playwright,
    pytest.mark.visual
]

# Allow loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Directory constants
BASELINE_DIR = "test_results/screenshots/baseline"
ACTUAL_DIR = "test_results/screenshots/actual"
DIFF_DIR = "test_results/screenshots/diff"

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

def debug_filesystem_info(path):
    """Capture detailed filesystem information for debugging"""
    info = []
    
    # Get absolute path
    abs_path = os.path.abspath(path)
    info.append(f"Path: {path}")
    info.append(f"Absolute path: {abs_path}")
    
    # Check if path exists
    exists = os.path.exists(abs_path)
    info.append(f"Exists: {exists}")
    
    if exists:
        # Get file stats
        try:
            stat_info = os.stat(abs_path)
            info.append(f"Size: {stat_info.st_size} bytes")
            info.append(f"Permissions: {oct(stat_info.st_mode)}")
            info.append(f"Owner: {stat_info.st_uid}")
            info.append(f"Group: {stat_info.st_gid}")
            info.append(f"Last modified: {stat_info.st_mtime}")
        except Exception as e:
            info.append(f"Error getting stats: {e}")
    
    # Check parent directory
    parent_dir = os.path.dirname(abs_path)
    info.append(f"\nParent directory: {parent_dir}")
    info.append(f"Parent exists: {os.path.exists(parent_dir)}")
    
    if os.path.exists(parent_dir):
        try:
            contents = os.listdir(parent_dir)
            info.append(f"Contents of {parent_dir}:")
            for item in contents:
                item_path = os.path.join(parent_dir, item)
                try:
                    item_stat = os.stat(item_path)
                    info.append(f"  {item} (size: {item_stat.st_size} bytes, mode: {oct(item_stat.st_mode)})")
                except Exception as e:
                    info.append(f"  {item} (error: {e})")
        except Exception as e:
            info.append(f"Error listing directory: {e}")
    
    return "\n".join(info)

@pytest.mark.skip(reason="Need further investigation")
def test_visual_regression(home_page: Page, request):
    """
    Compare current page appearance with baseline.

    This test will:
    1. Wait for the page to be fully loaded
    2. Hide dynamic content that might cause false positives
    3. Take a screenshot and compare with baseline
    4. Allow for minor visual differences
    """
    # Get test name for file naming
    test_name = request.node.name
    
    debug_file = "test_debug.log"
    with open(debug_file, "w") as f:
        f.write(f"=== Starting Visual Regression Test for {test_name} ===\n\n")
    
    def log_debug(message):
        with open(debug_file, "a") as f:
            f.write(f"{message}\n")
    
    log_debug("Test started")
    log_debug(f"Current working directory: {os.getcwd()}")
    log_debug(f"Python executable: {sys.executable}")
    log_debug(f"System path: {sys.path}")
    log_debug("\nEnvironment variables:")
    for key, value in os.environ.items():
        if key.startswith('PYTHON') or key.startswith('VIRTUAL_ENV') or 'PLAYWRIGHT' in key:
            log_debug(f"{key}={value}")
    
    print(f"\n=== Starting Visual Regression Test for {test_name} ===")

    try:
        # Set consistent viewport size
        home_page.set_viewport_size({"width": 1280, "height": 1024})
        
        # Wait for page to be fully loaded
        home_page.wait_for_load_state("networkidle")
        home_page.wait_for_load_state("domcontentloaded")
        time.sleep(2)  # Additional wait for any animations
        
        # Hide and modify dynamic content that might cause false positives
        home_page.evaluate("""
        (() => {
            // Remove or hide elements that frequently change
            const removeSelectors = [
                '[class*="cookie" i]',
                '[class*="banner" i]',
                '[class*="toast" i]',
                '[class*="notification" i]',
                '[class*="modal" i]',
                '[class*="popup" i]',
                '[class*="tooltip" i]',
                '[class*="tour" i]',
                '[class*="tutorial" i]',
                '[class*="announcement" i]',
                '[class*="ad" i]:not([class*="add" i])',
                'iframe',
                'video',
                'canvas',
                'svg',
                'img',
                '.MuiCircularProgress-root',
                '.MuiLinearProgress-root'
            ];
            
            // Hide elements that should be consistent
            const hideSelectors = [
                '[class*="loading" i]',
                '[class*="spinner" i]',
                '[class*="skeleton" i]',
                '[class*="progress" i]',
                '[class*="shimmer" i]',
                '[class*="pulse" i]',
                '[class*="animate" i]',
                '[class*="transition" i]',
                '[class*="fade" i]',
                '[class*="slide" i]',
                '[class*="carousel" i]',
                '[class*="slider" i]',
                '[class*="marquee" i]',
                '[class*="ticker" i]',
                '[class*="notification" i]',
                '[class*="alert" i]',
                '[class*="message" i]',
                '[class*="snackbar" i]',
                '[class*="toast" i]',
                '[class*="banner" i]',
                '[class*="cookie" i]',
                '[class*="modal" i]',
                '[class*="popup" i]',
                '[class*="tooltip" i]',
                '[class*="tour" i]',
                '[class*="tutorial" i]',
                '[class*="announcement" i]',
                '[class*="ad" i]:not([class*="add" i])',
                'iframe',
                'video',
                'canvas',
                'svg',
                'img',
                '.MuiCircularProgress-root',
                '.MuiLinearProgress-root'
            ];
            
            // Function to safely remove elements
            const removeElements = (selector) => {
                try {
                    document.querySelectorAll(selector).forEach(el => el.remove());
                } catch (e) {
                    console.warn(`Failed to remove elements with selector: ${selector}`, e);
                }
            };
            
            // Function to safely hide elements
            const hideElements = (selector) => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el && el.style) {
                            el.style.visibility = 'hidden';
                            el.style.opacity = '0';
                            el.style.transition = 'none';
                            el.style.animation = 'none';
                        }
                    });
                } catch (e) {
                    console.warn(`Failed to hide elements with selector: ${selector}`, e);
                }
            };
            
            // Remove problematic elements
            removeSelectors.forEach(removeElements);
    
            // Hide dynamic elements
            hideSelectors.forEach(hideElements);
            
            // Add common UI framework classes to hide
            const commonUISelectors = [
                // Material-UI
                '.MuiCircularProgress-root',
                '.MuiLinearProgress-root',
                '.MuiSkeleton-root',
                // Ant Design
                '.ant-spin',
                '.ant-progress',
                // Common loading indicators
                '[class*="loading" i]',
                '[class*="spinner" i]',
                '[class*="skeleton" i]',
                // Hide scrollbars
                '::-webkit-scrollbar',
                '::-webkit-scrollbar-thumb',
                '::-webkit-scrollbar-track'
            ];
                
            commonUISelectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        if (el && el.style) {
                            el.style.display = 'none';
                        }
                    });
                } catch (e) {
                    console.warn(`Failed to hide ${selector}:`, e);
                }
            });
            
            // Set consistent styles
            document.body.style.animation = 'none';
            document.body.style.transition = 'none';
            document.body.style.cursor = 'default';
            
            // Disable animations and transitions
            const style = document.createElement('style');
            style.textContent = `
                *, *::before, *::after {
                    animation: none !important;
                    transition: none !important;
                    animation-duration: 0.01ms !important;
                    animation-iteration-count: 1 !important;
                    transition-duration: 0.01ms !important;
                    scroll-behavior: auto !important;
                }
                
                /* Hide scrollbars */
                ::-webkit-scrollbar {
                    display: none !important;
                }
                
                /* Hide any remaining iframes */
                iframe {
                    display: none !important;
                }
            `;
            document.head.appendChild(style);
            
            // Scroll to top
            window.scrollTo(0, 0);
            
            // Force a reflow to ensure all styles are applied
            document.body.offsetHeight;
        })();
        """)
        
        # Wait for any remaining animations and dynamic content to stabilize
        home_page.wait_for_timeout(3000)  # Increased wait time
        
        # Force scroll to top and wait for any scroll-related animations
        home_page.evaluate("window.scrollTo(0, 0)")
        home_page.wait_for_timeout(500)
        
        # Take a screenshot with consistent options
        screenshot_path = os.path.join(ACTUAL_DIR, f"{test_name}.png")
        home_page.screenshot(path=screenshot_path, full_page=True)
        
        # Wait a moment for the screenshot to be saved
        time.sleep(1)
        
        # Create directories if they don't exist
        os.makedirs(BASELINE_DIR, exist_ok=True)
        os.makedirs(ACTUAL_DIR, exist_ok=True)
        os.makedirs(DIFF_DIR, exist_ok=True)

        # Check if baseline exists
        baseline_path = os.path.join(BASELINE_DIR, f"{test_name}.png")
        if not os.path.exists(baseline_path):
            # If no baseline exists, create one
            os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
            shutil.copy2(screenshot_path, baseline_path)
            pytest.skip(f"Created baseline image at {baseline_path}")

        # Compare images
        img1 = Image.open(baseline_path)
        img2 = Image.open(screenshot_path)

        if not images_are_similar(img1, img2):
            # Create diff image
            diff_path = os.path.join(DIFF_DIR, f"{test_name}_diff.png")
            highlight_differences(img1, img2, diff_path)

            # Save the actual image with timestamp for debugging
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_path = os.path.join(DIFF_DIR, f"{test_name}_actual_{timestamp}.png")
            shutil.copy2(screenshot_path, debug_path)

            # Fail the test with helpful message
            pytest.fail(f"Visual regression detected. See {diff_path} for differences.")
        
        # If we get here, the test passed
        print("Visual regression test passed!")
        
    except Exception as e:
        print("\n=== Test Failed ===")
        print(f"Error: {str(e)}")
        print("\nStack trace:")
        traceback.print_exc()
        
        # Save page source for debugging
        try:
            page_source_path = os.path.join(DIFF_DIR, f"{test_name}_page_source_{timestamp}.html")
            with open(page_source_path, 'w', encoding='utf-8') as f:
                f.write(home_page.content())
            print(f"\nPage source saved to: {page_source_path}")
        except Exception as e:
            print(f"Failed to save page source: {str(e)}")
        
        # Re-raise the exception to fail the test
        raise
