import json
from playwright.sync_api import expect

def test_page_performance(home_page):
    """Test page load performance metrics"""
    # Enable performance metrics
    metrics = home_page.evaluate("""() => {
        const [pageNav] = performance.getEntriesByType('navigation');
        return {
            loadTime: pageNav.loadEventEnd - pageNav.startTime,
            domContentLoaded: pageNav.domContentLoadedEventEnd - pageNav.startTime,
            firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
            largestContentfulPaint: performance.getEntriesByName('largest-contentful-paint')[0]?.startTime || 0,
            cumulativeLayoutShift: performance.getEntriesByName('layout-shift').reduce((sum, entry) => sum + entry.value, 0)
        };
    }""")
    
    # Log metrics
    print("Performance Metrics:", json.dumps(metrics, indent=2))
    
    # Assert performance thresholds (adjust these based on your requirements)
    assert metrics['loadTime'] < 5000, f"Page load time {metrics['loadTime']}ms exceeds 5s threshold"
    assert metrics['largestContentfulPaint'] < 2500, f"LCP {metrics['largestContentfulPaint']}ms exceeds 2.5s threshold"
    assert metrics['cumulativeLayoutShift'] < 0.1, f"Cumulative Layout Shift {metrics['cumulativeLayoutShift']} is too high"
    
    # Check for large images that could be optimized
    resources = home_page.evaluate("""() => 
        performance.getEntriesByType('resource')
            .filter(r => r.initiatorType === 'img')
            .map(r => ({
                url: r.name,
                size: r.encodedBodySize,
                duration: r.duration
            }))
    """)
    
    # Log large resources
    large_resources = [r for r in resources if r['size'] > 500000]  # 500KB
    if large_resources:
        print("Large resources found:", json.dumps(large_resources, indent=2))
    
    # Check for 4xx/5xx resources
    failed_requests = home_page.evaluate("""() => 
        performance.getEntriesByType('resource')
            .filter(r => r.responseStatus >= 400)
            .map(r => ({
                url: r.name,
                status: r.responseStatus
            }))
    """)
    
    assert len(failed_requests) == 0, f"Failed to load resources: {failed_requests}"
