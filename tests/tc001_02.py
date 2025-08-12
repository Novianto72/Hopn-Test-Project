from playwright.sync_api import sync_playwright

# Define anchor links and their matching section IDs
anchor_targets = [
    {"link_text": "Pricing", "target_id": "#pricing"},
    {"link_text": "Features", "target_id": "#features"},
    {"link_text": "How it Works", "target_id": "#how-it-works"},
    {"link_text": "FAQ", "target_id": "#faq"},
    {"link_text": "Home", "target_id": "#home"}
]


def run_anchor_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set headless=True for silent run
        page = browser.new_page()
        page.goto("https://wizeinvoice.com/en", timeout=60000)

        for target in anchor_targets:
            print(f"\n🔎 Testing link: {target['link_text']}")

            try:
                # Click the link
                page.click(f'a[href="{target["target_id"]}"]')
                page.wait_for_timeout(1000)

                # Locate the target section
                section = page.locator(f'section{target["target_id"]}')

                # Optional: force scroll to ensure bounding_box gets a value
                section.scroll_into_view_if_needed()
                page.wait_for_timeout(500)

                # Get position info
                box = section.bounding_box()

                # if section.is_visible():
                #     print(f"✅ Section {target['target_id']} is visible after clicking.")
                # else:
                #     print(f"❌ Section {target['target_id']} is NOT visible after clicking.")

                if box:
                    if box["y"] < 200:
                        print(f"✅ Section {target['target_id']} is in view (Y={box['y']:.2f})")
                    else:
                        print(f"❌ Section {target['target_id']} is not properly scrolled into view (Y={box['y']:.2f})")
                else:
                    print(f"⚠️ Section {target['target_id']} could not be located (bounding box not found)")

            except Exception as e:
                print(f"⚠️ Error while testing {target['link_text']}: {e}")

        browser.close()


if __name__ == "__main__":
    run_anchor_test()
